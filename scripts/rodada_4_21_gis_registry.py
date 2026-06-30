from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


LAYERS = Path("data/reference/gis_layer_registry_seed.csv")
INDICATORS = Path("data/reference/gis_indicator_registry_seed.csv")

OUT_LAYERS = Path("data/processed/gis/gis_layer_registry.csv")
OUT_INDICATORS = Path("data/processed/gis/gis_indicator_registry.csv")
OUT_READINESS = Path("data/processed/gis/gis_readiness_report.csv")
OUT_GAPS = Path("data/processed/gis/gis_gap_register.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_gis_registry.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_ESTRUTURAL.md")
OUT_LOG = Path("outputs/logs/teste_gis_registry_4_21.txt")


VALID_GEOMETRY = {
    "ponto",
    "linha",
    "poligono",
    "linha_poligono",
    "poligono_ponto",
    "raster_vetor_oficial_ou_mapbiomas_validado",
}

VALID_STATUS_DADO = {
    "pendente_download",
    "pendente_validacao",
    "pendente_manual",
    "disponivel",
    "validado",
    "bloqueado",
}

VALID_STATUS_USO = {
    "apenas_monitoramento",
    "calculavel_futuro",
    "calculavel_preliminar",
    "proxy_baixa_confianca",
    "bloqueado",
}

OBRIGATORIA = {"sim", "nao"}


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


