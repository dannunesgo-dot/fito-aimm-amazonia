# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_29_benchmarks_fontes_normalizacao")
MANIFEST = Path("data/manual/aimm_benchmark_sources_manifest_seed.csv")

FILES = {
    "template": BASE / "TEMPLATE_FONTES_BENCHMARK_AIMM_4_29.csv",
    "inventario": BASE / "INVENTARIO_ARQUIVOS_BENCHMARK_REPOSITORIO_AIMM_4_29.csv",
    "validacao": BASE / "VALIDACAO_FONTES_BENCHMARK_AIMM_4_29.csv",
    "normalizacao": BASE / "MATRIZ_NORMALIZACAO_BENCHMARK_AIMM_4_29.csv",
    "extracao": BASE / "PLANO_EXTRACAO_BENCHMARK_AIMM_4_29.csv",
    "readiness": BASE / "READINESS_BENCHMARK_AIMM_4_29.csv",
    "lacunas": BASE / "LACUNAS_BLOQUEIOS_BENCHMARK_AIMM_4_29.csv",
    "registry": Path("data/processed/aimm/aimm_benchmark_registry_4_29.csv"),
    "status": Path("data/processed/aimm/aimm_benchmark_status_4_29.csv"),
    "evidence": Path("data/evidence/evidence_aimm_benchmark_normalization_4_29.csv"),
    "report": Path("outputs/reports/RELATORIO_BENCHMARK_FONTES_NORMALIZACAO_AIMM_4_29.md"),
    "log": Path("outputs/logs/teste_aimm_benchmark_normalizacao_4_29.txt"),
}


ALLOWED_DIMENSIONS = {
    "gap",
    "intensidade",
    "mercado",
    "risco",
    "monitoramento",
}

ALLOWED_SOURCE_TYPES = {
    "oficial",
    "cientifica",
    "tecnica",
    "administrativa",
    "gis",
    "orcamentaria",
    "proxy",
    "interna_bloqueada",
    "outro_controlado",
}

ALLOWED_EXTRACTION_METHODS = {
    "manual",
    "csv",
    "xlsx",
    "json",
    "yaml",
    "pdf_manual",
    "api_futura",
    "web_futura",
    "qgis",
    "proxy",
    "nao_aplicavel",
}

ALLOWED_STATUS = {
    "publico_acessivel",
    "proxy_temporario",
    "bloqueado_ifc_interno",
    "pendente_revisao",
    "nao_encontrado",
    "nao_aplicavel",
}

