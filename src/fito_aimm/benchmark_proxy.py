
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/benchmark_proxy_rules.yaml")
BENCHMARKS = Path("data/reference/benchmark_registry_seed.csv")
METHODS = Path("data/reference/proxy_method_registry_seed.csv")
GAPS = Path("data/reference/benchmark_gap_report_seed.csv")
DIM_MAP = Path("data/reference/aimm_dimension_benchmark_map_seed.csv")
SOURCES = Path("data/reference/source_registry_benchmark_seed.csv")

OUT_BENCHMARKS = Path("data/processed/benchmark_registry.csv")
OUT_METHODS = Path("data/processed/proxy_method_registry.csv")
OUT_GAPS = Path("data/processed/benchmark_gap_report.csv")
OUT_DIM_MAP = Path("data/processed/aimm_dimension_benchmark_map.csv")
OUT_SOURCES = Path("data/processed/source_registry_benchmark.csv")
OUT_READINESS = Path("data/processed/benchmark_readiness_matrix.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_benchmark_proxy.csv")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def check_unique(rows: list[dict[str, str]], field: str, label: str) -> list[str]:
    seen = set()
    errors = []
    for i, row in enumerate(rows, start=2):
        key = row.get(field, "").strip()
        if not key:
            errors.append(f"{label}: linha {i} sem {field}")
        elif key in seen:
            errors.append(f"{label}: {field} duplicado: {key}")
        seen.add(key)
    return errors


def validate_inputs(benchmarks, methods, gaps, dim_map, sources, rules) -> list[str]:
    errors = []
    errors.extend(check_unique(benchmarks, "id_benchmark", "benchmark_registry"))
    errors.extend(check_unique(methods, "id_metodo_proxy", "proxy_method_registry"))
    errors.extend(check_unique(gaps, "id_lacuna_benchmark", "benchmark_gap_report"))
    errors.extend(check_unique(sources, "id_fonte", "source_registry_benchmark"))

    valid_classes = set(rules.get("classificacao_benchmark", []))
    valid_conf = set(rules.get("niveis_confianca", []))
    valid_dims = set(rules.get("dimensoes", []))
    method_ids = {r["id_metodo_proxy"] for r in methods}
    source_ids = {r["id_fonte"] for r in sources}

    for i, row in enumerate(benchmarks, start=2):
        if row.get("classificacao_benchmark") not in valid_classes:
            errors.append(f"benchmark_registry linha {i}: classificação inválida: {row.get('classificacao_benchmark')}")
        if row.get("nivel_confianca") not in valid_conf:
            errors.append(f"benchmark_registry linha {i}: nível de confiança inválido: {row.get('nivel_confianca')}")
        if row.get("dimensao_aimm") not in valid_dims:
            errors.append(f"benchmark_registry linha {i}: dimensão AIMM inválida: {row.get('dimensao_aimm')}")
        if row.get("id_metodo_proxy") not in method_ids:
            errors.append(f"benchmark_registry linha {i}: método proxy desconhecido: {row.get('id_metodo_proxy')}")
        for src in [s.strip() for s in row.get("fontes", "").split(";") if s.strip()]:
            if src not in source_ids:
                errors.append(f"benchmark_registry linha {i}: fonte desconhecida: {src}")
        if row.get("classificacao_benchmark") == "benchmark_ifc_nao_publico" and row.get("nivel_confianca") != "bloqueado":
            errors.append(f"benchmark_registry linha {i}: benchmark IFC não público deve ter nível bloqueado")

    dims_in_map = {r["dimensao_aimm"] for r in dim_map}
    if dims_in_map != valid_dims:
        missing = valid_dims - dims_in_map
        extra = dims_in_map - valid_dims
        if missing:
            errors.append(f"aimm_dimension_benchmark_map: dimensões ausentes: {sorted(missing)}")
        if extra:
            errors.append(f"aimm_dimension_benchmark_map: dimensões extras: {sorted(extra)}")

    return errors


def readiness_status(row: dict[str, str]) -> str:
    classification = row.get("classificacao_benchmark")
    confidence = row.get("nivel_confianca")
    if classification in {"benchmark_ifc_nao_publico", "lacuna_sem_benchmark"} or confidence == "bloqueado":
        return "bloqueado"
    if confidence == "baixo":
        return "proxy_baixa_confianca"
    if confidence == "medio":
        return "proxy_utilizavel_com_validacao"
    if confidence == "alto":
        return "benchmark_utilizavel"
    return "revisar"