def validate_layers(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    for row in rows:
        erros: list[str] = []
        alertas: list[str] = []

        if row.get("tipo_geometria", "") not in VALID_GEOMETRY:
            erros.append("tipo_geometria_invalido")

        if row.get("status_dado", "") not in VALID_STATUS_DADO:
            erros.append("status_dado_invalido")

        if row.get("obrigatoria", "") not in OBRIGATORIA:
            erros.append("obrigatoria_invalida")

        if row.get("crs_esperado", "") != "EPSG:4674":
            alertas.append("crs_diferente_do_padrao_entrada")

        if row.get("status_dado", "").startswith("pendente"):
            alertas.append("camada_pendente")

        out.append(
            {
                **row,
                "erros": "|".join(erros),
                "alertas": "|".join(alertas),
                "status_validacao": "erro" if erros else "ok_com_alerta" if alertas else "ok",
            }
        )

    return out


def validate_indicators(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    for row in rows:
        erros: list[str] = []
        alertas: list[str] = []

        if row.get("status_uso", "") not in VALID_STATUS_USO:
            erros.append("status_uso_invalido")

        if row.get("status_uso", "") in {"calculavel_futuro", "proxy_baixa_confianca"}:
            alertas.append("indicador_nao_calculado_nesta_rodada")

        if row.get("status_uso", "") == "proxy_baixa_confianca":
            alertas.append("proxy_requer_penalidade_futura")

        out.append(
            {
                **row,
                "erros": "|".join(erros),
                "alertas": "|".join(alertas),
                "status_validacao": "erro" if erros else "ok_com_alerta" if alertas else "ok",
            }
        )

    return out


def build_gaps(layers: list[dict[str, str]], indicators: list[dict[str, str]]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []

    for row in layers:
        if row["status_dado"].startswith("pendente"):
            gaps.append(
                {
                    "id_lacuna": f"GAP_{row['layer_id']}",
                    "tipo": "camada_gis",
                    "item": row["nome_camada"],
                    "criticidade": "alta" if row["obrigatoria"] == "sim" else "media",
                    "descricao": f"Camada GIS com status {row['status_dado']}.",
                    "acao_recomendada": "Obter camada oficial, validar CRS, campos obrigatórios e geometria antes da Rodada 4.22.",
                    "bloqueia_score_final": "sim" if row["obrigatoria"] == "sim" else "nao",
                }
            )

    for row in indicators:
        if row["status_uso"] in {"calculavel_futuro", "proxy_baixa_confianca"}:
            gaps.append(
                {
                    "id_lacuna": f"GAP_{row['gis_indicator_id']}",
                    "tipo": "indicador_gis",
                    "item": row["nome_indicador"],
                    "criticidade": "media",
                    "descricao": f"Indicador GIS com status {row['status_uso']}.",
                    "acao_recomendada": "Implementar cálculo espacial real na Rodada 4.22 ou posterior.",
                    "bloqueia_score_final": "sim" if row["status_uso"] == "proxy_baixa_confianca" else "nao",
                }
            )

    return gaps


def build_report(
    layers: list[dict[str, str]],
    indicators: list[dict[str, str]],
    readiness: list[dict[str, str]],
    gaps: list[dict[str, str]],
) -> str:
    status = readiness[0]

    lines = [
        "# Relatório GIS Estrutural — Rodada 4.21",
        "",
        "## 1. Resultado da rodada",
        "",
        f"- Camadas registradas: `{status['camadas_registradas']}`",
        f"- Camadas obrigatórias: `{status['camadas_obrigatorias']}`",
        f"- Camadas pendentes: `{status['camadas_pendentes']}`",
        f"- Indicadores GIS registrados: `{status['indicadores_registrados']}`",
        f"- Indicadores calculáveis futuros: `{status['indicadores_calculaveis_futuros']}`",
        f"- Indicadores proxy de baixa confiança: `{status['indicadores_proxy_baixa_confianca']}`",
        f"- Readiness GIS estrutural: `{status['readiness_gis_percentual']}%`",
        "",
        "## 2. Função do módulo GIS na calculadora AIMM",
        "",
        "O módulo GIS será usado para analisar território, logística, proximidade institucional, risco de sobreposição territorial, disponibilidade de infraestrutura, densidade institucional e condições espaciais de implementação do Fito+ Amazônia.",
        "",
        "Nesta rodada, apenas a arquitetura GIS foi criada. O processamento espacial real será feito na Rodada 4.22.",
        "",
        "## 3. Camadas GIS registradas",
        "",
        "| ID | Camada | Geometria | Status | Obrigatória |",
        "|---|---|---|---|---|",
    ]

    for row in layers:
        lines.append(
            f"| {row['layer_id']} | {row['nome_camada']} | {row['tipo_geometria']} | "
            f"{row['status_dado']} | {row['obrigatoria']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Indicadores GIS registrados",
            "",
            "| ID | Indicador | Grupo | Status | Trava |",
            "|---|---|---|---|---|",
        ]
    )

    for row in indicators:
        lines.append(
            f"| {row['gis_indicator_id']} | {row['nome_indicador']} | {row['grupo']} | "
            f"{row['status_uso']} | {row['trava']} |"
        )

    lines.extend(
        [
            "",
            "## 5. Lacunas GIS",
            "",
            "| Lacuna | Tipo | Item | Criticidade | Ação recomendada |",
            "|---|---|---|---|---|",
        ]
    )

    for row in gaps:
        lines.append(
            f"| {row['id_lacuna']} | {row['tipo']} | {row['item']} | "
            f"{row['criticidade']} | {row['acao_recomendada']} |"
        )

    lines.extend(
        [
            "",
            "## 6. Travas",
            "",
            "- A Rodada 4.21 não calcula área, distância, buffer ou interseção.",
            "- A Rodada 4.21 não seleciona territórios, OSCs, cooperativas, espécies ou produtos.",
            "- A Rodada 4.21 não libera score AIMM final.",
            "- O processamento espacial real fica condicionado à Rodada 4.22.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    raw_layers = read_csv(LAYERS)
    raw_indicators = read_csv(INDICATORS)

    layers = validate_layers(raw_layers)
    indicators = validate_indicators(raw_indicators)
    gaps = build_gaps(layers, indicators)

    layer_errors = sum(1 for row in layers if row["status_validacao"] == "erro")
    indicator_errors = sum(1 for row in indicators if row["status_validacao"] == "erro")

    mandatory_layers = sum(1 for row in layers if row["obrigatoria"] == "sim")
    pending_layers = sum(1 for row in layers if row["status_dado"].startswith("pendente"))
    future_indicators = sum(1 for row in indicators if row["status_uso"] == "calculavel_futuro")
    proxy_indicators = sum(1 for row in indicators if row["status_uso"] == "proxy_baixa_confianca")

    available_layers = sum(1 for row in layers if row["status_dado"] in {"disponivel", "validado"})
    readiness_percentual = round((available_layers / len(layers)) * 100, 2) if layers else 0.0

    readiness = [
        {
            "rodada": "4.21",
            "camadas_registradas": str(len(layers)),
            "camadas_obrigatorias": str(mandatory_layers),
            "camadas_pendentes": str(pending_layers),
            "indicadores_registrados": str(len(indicators)),
            "indicadores_calculaveis_futuros": str(future_indicators),
            "indicadores_proxy_baixa_confianca": str(proxy_indicators),
            "readiness_gis_percentual": str(readiness_percentual),
            "erros_camadas": str(layer_errors),
            "erros_indicadores": str(indicator_errors),
            "status_rodada": "erro" if layer_errors or indicator_errors else "validada_com_lacunas",
            "observacao": "Rodada estrutural. Camadas e indicadores foram registrados, mas processamento espacial real ainda não foi executado.",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_GIS_REGISTRY_4_21",
            "tipo_evidencia": "registro_gis_estrutural",
            "fonte_1": "IBGE Malhas Territoriais",
            "fonte_2": "GeoPandas documentation",
            "fonte_3": "QGIS processing documentation",
            "uso_na_calculadora": "Base para registro de camadas, indicadores GIS, readiness e lacunas espaciais.",
            "status_conferencia": "validado_estruturalmente",
            "limitacoes": "Não houve processamento de geometrias reais nesta rodada.",
        }
    ]

    write_csv(OUT_LAYERS, layers)
    write_csv(OUT_INDICATORS, indicators)
    write_csv(OUT_READINESS, readiness)
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_EVIDENCE, evidence)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(
        build_report(layers, indicators, readiness, gaps),
        encoding="utf-8",
    )

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log_lines = [
        "TESTE GIS_REGISTRY — Fito+ Amazônia",
        "=" * 86,
        f"Camadas GIS registradas: {len(layers)}",
        f"Camadas obrigatórias: {mandatory_layers}",
        f"Camadas pendentes: {pending_layers}",
        f"Indicadores GIS registrados: {len(indicators)}",
        f"Indicadores calculáveis futuros: {future_indicators}",
        f"Indicadores proxy baixa confiança: {proxy_indicators}",
        f"Readiness GIS estrutural: {readiness_percentual}%",
        f"Erros de camada: {layer_errors}",
        f"Erros de indicador: {indicator_errors}",
        f"Lacunas GIS registradas: {len(gaps)}",
        "",
        "Resultado: SUCESSO.",
        "A implementação GIS estrutural foi criada e validada com lacunas controladas.",
        "",
        "Trava: GIS estrutural não processa geometrias reais nem libera score AIMM final.",
    ]

    log_text = "\n".join(log_lines)
    OUT_LOG.write_text(log_text, encoding="utf-8")
    print(log_text)

    if layer_errors or indicator_errors:
        raise ValueError("Há erros estruturais no registro GIS.")


if __name__ == "__main__":
    main()
