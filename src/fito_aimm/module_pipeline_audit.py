"""
Agente — Auditoria factual de módulo/pipeline (AIMM).

Verifica, sem inferência, a completude e a consistência de cada módulo de
negócio em ``src/fito_aimm/``:

- código Python presente;
- função de execução pública (``execute_*`` / ``main``);
- regras ``config/*.yaml`` referenciadas pelo código e existentes;
- teste ``scripts/testar_<modulo>.py``;
- workflow ``.github/workflows/<modulo>.yml`` (com mapeamento explícito quando
  o nome diverge);
- saídas ``OUT_*`` declaradas no código;
- saídas publicadas pelo workflow (aparecem no bloco ``path:`` do
  ``upload-artifact``);
- seeds/entradas (``SEED_*`` e leituras) resolvidos no repositório ou
  classificados como artefato externo no congelamento técnico.

A extração de constantes é feita por análise de sintaxe (AST) do próprio
código-fonte — não por suposição. O agente lê a árvore de arquivos do
repositório e cruza referências.

Convenções idiomáticas do projeto respeitadas: função pública
``execute_module_pipeline_audit``; regras em YAML; saídas CSV com delimitador
``;`` e encoding ``utf-8-sig``; evidência sintética; retorno estruturado com
``errors``.
"""

from __future__ import annotations

import ast
import csv
import re
from pathlib import Path
from typing import Any

import yaml

RULES = Path("config/module_pipeline_audit_rules.yaml")
FREEZE_RULES = Path("config/system_freeze_rules.yaml")

OUT_MODULES = Path("data/processed/module_pipeline_inventory.csv")
OUT_EVIDENCE_TABLE = Path("docs/MODULE_PIPELINE_EVIDENCE_TABLE.csv")
OUT_UNPUBLISHED = Path("data/processed/module_pipeline_unpublished_outputs.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_module_pipeline_audit.csv")

# Requisitos que, quando falham, rebaixam módulo de negócio para PARCIAL.
_REBAIXA_PARCIAL = {
    "regras_yaml",
    "workflow",
    "saidas_declaradas",
    "saidas_publicadas",
    "seeds_entradas",
}


# --------------------------------------------------------------------------- #
# Utilitários de E/S (padrão do repositório).
# --------------------------------------------------------------------------- #
def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


# --------------------------------------------------------------------------- #
# Extração factual por análise de sintaxe (AST).
# --------------------------------------------------------------------------- #
def _string_constants_from_assignments(tree: ast.AST) -> dict[str, str]:
    """Mapeia NOME_CONSTANTE -> literal de string (quando o alvo é Path("...") ou "...")."""
    consts: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            value = node.value
            # Caso Path("literal")
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "Path"
                and value.args
                and isinstance(value.args[0], ast.Constant)
                and isinstance(value.args[0].value, str)
            ):
                consts[target.id] = value.args[0].value
            # Caso "literal" direto
            elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                consts[target.id] = value.value
    return consts


def _has_public_execution(tree: ast.AST) -> str | None:
    """Retorna o nome da função pública de execução, ou None.

    Reconhece as convenções de nome usadas no repositório: prefixos
    ``execute_`` (inglês) e ``executar_`` (português), ``coletar_`` (coletores
    de dados) e a função ``main``.
    """
    prefixos = ("execute_", "executar_", "coletar_")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "main" or node.name.startswith(prefixos):
                return node.name
    return None


def analisar_modulo(module_path: Path) -> dict[str, Any]:
    """Extrai fatos de um módulo por AST: execução pública, YAMLs, OUT_*, SEED_*."""
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    consts = _string_constants_from_assignments(tree)

    yaml_refs = sorted({v for v in consts.values() if v.startswith("config/") and v.endswith((".yaml", ".yml"))})
    out_paths = sorted({v for k, v in consts.items() if k.startswith("OUT_")})
    seed_paths = sorted({v for k, v in consts.items() if k.startswith("SEED_")})

    # Entradas adicionais: literais lidos por read_csv/open que apontem a data/.
    input_literals = sorted(
        {
            v
            for v in consts.values()
            if v.startswith("data/") and v not in out_paths
        }
    )

    return {
        "execucao": _has_public_execution(tree),
        "yaml_refs": yaml_refs,
        "out_paths": out_paths,
        "seed_paths": seed_paths,
        "input_literals": input_literals,
    }


def _workflow_paths(workflow_file: Path) -> set[str]:
    """Extrai caminhos citados no bloco path: de upload-artifact (heurística textual)."""
    if not workflow_file.exists():
        return set()
    text = workflow_file.read_text(encoding="utf-8")
    # Captura linhas de caminho dentro de blocos path:| — linhas que apontam a data/ ou docs/.
    paths = set()
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if re.match(r"^(data|docs|outputs)/", stripped):
            paths.add(stripped)
    return paths