ALLOWED_DIRECTIONS = {
    "maior_melhor",
    "menor_melhor",
    "faixa_ideal",
    "binario",
    "qualitativo",
    "nao_aplicavel",
}


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        rows = [{"status": "sem_linhas"}]

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized_rows.append({key: row.get(key, "") for key in fieldnames})

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(normalized_rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        file.seek(0)
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(file, delimiter=delimiter)
        return [dict(row) for row in reader]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def parse_float(value: str, default: float = 0.0) -> float:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def build_template() -> list[dict[str, str]]:
    return [
        {
            "id_benchmark": "BMK_001",
            "nome_benchmark": "lacuna de benchmark por dimensão AIMM",
            "dimensao_aimm": "gap",
            "fonte": "registro interno de lacunas controladas",
            "url_ou_referencia": "nao_aplicavel",
            "tipo_fonte": "administrativa",
            "metodo_extracao": "manual",
            "unidade_original": "contagem",
            "regra_normalizacao": "normalizar para escala 0_1 por proporcao de lacunas abertas",
            "direcao_melhor": "menor_melhor",
            "peso_preliminar": "0.20",
            "status_uso": "pendente_revisao",
            "usa_no_score_final": "nao",
            "observacao": "benchmark estrutural; nao libera score final",
        },
        {
            "id_benchmark": "BMK_002",
            "nome_benchmark": "intensidade de evidencias por componente",
            "dimensao_aimm": "intensidade",
            "fonte": "data/evidence e outputs/reports",
            "url_ou_referencia": "nao_aplicavel",
            "tipo_fonte": "tecnica",
            "metodo_extracao": "manual",
            "unidade_original": "contagem",
            "regra_normalizacao": "normalizar por componente avaliado",
            "direcao_melhor": "maior_melhor",
            "peso_preliminar": "0.20",
            "status_uso": "pendente_revisao",
            "usa_no_score_final": "nao",
            "observacao": "depende de auditoria das evidencias",
        },
        {
            "id_benchmark": "BMK_003",
            "nome_benchmark": "mercado e demanda potencial",
            "dimensao_aimm": "mercado",
            "fonte": "fontes publicas futuras e bases de comercio",
            "url_ou_referencia": "pendente",
            "tipo_fonte": "proxy",
            "metodo_extracao": "web_futura",
            "unidade_original": "indice",
            "regra_normalizacao": "normalizar por percentil ou faixa definida",
            "direcao_melhor": "maior_melhor",
            "peso_preliminar": "0.20",
            "status_uso": "proxy_temporario",
            "usa_no_score_final": "nao",
            "observacao": "coleta automatica ainda nao implementada",
        },
        {
            "id_benchmark": "BMK_004",
            "nome_benchmark": "risco regulatorio e operacional",
            "dimensao_aimm": "risco",
            "fonte": "matriz de riscos AIMM",
            "url_ou_referencia": "nao_aplicavel",
            "tipo_fonte": "administrativa",
            "metodo_extracao": "manual",
            "unidade_original": "indice",
            "regra_normalizacao": "maior risco reduz readiness",
            "direcao_melhor": "menor_melhor",
            "peso_preliminar": "0.20",
            "status_uso": "pendente_revisao",
            "usa_no_score_final": "nao",
            "observacao": "exige validação humana",
        },
        {
            "id_benchmark": "BMK_005",
            "nome_benchmark": "monitoramento e verificabilidade",
            "dimensao_aimm": "monitoramento",
            "fonte": "logs, registros e artefatos versionados",
            "url_ou_referencia": "nao_aplicavel",
            "tipo_fonte": "tecnica",
            "metodo_extracao": "csv",
            "unidade_original": "indice",
            "regra_normalizacao": "proporcao de itens com evidencia e log",
            "direcao_melhor": "maior_melhor",
            "peso_preliminar": "0.20",
            "status_uso": "pendente_revisao",
            "usa_no_score_final": "nao",
            "observacao": "estrutura inicial ja existente",
        },
    ]


def inventory_benchmark_files() -> list[dict[str, str]]:
    ignored_parts = {".git", "__pycache__", ".pytest_cache"}
    rows: list[dict[str, str]] = []

    for path in sorted(Path(".").rglob("*")):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue

        path_text = str(path).replace("\\", "/").lstrip("./")
        name_lower = path.name.lower()
        path_lower = path_text.lower()

        if "benchmark" not in name_lower and "benchmark" not in path_lower and "proxy" not in name_lower:
            continue

        rows.append(
            {
                "caminho": path_text,
                "nome_arquivo": path.name,
                "extensao": path.suffix.lower(),
                "tamanho_bytes": str(file_size(path)),
                "sha256": sha256_file(path),
                "possivel_funcao": classify_benchmark_file(path_text),
            }
        )

    return rows


def classify_benchmark_file(path_text: str) -> str:
    lower = path_text.lower()

    if "registry" in lower:
        return "registro"
    if "gap" in lower:
        return "lacunas"
    if "readiness" in lower:
        return "readiness"
    if "source" in lower or "fonte" in lower:
        return "fontes"
    if "proxy" in lower:
        return "proxy"
    if "evidence" in lower:
        return "evidencia"
    return "benchmark_indeterminado"


def validate_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], int, int]:
    validation: list[dict[str, str]] = []
    normalization: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []

    errors = 0
    warnings = 0

    for idx, row in enumerate(rows, start=1):
        benchmark_id = row.get("id_benchmark", f"BMK_LINHA_{idx}").strip() or f"BMK_LINHA_{idx}"
        nome = row.get("nome_benchmark", "").strip()
        dimensao = row.get("dimensao_aimm", "").strip().lower()
        fonte = row.get("fonte", "").strip()
        tipo_fonte = row.get("tipo_fonte", "").strip().lower()
        metodo = row.get("metodo_extracao", "").strip().lower()
        regra = row.get("regra_normalizacao", "").strip()
        direcao = row.get("direcao_melhor", "").strip().lower()
        status_uso = row.get("status_uso", "").strip().lower()
        usa_score = row.get("usa_no_score_final", "").strip().lower()
        peso = parse_float(row.get("peso_preliminar", "0"), 0.0)

        issues: list[str] = []
        row_status = "ok"

        if not nome:
            issues.append("nome_benchmark_vazio")
            row_status = "erro"
            errors += 1

        if dimensao not in ALLOWED_DIMENSIONS:
            issues.append("dimensao_aimm_invalida")
            row_status = "erro"
            errors += 1

        if not fonte:
            issues.append("fonte_vazia")
            row_status = "erro"
            errors += 1

        if tipo_fonte not in ALLOWED_SOURCE_TYPES:
            issues.append("tipo_fonte_invalido")
            row_status = "erro"
            errors += 1

        if metodo not in ALLOWED_EXTRACTION_METHODS:
            issues.append("metodo_extracao_invalido")
            row_status = "erro"
            errors += 1

        if not regra:
            issues.append("regra_normalizacao_vazia")
            row_status = "erro"
            errors += 1

        if direcao not in ALLOWED_DIRECTIONS:
            issues.append("direcao_melhor_invalida")
            row_status = "erro"
            errors += 1

        if status_uso not in ALLOWED_STATUS:
            issues.append("status_uso_invalido")
            row_status = "erro"
            errors += 1

        if usa_score == "sim":
            issues.append("uso_em_score_final_bloqueado_nesta_fase")
            row_status = "erro"
            errors += 1

        if peso < 0 or peso > 1:
            issues.append("peso_preliminar_fora_0_1")
            row_status = "erro"
            errors += 1

        if status_uso in {"proxy_temporario", "pendente_revisao", "bloqueado_ifc_interno", "nao_encontrado"}:
            issue = f"benchmark_nao_pronto:{status_uso}"
            issues.append(issue)
            if row_status == "ok":
                row_status = "alerta"
            warnings += 1

            gaps.append(
                {
                    "id_benchmark": benchmark_id,
                    "dimensao_aimm": dimensao,
                    "lacuna_ou_bloqueio": issue,
                    "acao_corretiva": corrective_action(status_uso),
                    "bloqueia_score_final": "sim",
                }
            )

        validation.append(
            {
                "id_benchmark": benchmark_id,
                "nome_benchmark": nome,
                "dimensao_aimm": dimensao,
                "tipo_fonte": tipo_fonte,
                "metodo_extracao": metodo,
                "status_uso": status_uso,
                "usa_no_score_final": usa_score,
                "peso_preliminar": f"{peso:.4f}",
                "status_validacao": row_status,
                "issues": "|".join(issues) if issues else "sem_issue",
            }
        )

        normalization.append(
            {
                "id_benchmark": benchmark_id,
                "dimensao_aimm": dimensao,
                "unidade_original": row.get("unidade_original", "").strip(),
                "regra_normalizacao": regra,
                "direcao_melhor": direcao,
                "escala_saida": "0_1",
                "pode_alimentar_score_final": "nao",
                "motivo_bloqueio_score": "score_final_bloqueado_ate_validacao_metodologica_e_fontes",
            }
        )

    return validation, normalization, gaps, errors, warnings