def build_readiness(benchmarks: list[dict[str, str]], gaps: list[dict[str, str]]) -> list[dict[str, Any]]:
    gaps_by_indicator: dict[str, list[str]] = {}
    for g in gaps:
        gaps_by_indicator.setdefault(g.get("id_indicador", ""), []).append(g.get("id_lacuna_benchmark", ""))

    rows = []
    for b in benchmarks:
        status = readiness_status(b)
        rows.append({
            "id_benchmark": b.get("id_benchmark", ""),
            "id_indicador": b.get("id_indicador", ""),
            "dimensao_aimm": b.get("dimensao_aimm", ""),
            "classificacao_benchmark": b.get("classificacao_benchmark", ""),
            "nivel_confianca": b.get("nivel_confianca", ""),
            "status_prontidao": status,
            "pode_alimentar_score_final": "não" if status in {"bloqueado", "proxy_baixa_confianca"} else "somente_com_validacao",
            "lacunas_relacionadas": "|".join(gaps_by_indicator.get(b.get("id_indicador", ""), [])),
            "acao_requerida": (
                "não usar; manter como lacuna/bloqueio" if status == "bloqueado"
                else "validar fonte, unidade, período, território e fórmula antes do score"
            ),
            "limitacao": b.get("limitacao", ""),
        })
    return rows


def generate_evidence(benchmarks, methods, gaps, dim_map, sources, readiness):
    blocked = sum(1 for r in readiness if r["status_prontidao"] == "bloqueado")
    low = sum(1 for r in readiness if r["status_prontidao"] == "proxy_baixa_confianca")
    usable = len(readiness) - blocked - low
    return [{
        "id_evidencia": "EVD_BENCHMARK_PROXY_4_15",
        "id_fonte": "BENCHMARK_PROXY_REGISTRY",
        "id_indicador": "GAP; INTENSIDADE; MERCADO; RISCO; MONITORAMENTO",
        "tipo_evidencia": "registro_benchmarks_proxies_lacunas",
        "pergunta_ou_lacuna": "Quais benchmarks, proxies e lacunas podem alimentar a calculadora Fito+ Amazônia AIMM sem inventar dados internos não públicos?",
        "url_ou_arquivo": "data/processed/benchmark_registry.csv; data/processed/benchmark_gap_report.csv; data/processed/benchmark_readiness_matrix.csv",
        "titulo_documento": "Benchmarks, proxies e lacunas AIMM — Rodada 4.15",
        "pagina_tabela_secao": "benchmark_registry; proxy_method_registry; benchmark_gap_report; readiness_matrix",
        "trecho_original_ou_descricao": f"Benchmarks/proxies registrados: {len(benchmarks)}; métodos proxy: {len(methods)}; lacunas: {len(gaps)}; fontes: {len(sources)}; bloqueados: {blocked}; baixa confiança: {low}; utilizáveis apenas com validação: {usable}.",
        "resumo_ptbr": "Evidência de estruturação metodológica de benchmarks e proxies; não há score final.",
        "valor_extraido": str(len(benchmarks)),
        "unidade": "benchmarks/proxies",
        "periodo_referencia": "Rodada 4.15",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "classificação automatizada de benchmarks, proxies, lacunas e prontidão",
        "nivel_confianca": "médio_para_governança_metodológica; baixo_para_score_final",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_validacao_fontes_e_benchmarks",
        "limitacoes": "Benchmarks IFC internos não públicos ficam bloqueados; proxies exigem validação por fonte, unidade, período e território.",
        "uso_na_calculadora": "Define quais indicadores podem receber proxy, quais ficam bloqueados e quais exigem novas coletas.",
        "status_evidencia": "pendente",
    }]


def execute_benchmark_proxy() -> dict[str, Any]:
    rules = load_yaml(RULES)
    benchmarks = read_csv(BENCHMARKS)
    methods = read_csv(METHODS)
    gaps = read_csv(GAPS)
    dim_map = read_csv(DIM_MAP)
    sources = read_csv(SOURCES)

    errors = validate_inputs(benchmarks, methods, gaps, dim_map, sources, rules)
    if errors:
        return {"errors": errors}

    readiness = build_readiness(benchmarks, gaps)
    evidence = generate_evidence(benchmarks, methods, gaps, dim_map, sources, readiness)

    write_csv(OUT_BENCHMARKS, benchmarks)
    write_csv(OUT_METHODS, methods)
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_DIM_MAP, dim_map)
    write_csv(OUT_SOURCES, sources)
    write_csv(OUT_READINESS, readiness)
    write_csv(OUT_EVIDENCE, evidence)

    blocked = sum(1 for r in readiness if r["status_prontidao"] == "bloqueado")
    low = sum(1 for r in readiness if r["status_prontidao"] == "proxy_baixa_confianca")

    return {
        "errors": [],
        "total_benchmarks": len(benchmarks),
        "total_methods": len(methods),
        "total_gaps": len(gaps),
        "total_sources": len(sources),
        "total_dimensions": len(dim_map),
        "blocked": blocked,
        "low_confidence": low,
        "outputs": {
            "benchmark_registry": str(OUT_BENCHMARKS),
            "proxy_method_registry": str(OUT_METHODS),
            "benchmark_gap_report": str(OUT_GAPS),
            "aimm_dimension_benchmark_map": str(OUT_DIM_MAP),
            "source_registry_benchmark": str(OUT_SOURCES),
            "benchmark_readiness_matrix": str(OUT_READINESS),
            "evidence": str(OUT_EVIDENCE),
        }
    }