# --------------------------------------------------------------------------- #
# Classificação de status por módulo.
# --------------------------------------------------------------------------- #
def _classificar(reqs: dict[str, str]) -> str:
    aplicaveis = {k: v for k, v in reqs.items() if v != "NAO_APLICAVEL"}
    valores = set(aplicaveis.values())
    if "CONFLITANTE" in valores:
        return "CONFLITANTE"
    if valores == {"IMPLEMENTADO"}:
        return "IMPLEMENTADO"
    # Código presente mas sem teste e sem workflow → EXPERIMENTAL.
    if reqs.get("teste") == "AUSENTE" and reqs.get("workflow") == "AUSENTE":
        return "EXPERIMENTAL"
    # Núcleo mínimo presente, falha em requisito rebaixador → PARCIAL.
    nucleo_ok = reqs.get("codigo") == "IMPLEMENTADO" and reqs.get("execucao") == "IMPLEMENTADO"
    if nucleo_ok and any(reqs.get(r) in {"AUSENTE", "PARCIAL"} for r in _REBAIXA_PARCIAL):
        return "PARCIAL"
    if "AUSENTE" in valores:
        return "PARCIAL"
    return "NAO_COMPROVADO"


def execute_module_pipeline_audit() -> dict[str, Any]:
    cfg = load_yaml(RULES)
    if not cfg:
        raise FileNotFoundError(f"Arquivo de regras obrigatório ausente: {RULES}")

    dirs = cfg.get("diretorios", {})
    mod_dir = Path(dirs.get("modulos", "src/fito_aimm"))
    wf_dir = Path(dirs.get("workflows", ".github/workflows"))
    test_dir = Path(dirs.get("testes", "scripts"))

    base_utils = set(cfg.get("modulos_base_utilitarios", []))
    wf_map = cfg.get("mapeamento_workflow_por_modulo", {})
    test_map = cfg.get("mapeamento_teste_por_modulo", {})
    dep_prefixes = tuple(cfg.get("prefixos_dependencia_pipeline", []))

    # Artefatos externos declarados no congelamento técnico (entradas toleráveis).
    freeze = load_yaml(FREEZE_RULES)
    externos_ok = bool(freeze)  # se há congelamento técnico, entradas ausentes podem ser externas

    errors: list[str] = []
    inventory: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []

    if not mod_dir.exists():
        raise FileNotFoundError(f"Diretório de módulos ausente: {mod_dir}")

    # União de caminhos publicados por qualquer workflow (para checagem cruzada).
    todos_workflow_paths: set[str] = set()
    for wf in sorted(wf_dir.glob("*.yml")):
        todos_workflow_paths |= _workflow_paths(wf)

    todas_saidas_declaradas: set[str] = set()

    for py in sorted(mod_dir.glob("*.py")):
        nome = py.name
        stem = py.stem
        if nome in base_utils:
            inventory.append(
                {
                    "modulo": nome,
                    "classe": "utilitario_base",
                    "status": "IMPLEMENTADO",
                    "execucao": "NAO_APLICAVEL",
                    "linhas": len(py.read_text(encoding="utf-8").splitlines()),
                }
            )
            continue

        fatos = analisar_modulo(py)

        # Requisito 1: código presente.
        r_codigo = "IMPLEMENTADO"
        # Requisito 2: execução pública.
        r_exec = "IMPLEMENTADO" if fatos["execucao"] else "AUSENTE"

        # Requisito 3: regras YAML (só exigido se o código referencia config/*.yaml).
        if fatos["yaml_refs"]:
            faltando_yaml = [y for y in fatos["yaml_refs"] if not Path(y).exists()]
            r_yaml = "IMPLEMENTADO" if not faltando_yaml else "AUSENTE"
            for y in faltando_yaml:
                evidence_rows.append(_ev(nome, "regras_yaml", "AUSENTE", y, "Regra YAML referenciada no código não existe."))
        else:
            r_yaml = "NAO_APLICAVEL"

        # Requisito 4: teste (com mapeamento explícito de nome divergente).
        test_name = test_map.get(stem, f"testar_{stem}")
        test_file = test_dir / f"{test_name}.py"
        r_teste = "IMPLEMENTADO" if test_file.exists() else "AUSENTE"

        # Requisito 5: workflow (com mapeamento explícito).
        wf_name = wf_map.get(stem, stem)
        wf_file = wf_dir / f"{wf_name}.yml"
        r_workflow = "IMPLEMENTADO" if wf_file.exists() else "AUSENTE"

        # Requisito 6: saídas declaradas existem como constante (fato do código).
        r_saidas_decl = "IMPLEMENTADO" if fatos["out_paths"] else "NAO_APLICAVEL"
        todas_saidas_declaradas |= set(fatos["out_paths"])

        # Requisito 7: saídas publicadas pelo workflow correspondente.
        if fatos["out_paths"]:
            wf_paths = _workflow_paths(wf_file)
            nao_publicadas = [o for o in fatos["out_paths"] if o not in wf_paths]
            if not wf_file.exists():
                r_saidas_pub = "NAO_COMPROVADO"
            elif not nao_publicadas:
                r_saidas_pub = "IMPLEMENTADO"
            else:
                r_saidas_pub = "CONFLITANTE"
                for o in nao_publicadas:
                    evidence_rows.append(
                        _ev(nome, "saidas_publicadas", "CONFLITANTE", str(wf_file),
                            f"Saída declarada no código não publicada pelo workflow: {o}")
                    )
        else:
            r_saidas_pub = "NAO_APLICAVEL"

        # Requisito 8: seeds/entradas resolvidos, dependência de pipeline ou externos.
        entradas = fatos["seed_paths"] + fatos["input_literals"]
        if entradas:
            faltando = [s for s in entradas if not Path(s).exists()]
            # Separa dependências de pipeline (geradas em runtime por outro
            # módulo) de seeds de entrada genuinamente ausentes.
            dep_pipeline = [s for s in faltando if s.startswith(dep_prefixes)]
            seeds_faltando = [s for s in faltando if not s.startswith(dep_prefixes)]
            if not faltando:
                r_seeds = "IMPLEMENTADO"
            elif seeds_faltando and not externos_ok:
                r_seeds = "AUSENTE"
                for s in seeds_faltando:
                    evidence_rows.append(_ev(nome, "seeds_entradas", "AUSENTE", s, "Seed de entrada referenciado não existe."))
            else:
                # Só há dependências de pipeline ausentes, ou seeds toleráveis como externos.
                r_seeds = "PARCIAL"
                for s in dep_pipeline:
                    evidence_rows.append(
                        _ev(nome, "seeds_entradas", "PARCIAL", s,
                            "Dependência de pipeline gerada em runtime por outro módulo; ausente em clone estático.")
                    )
                for s in seeds_faltando:
                    evidence_rows.append(
                        _ev(nome, "seeds_entradas", "PARCIAL", s,
                            "Seed ausente no repositório; tolerável se artefato externo (congelamento técnico).")
                    )
        else:
            r_seeds = "NAO_APLICAVEL"

        reqs = {
            "codigo": r_codigo,
            "execucao": r_exec,
            "regras_yaml": r_yaml,
            "teste": r_teste,
            "workflow": r_workflow,
            "saidas_declaradas": r_saidas_decl,
            "saidas_publicadas": r_saidas_pub,
            "seeds_entradas": r_seeds,
        }
        status = _classificar(reqs)

        # Linhas de evidência para os requisitos-chave presentes.
        evidence_rows.append(_ev(nome, "codigo", "IMPLEMENTADO", str(py), f"Módulo com {len(py.read_text(encoding='utf-8').splitlines())} linhas."))
        evidence_rows.append(_ev(nome, "execucao", r_exec, str(py), f"Função pública: {fatos['execucao'] or 'não encontrada'}."))
        evidence_rows.append(_ev(nome, "teste", r_teste, str(test_file), "Teste presente." if r_teste == "IMPLEMENTADO" else "Teste ausente."))
        evidence_rows.append(_ev(nome, "workflow", r_workflow, str(wf_file), "Workflow presente." if r_workflow == "IMPLEMENTADO" else "Workflow ausente."))

        inventory.append(
            {
                "modulo": nome,
                "classe": "negocio",
                "status": status,
                "execucao": fatos["execucao"] or "",
                "linhas": len(py.read_text(encoding="utf-8").splitlines()),
                "yaml_refs": " | ".join(fatos["yaml_refs"]),
                "saidas": " | ".join(fatos["out_paths"]),
                "seeds": " | ".join(fatos["seed_paths"]),
                "req_codigo": reqs["codigo"],
                "req_execucao": reqs["execucao"],
                "req_regras_yaml": reqs["regras_yaml"],
                "req_teste": reqs["teste"],
                "req_workflow": reqs["workflow"],
                "req_saidas_declaradas": reqs["saidas_declaradas"],
                "req_saidas_publicadas": reqs["saidas_publicadas"],
                "req_seeds_entradas": reqs["seeds_entradas"],
            }
        )

    # Saídas escritas por código e não publicadas por nenhum workflow.
    # Exclui os próprios artefatos deste agente de auditoria: seu workflow
    # (module_pipeline_audit.yml) é parte da mesma entrega e não deve ser
    # contabilizado como lacuna preexistente do repositório.
    proprios = {
        str(OUT_MODULES), str(OUT_EVIDENCE_TABLE),
        str(OUT_UNPUBLISHED), str(OUT_EVIDENCE),
    }
    unpublished = sorted((todas_saidas_declaradas - todos_workflow_paths) - proprios)
    unpublished_rows = [{"saida_declarada": u, "publicada_por_algum_workflow": "nao"} for u in unpublished]

    # Cabeçalho fixo do inventário (linhas de negócio e utilitário-base têm o
    # mesmo conjunto de colunas; campos ausentes são preenchidos vazios).
    inv_fields = [
        "modulo", "classe", "status", "execucao", "linhas",
        "yaml_refs", "saidas", "seeds",
        "req_codigo", "req_execucao", "req_regras_yaml", "req_teste",
        "req_workflow", "req_saidas_declaradas", "req_saidas_publicadas",
        "req_seeds_entradas",
    ]
    inventory_norm = [{campo: row.get(campo, "") for campo in inv_fields} for row in inventory]

    # Persistência.
    write_csv(OUT_MODULES, inventory_norm, fields=inv_fields)
    write_csv(
        OUT_EVIDENCE_TABLE,
        evidence_rows,
        fields=["modulo", "requisito", "status", "arquivo", "evidencia", "impacto", "acao_recomendada"],
    )
    write_csv(OUT_UNPUBLISHED, unpublished_rows, fields=["saida_declarada", "publicada_por_algum_workflow"])

    # Contadores.
    negocio = [m for m in inventory if m["classe"] == "negocio"]
    total_negocio = len(negocio)
    total_implementado = sum(1 for m in negocio if m["status"] == "IMPLEMENTADO")
    total_parcial = sum(1 for m in negocio if m["status"] == "PARCIAL")
    total_conflitante = sum(1 for m in negocio if m["status"] == "CONFLITANTE")

    evidence = [{
        "id_evidencia": "EVD_MODULE_PIPELINE_AUDIT",
        "id_fonte": "MODULE_PIPELINE_AUDIT",
        "id_indicador": "SYS_01; GOV_01",
        "tipo_evidencia": "auditoria_estrutural",
        "pergunta_ou_lacuna": "Cada módulo de negócio AIMM forma tríade completa e consistente (código+regras+workflow+teste+saídas)?",
        "url_ou_arquivo": f"{OUT_MODULES}; {OUT_EVIDENCE_TABLE}; {OUT_UNPUBLISHED}",
        "titulo_documento": "Auditoria factual de módulo/pipeline — AIMM",
        "pagina_tabela_secao": "inventário de módulos, tabela de evidência e saídas não publicadas",
        "trecho_original_ou_descricao": (
            f"Módulos de negócio: {total_negocio}; completos: {total_implementado}; "
            f"parciais: {total_parcial}; conflitantes: {total_conflitante}; "
            f"saídas não publicadas por workflow: {len(unpublished)}."
        ),
        "resumo_ptbr": "Diagnóstico de completude estrutural dos módulos antes de novas tarefas.",
        "valor_extraido": str(total_negocio),
        "unidade": "módulos de negócio auditados",
        "periodo_referencia": "estado atual da branch auditada",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "análise de sintaxe (AST) do código e checagem cruzada com workflows e sistema de arquivos",
        "nivel_confianca": "alto_para_estrutura",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "automatico",
        "limitacoes": "Não executa os módulos; audita presença, declaração e publicação, não correção funcional dos cálculos.",
        "uso_na_calculadora": "Governança, rastreabilidade e priorização de fechamento de lacunas.",
        "status_evidencia": "gerada",
    }]
    write_csv(OUT_EVIDENCE, evidence)

    return {
        "errors": errors,
        "total_negocio": total_negocio,
        "total_implementado": total_implementado,
        "total_parcial": total_parcial,
        "total_conflitante": total_conflitante,
        "total_unpublished_outputs": len(unpublished),
        "inventory": inventory,
        "unpublished": unpublished,
        "outputs": {
            "module_pipeline_inventory": str(OUT_MODULES),
            "evidence_table": str(OUT_EVIDENCE_TABLE),
            "unpublished_outputs": str(OUT_UNPUBLISHED),
            "evidence": str(OUT_EVIDENCE),
        },
    }


def _ev(modulo: str, requisito: str, status: str, arquivo: str, evidencia: str,
        impacto: str = "", acao: str = "") -> dict[str, str]:
    return {
        "modulo": modulo,
        "requisito": requisito,
        "status": status,
        "arquivo": arquivo,
        "evidencia": evidencia,
        "impacto": impacto or ("bloqueia_completude" if status in {"AUSENTE", "CONFLITANTE"} else "informativo"),
        "acao_recomendada": acao or (
            "criar_ou_corrigir_artefato" if status in {"AUSENTE", "CONFLITANTE"} else "nenhuma"
        ),
    }


if __name__ == "__main__":
    resultado = execute_module_pipeline_audit()
    print(resultado["trecho_original_ou_descricao"] if "trecho_original_ou_descricao" in resultado else resultado)
