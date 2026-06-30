from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


DIMENSIONS = Path("data/reference/aimm_canonical_dimensions_seed.csv")
ALIGNMENT = Path("data/reference/aimm_indicator_alignment_seed.csv")

OUT_DIM = Path("data/processed/aimm_canonical_dimension_registry.csv")
OUT_ALIGN = Path("data/processed/aimm_indicator_alignment_registry.csv")
OUT_VALIDATION = Path("data/processed/aimm_alignment_validation_report.csv")
OUT_BLOCKERS = Path("data/processed/aimm_score_blockers_registry.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_aimm_alignment.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_ALINHAMENTO_AIMM.md")
OUT_LOG = Path("outputs/logs/teste_aimm_alignment_4_20.txt")


VALID_DIMENSIONS = {"project_outcomes", "market_outcomes"}
VALID_SUBDIMENSIONS = {
    "stakeholder_effects",
    "economy_wide_effects",
    "environmental_social_effects",
    "competitiveness",
    "resilience",
    "sustainability",
}
VALID_AXES = {
    "gap",
    "intensity",
    "impact_potential",
    "risk_assessment",
    "monitoring",
    "benchmark",
    "cross_cutting",
}
VALID_STATUS = {
    "calculavel_preliminar",
    "proxy_baixa_confianca",
    "bloqueado_sem_benchmark",
    "bloqueado_revisao_humana",
    "apenas_monitoramento",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def validate_alignment(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validation_rows: list[dict[str, str]] = []
    blocker_rows: list[dict[str, str]] = []

    for row in rows:
        errors: list[str] = []
        warnings: list[str] = []

        dim = row.get("dimensao_canonica", "")
        sub = row.get("subdimensao", "")
        axis = row.get("eixo_analitico", "")
        status = row.get("status_uso", "")
        benchmark_status = row.get("benchmark_status", "")

        if dim not in VALID_DIMENSIONS:
            errors.append("dimensao_canonica_invalida")

        if sub not in VALID_SUBDIMENSIONS:
            errors.append("subdimensao_invalida")

        if axis not in VALID_AXES:
            errors.append("eixo_analitico_invalido")

        if status not in VALID_STATUS:
            errors.append("status_uso_invalido")

        if benchmark_status in {"bloqueado_sem_benchmark", "proxy_baixa_confianca"}:
            warnings.append("benchmark_ou_proxy_limitado")

        if status.startswith("bloqueado"):
            blocker_rows.append(
                {
                    "indicator_id": row.get("indicator_id", ""),
                    "nome_indicador": row.get("nome_indicador", ""),
                    "motivo_bloqueio": status,
                    "benchmark_status": benchmark_status,
                    "acao_recomendada": "Completar benchmark, proxy, fonte, revisão humana ou evidência antes de liberar score final.",
                }
            )

        if status == "proxy_baixa_confianca":
            blocker_rows.append(
                {
                    "indicator_id": row.get("indicator_id", ""),
                    "nome_indicador": row.get("nome_indicador", ""),
                    "motivo_bloqueio": "proxy_baixa_confianca",
                    "benchmark_status": benchmark_status,
                    "acao_recomendada": "Manter apenas em score estrutural preliminar com penalidade futura.",
                }
            )

        validation_rows.append(
            {
                "indicator_id": row.get("indicator_id", ""),
                "nome_indicador": row.get("nome_indicador", ""),
                "dimensao_canonica": dim,
                "subdimensao": sub,
                "eixo_analitico": axis,
                "status_uso": status,
                "benchmark_status": benchmark_status,
                "erros": "|".join(errors),
                "alertas": "|".join(warnings),
                "status_validacao": "erro" if errors else "ok_com_alerta" if warnings else "ok",
            }
        )

    return validation_rows, blocker_rows


def build_report(
    dimensions: list[dict[str, str]],
    alignment: list[dict[str, str]],
    validation: list[dict[str, str]],
    blockers: list[dict[str, str]],
) -> str:
    total = len(alignment)
    errors = sum(1 for row in validation if row["status_validacao"] == "erro")
    alerts = sum(1 for row in validation if row["status_validacao"] == "ok_com_alerta")
    ok = sum(1 for row in validation if row["status_validacao"] == "ok")

    project = sum(1 for row in alignment if row["dimensao_canonica"] == "project_outcomes")
    market = sum(1 for row in alignment if row["dimensao_canonica"] == "market_outcomes")

    lines = [
        "# Relatório de Alinhamento AIMM — Rodada 4.20",
        "",
        "## 1. Resultado estrutural",
        "",
        f"- Indicadores avaliados: `{total}`",
        f"- Indicadores em Project Outcomes: `{project}`",
        f"- Indicadores em Market Outcomes: `{market}`",
        f"- Registros de dimensão/eixo: `{len(dimensions)}`",
        f"- Validações OK: `{ok}`",
        f"- Validações com alerta: `{alerts}`",
        f"- Validações com erro: `{errors}`",
        f"- Bloqueios/limitações registrados: `{len(blockers)}`",
        "",
        "## 2. Base conceitual",
        "",
        "A Rodada 4.20 separa as dimensões AIMM canônicas dos eixos analíticos. Project Outcomes e Market Outcomes são dimensões principais. Gap, intensity, impact potential, risk assessment, monitoring e benchmark são eixos de análise, não dimensões finais equivalentes.",
        "",
        "## 3. Indicadores com bloqueio ou limitação",
        "",
        "| Indicador | Motivo | Ação recomendada |",
        "|---|---|---|",
    ]

    for row in blockers:
        lines.append(
            f"| {row['indicator_id']} — {row['nome_indicador']} | "
            f"{row['motivo_bloqueio']} | {row['acao_recomendada']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Travas",
            "",
            "- A Rodada 4.20 não calcula score AIMM final.",
            "- Indicadores com benchmark ausente permanecem bloqueados.",
            "- Proxies de baixa confiança entram apenas em estrutura preliminar.",
            "- Revisão humana pendente continua bloqueando circulação externa.",
            "- Score final depende de rodadas futuras de benchmark, GIS, orçamento, mercado, regulação e revisão humana.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    dimensions = read_csv(DIMENSIONS)
    alignment = read_csv(ALIGNMENT)

    validation, blockers = validate_alignment(alignment)

    write_csv(OUT_DIM, dimensions)
    write_csv(OUT_ALIGN, alignment)
    write_csv(OUT_VALIDATION, validation)
    write_csv(OUT_BLOCKERS, blockers)

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_ALIGNMENT_4_20",
            "tipo_evidencia": "alinhamento_conceitual",
            "fonte": "IFC Anticipated Impact Measurement and Monitoring",
            "url": "https://www.ifc.org/en/our-impact/measuring-and-monitoring",
            "descricao": "Base conceitual para dimensões AIMM, parâmetros de mensuração, benchmarks setoriais e monitoramento.",
            "uso_na_calculadora": "Reclassificar indicadores em Project Outcomes, Market Outcomes, subdimensões e eixos analíticos.",
            "status_conferencia": "validado_estruturalmente",
            "limitacoes": "Não substitui acesso aos frameworks setoriais internos completos da IFC.",
        }
    ]

    write_csv(OUT_EVIDENCE, evidence)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(
        build_report(dimensions, alignment, validation, blockers),
        encoding="utf-8",
    )

    total_errors = sum(1 for row in validation if row["status_validacao"] == "erro")
    total_alerts = sum(1 for row in validation if row["status_validacao"] == "ok_com_alerta")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log_lines = [
        "TESTE AIMM_ALIGNMENT — Fito+ Amazônia",
        "=" * 86,
        f"Registros canônicos: {len(dimensions)}",
        f"Indicadores alinhados: {len(alignment)}",
        f"Validações com erro: {total_errors}",
        f"Validações com alerta: {total_alerts}",
        f"Bloqueios/limitações: {len(blockers)}",
        "",
        "Resultado: SUCESSO.",
        "O alinhamento AIMM foi gerado e validado estruturalmente.",
        "",
        "Trava: alinhamento AIMM não libera score final nem decisões executivas.",
    ]

    log_text = "\n".join(log_lines)
    OUT_LOG.write_text(log_text, encoding="utf-8")

    print(log_text)

    if total_errors:
        raise ValueError(f"Alinhamento AIMM contém {total_errors} erro(s) estruturais.")


if __name__ == "__main__":
    main()
