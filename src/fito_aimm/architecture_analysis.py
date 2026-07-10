"""
Agente — Análise de arquitetura e condições técnicas (AIMM).

Automatiza a extração factual dos eixos objetiváveis por código:

- **Eixo Arquitetura:** grafo de dependência entre módulos (quem lê saída que
  outro escreve), pontos de entrada (funções públicas) e saída (``OUT_*``).
- **Eixo APIs:** URLs externas consumidas (com módulo consumidor) e endpoints
  Flask internos (rota, método, autenticação).
- **Eixo Condições técnicas:** stack de ``requirements.txt``, portas do gateway
  e backend, variáveis de ``.env.example``.

Os eixos Objetivo e Funcionalidades exigem leitura interpretativa e são tratados
no relatório ``docs/ARCHITECTURE_ANALYSIS_FACTUAL.md``, não neste módulo.

Extração por análise de sintaxe (AST) e leitura direta de arquivos — sem
inferência. Convenções idiomáticas do repositório respeitadas: função pública
``execute_architecture_analysis``; saídas CSV ``;`` / ``utf-8-sig``; retorno
estruturado com ``errors``.
"""

from __future__ import annotations

import ast
import csv
import re
from pathlib import Path
from typing import Any

MODULES_DIR = Path("src/fito_aimm")
APP_FILE = Path("app.py")
REQUIREMENTS = Path("requirements.txt")
ENV_EXAMPLE = Path(".env.example")
CADDYFILE = Path("Caddyfile")

OUT_API_TABLE = Path("docs/ARCHITECTURE_API_TABLE.csv")
OUT_DEPENDENCY = Path("data/processed/architecture_dependency_graph.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_architecture_analysis.csv")

# Prefixos que indicam função pública de execução (convenções do repositório).
_EXEC_PREFIXES = ("execute_", "executar_", "coletar_")

# Módulos-base utilitários (superfície mínima).
_BASE_UTILS = {
    "__init__.py", "buscador.py", "extrator.py",
    "normalizador.py", "conferidor.py", "sincroniza_drive.py",
}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def _string_constants(tree: ast.AST) -> dict[str, str]:
    consts: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            v = node.value
            if (
                isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
                and v.func.id == "Path" and v.args
                and isinstance(v.args[0], ast.Constant) and isinstance(v.args[0].value, str)
            ):
                consts[target.id] = v.args[0].value
            elif isinstance(v, ast.Constant) and isinstance(v.value, str):
                consts[target.id] = v.value
    return consts


def _public_exec(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "main" or node.name.startswith(_EXEC_PREFIXES):
                return node.name
    return None


def _urls_in(source: str) -> list[str]:
    # URLs http(s) que não sejam namespaces XML.
    urls = re.findall(r"https?://[a-zA-Z0-9./_%:-]+", source)
    return sorted({u for u in urls if "w3.org" not in u})


def _analisar_modulos() -> dict[str, dict[str, Any]]:
    dados: dict[str, dict[str, Any]] = {}
    for py in sorted(MODULES_DIR.glob("*.py")):
        if py.name in _BASE_UTILS:
            continue
        src = py.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(py))
        consts = _string_constants(tree)
        out_paths = sorted({v for k, v in consts.items() if k.startswith("OUT_")})
        # Entradas: SEED_* e literais data/ que não sejam saídas.
        entradas = sorted({
            v for k, v in consts.items()
            if (k.startswith("SEED_") or v.startswith("data/")) and v not in out_paths
        })
        dados[py.name] = {
            "arquivo": str(py),
            "exec": _public_exec(tree),
            "out_paths": out_paths,
            "entradas": entradas,
            "urls": _urls_in(src),
        }
    return dados