def corrective_action(status_uso: str) -> str:
    if status_uso == "proxy_temporario":
        return "substituir_proxy_por_fonte_publica_ou_validar_metodologia_proxy"
    if status_uso == "pendente_revisao":
        return "revisar_fonte_metodo_regra_normalizacao_e_documentar_evidencia"
    if status_uso == "bloqueado_ifc_interno":
        return "manter_bloqueado_ou_substituir_por_fonte_publica_equivalente"
    if status_uso == "nao_encontrado":
        return "localizar_fonte_ou_remover_benchmark_do_fluxo"
    return "sem_acao"


def extraction_plan(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []

    for row in rows:
        benchmark_id = row.get("id_benchmark", "").strip()
        metodo = row.get("metodo_extracao", "").strip().lower()
        fonte = row.get("fonte", "").strip()

        if metodo in {"manual", "csv", "xlsx", "json", "yaml", "qgis"}:
            etapa = "extracao_controlada_local"
        elif metodo in {"api_futura", "web_futura"}:
            etapa = "extracao_futura_bloqueada"
        elif metodo == "proxy":
            etapa = "proxy_exige_justificativa"
        else:
            etapa = "nao_aplicavel"

        plan.append(
            {
                "id_benchmark": benchmark_id,
                "fonte": fonte,
                "metodo_extracao": metodo,
                "etapa_operacional": etapa,
                "arquivo_entrada_esperado": "definir_em_manifesto_de_benchmark" if etapa != "nao_aplicavel" else "nao_aplicavel",
                "validacao_minima": "fonte_metodo_unidade_regra_normalizacao_status",
                "saida_esperada": "valor_normalizado_0_1_com_evidencia",
                "status_execucao_4_29": "planejado_nao_executado",
            }
        )

    return plan


def readiness_rows(validation: list[dict[str, str]], errors: int, warnings: int) -> list[dict[str, str]]:
    total = len(validation)
    ok = sum(1 for row in validation if row.get("status_validacao") == "ok")
    alertas = sum(1 for row in validation if row.get("status_validacao") == "alerta")
    erro = sum(1 for row in validation if row.get("status_validacao") == "erro")

    readiness = 0.0
    if total:
        readiness = ok / total

    return [
        {
            "total_benchmarks": str(total),
            "benchmarks_ok": str(ok),
            "benchmarks_com_alerta": str(alertas),
            "benchmarks_com_erro": str(erro),
            "erros_estruturais": str(errors),
            "alertas": str(warnings),
            "readiness_benchmark_preliminar": f"{readiness:.4f}",
            "score_aimm_final_liberado": "nao",
            "motivo": "benchmarks_ainda_exigem_fontes_validadas_extracao_real_e_revisao_metodologica",
        }
    ]


def main() -> None:
    template_rows = build_template()
    write_csv(FILES["template"], template_rows)

    if MANIFEST.exists():
        benchmark_rows = read_csv(MANIFEST)
        manifest_mode = "manifesto_manual_detectado"
    else:
        benchmark_rows = template_rows
        manifest_mode = "template_usado_por_manifesto_manual_ausente"

    inventory = inventory_benchmark_files()
    validation, normalization, gaps, errors, warnings = validate_rows(benchmark_rows)
    extraction = extraction_plan(benchmark_rows)
    readiness = readiness_rows(validation, errors, warnings)

    if not gaps:
        gaps = [
            {
                "id_benchmark": "SEM_LACUNA",
                "dimensao_aimm": "nao_aplicavel",
                "lacuna_ou_bloqueio": "sem_lacuna_detectada",
                "acao_corretiva": "manter_revisao",
                "bloqueia_score_final": "sim_por_trava_metodologica_geral",
            }
        ]

    registry = [
        {
            "rodada": "4.29",
            "pacote": "modulo_benchmarks_fontes_extracao_normalizacao",
            "manifesto_origem": str(MANIFEST),
            "modo_manifesto": manifest_mode,
            "benchmarks_registrados": str(len(benchmark_rows)),
            "arquivos_benchmark_inventariados": str(len(inventory)),
            "itens_validados": str(len(validation)),
            "lacunas_bloqueios": str(len(gaps)),
            "alertas": str(warnings),
            "erros_estruturais": str(errors),
            "score_aimm_final": "nao_liberado",
            "status": "gerado" if errors == 0 else "gerado_com_erros",
        }
    ]

    status = [
        {
            "rodada": "4.29",
            "status": "sucesso" if errors == 0 else "erro",
            "erros_estruturais": str(errors),
            "alertas": str(warnings),
            "manifesto_manual_detectado": "sim" if MANIFEST.exists() else "nao",
            "modulo_benchmark_funcional": "sim",
            "extracao_real_executada": "nao",
            "normalizacao_real_executada": "nao",
            "api_externa_ativa": "nao",
            "score_aimm_final": "nao_liberado",
            "proxima_rodada": "4.30",
            "proxima_rodada_descricao": "estrategia segura de API GitHub-Drive e teste seco de autenticacao",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_BENCHMARK_NORMALIZATION_4_29",
            "tipo_evidencia": "modulo_benchmark_fontes_normalizacao",
            "descricao": "Modulo operacional inicial para registro, validacao e normalizacao metodologica de benchmarks AIMM.",
            "status": "gerado",
            "limitacao": "Nao executa coleta externa, nao extrai valores reais e nao libera score final.",
        }
    ]

    report = [
        "# Relatório da Rodada 4.29 — benchmarks, fontes, extração e normalização",
        "",
        "## Resultado",
        "",
        "A rodada criou o módulo operacional inicial para controle de benchmarks AIMM.",
        "",
        "## O que funciona",
        "",
        "- Template de fontes e benchmarks.",
        "- Leitura de manifesto manual quando existir.",
        "- Inventário de arquivos com benchmark/proxy no repositório.",
        "- Validação de dimensão AIMM, fonte, método, status e regra de normalização.",
        "- Plano de extração por benchmark.",
        "- Matriz de normalização para escala 0_1.",
        "- Registro de lacunas e bloqueios.",
        "",
        "## O que ainda não faz",
        "",
        "- Não acessa internet.",
        "- Não acessa Drive.",
        "- Não executa coleta automática.",
        "- Não extrai valores reais dos benchmarks.",
        "- Não calcula score AIMM final.",
        "",
        "## Status",
        "",
        f"- Modo do manifesto: `{manifest_mode}`",
        f"- Benchmarks registrados: `{len(benchmark_rows)}`",
        f"- Arquivos benchmark/proxy inventariados: `{len(inventory)}`",
        f"- Alertas: `{warnings}`",
        f"- Erros estruturais: `{errors}`",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.30 — estratégia segura de API GitHub-Drive e teste seco de autenticação.",
    ]

    log = [
        "TESTE AIMM_BENCHMARK_NORMALIZATION_4_29 — Fito+ Amazônia",
        "=" * 86,
        f"Modo do manifesto: {manifest_mode}",
        f"Arquivo manifesto esperado: {MANIFEST}",
        f"Benchmarks registrados: {len(benchmark_rows)}",
        f"Arquivos benchmark/proxy inventariados: {len(inventory)}",
        f"Itens validados: {len(validation)}",
        f"Lacunas/bloqueios registrados: {len(gaps)}",
        f"Alertas: {warnings}",
        f"Erros estruturais: {errors}",
        "Extracao real executada: nao",
        "Normalizacao real executada: nao",
        "API externa ativa: nao",
        "Score AIMM final liberado: nao",
        "",
        "Resultado: SUCESSO." if errors == 0 else "Resultado: ERRO.",
        "Modulo de benchmarks, fontes, extracao e normalizacao gerado.",
        "",
        "Trava: nao acessa web, nao acessa Drive, nao extrai valores reais e nao libera score AIMM final.",
    ]

    write_csv(FILES["inventario"], inventory)
    write_csv(FILES["validacao"], validation)
    write_csv(FILES["normalizacao"], normalization)
    write_csv(FILES["extracao"], extraction)
    write_csv(FILES["readiness"], readiness)
    write_csv(FILES["lacunas"], gaps)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["status"], status)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log))

    if errors:
        raise ValueError(f"Rodada 4.29 contém {errors} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