def _grafo_dependencia(dados: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """A depende de B se A lê uma saída OUT_* que B escreve."""
    escritores: dict[str, str] = {}
    for mod, d in dados.items():
        for out in d["out_paths"]:
            escritores[out] = mod
    arestas: list[dict[str, str]] = []
    for mod, d in dados.items():
        for entrada in d["entradas"]:
            produtor = escritores.get(entrada)
            if produtor and produtor != mod:
                arestas.append({
                    "modulo_consumidor": mod,
                    "depende_de": produtor,
                    "via_arquivo": entrada,
                })
    return arestas


def _endpoints_flask() -> list[dict[str, str]]:
    if not APP_FILE.exists():
        return []
    src = APP_FILE.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(APP_FILE))
    rotas: list[dict[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        rota = None
        metodos = "GET"
        autenticado = "nao"
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "route":
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    rota = dec.args[0].value
                for kw in dec.keywords:
                    if kw.arg == "methods" and isinstance(kw.value, ast.List):
                        metodos = ",".join(
                            e.value for e in kw.value.elts if isinstance(e, ast.Constant)
                        )
            elif isinstance(dec, ast.Name) and dec.id == "verify_bearer_token":
                autenticado = "sim"
        if rota is not None:
            rotas.append({
                "rota": rota,
                "metodo": metodos,
                "autenticacao_bearer": autenticado,
                "handler": node.name,
            })
    return rotas


def _condicoes_tecnicas() -> dict[str, Any]:
    stack = []
    if REQUIREMENTS.exists():
        stack = [l.strip() for l in REQUIREMENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    env_vars = []
    if ENV_EXAMPLE.exists():
        for l in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
            l = l.strip()
            if l and not l.startswith("#") and "=" in l:
                env_vars.append(l.split("=", 1)[0])
    portas = []
    if CADDYFILE.exists():
        portas = sorted(set(re.findall(r":(\d{2,5})", CADDYFILE.read_text(encoding="utf-8"))))
    return {"stack": stack, "env_vars": env_vars, "portas_caddy": portas}


def execute_architecture_analysis() -> dict[str, Any]:
    errors: list[str] = []
    if not MODULES_DIR.exists():
        raise FileNotFoundError(f"Diretório de módulos ausente: {MODULES_DIR}")

    dados = _analisar_modulos()
    arestas = _grafo_dependencia(dados)
    endpoints = _endpoints_flask()
    cond = _condicoes_tecnicas()

    # Tabela de APIs (externas + internas).
    api_rows: list[dict[str, str]] = []
    # Externas: uma linha por (módulo, url).
    for mod, d in dados.items():
        for url in d["urls"]:
            api_rows.append({
                "tipo": "api_externa",
                "nome": url.split("/")[2] if "/" in url else url,
                "origem_ou_rota": url,
                "modulo_consumidor": mod,
                "arquivo": d["arquivo"],
                "metodo_ou_formato": "HTTP GET (verificar formato no módulo)",
                "estado": "NAO_VERIFICADA",
                "observacao": "Estado da URL não verificado por este módulo; verificar em runtime com rede.",
            })
    # Internas: endpoints Flask.
    for ep in endpoints:
        api_rows.append({
            "tipo": "endpoint_interno",
            "nome": ep["handler"],
            "origem_ou_rota": ep["rota"],
            "modulo_consumidor": "app.py",
            "arquivo": str(APP_FILE),
            "metodo_ou_formato": ep["metodo"],
            "estado": "REQUER_AUTENTICACAO" if ep["autenticacao_bearer"] == "sim" else "ATIVA",
            "observacao": f"Bearer token: {ep['autenticacao_bearer']}",
        })

    write_csv(
        OUT_API_TABLE, api_rows,
        ["tipo", "nome", "origem_ou_rota", "modulo_consumidor", "arquivo",
         "metodo_ou_formato", "estado", "observacao"],
    )
    write_csv(
        OUT_DEPENDENCY, arestas,
        ["modulo_consumidor", "depende_de", "via_arquivo"],
    )

    total_apis_ext = sum(1 for r in api_rows if r["tipo"] == "api_externa")
    total_endpoints = sum(1 for r in api_rows if r["tipo"] == "endpoint_interno")

    evidence = [{
        "id_evidencia": "EVD_ARCHITECTURE_ANALYSIS",
        "id_fonte": "ARCHITECTURE_ANALYSIS",
        "id_indicador": "SYS_01; ARCH_01",
        "tipo_evidencia": "analise_arquitetura",
        "pergunta_ou_lacuna": "Qual a arquitetura, APIs e condições técnicas factuais do sistema AIMM?",
        "url_ou_arquivo": f"{OUT_API_TABLE}; {OUT_DEPENDENCY}",
        "titulo_documento": "Análise de arquitetura e condições técnicas — AIMM",
        "pagina_tabela_secao": "tabela de APIs, grafo de dependência e condições técnicas",
        "trecho_original_ou_descricao": (
            f"Módulos de negócio: {len(dados)}; APIs externas consumidas: {total_apis_ext}; "
            f"endpoints Flask internos: {total_endpoints}; arestas de dependência: {len(arestas)}; "
            f"dependências de stack: {len(cond['stack'])}; portas Caddy: {', '.join(cond['portas_caddy'])}."
        ),
        "resumo_ptbr": "Retrato técnico factual da arquitetura antes de decisões de evolução.",
        "valor_extraido": str(len(dados)),
        "unidade": "módulos de negócio analisados",
        "periodo_referencia": "estado atual da branch",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "análise de sintaxe (AST) e leitura direta de arquivos de configuração",
        "nivel_confianca": "alto_para_estrutura",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "automatico",
        "limitacoes": "Eixos Objetivo e Funcionalidades exigem leitura interpretativa (no relatório); estado de APIs externas requer verificação com rede.",
        "uso_na_calculadora": "Base para decisões de arquitetura, integração e evolução técnica.",
        "status_evidencia": "gerada",
    }]
    write_csv(
        OUT_EVIDENCE, evidence,
        list(evidence[0].keys()),
    )

    return {
        "errors": errors,
        "total_modulos": len(dados),
        "total_apis_externas": total_apis_ext,
        "total_endpoints": total_endpoints,
        "total_arestas": len(arestas),
        "stack": cond["stack"],
        "env_vars": cond["env_vars"],
        "portas_caddy": cond["portas_caddy"],
        "outputs": {
            "api_table": str(OUT_API_TABLE),
            "dependency_graph": str(OUT_DEPENDENCY),
            "evidence": str(OUT_EVIDENCE),
        },
    }


if __name__ == "__main__":
    r = execute_architecture_analysis()
    print(f"Módulos: {r['total_modulos']} | APIs externas: {r['total_apis_externas']} | "
          f"Endpoints: {r['total_endpoints']} | Arestas dependência: {r['total_arestas']}")
    print(f"Portas Caddy: {r['portas_caddy']} | Vars ambiente: {r['env_vars']}")
