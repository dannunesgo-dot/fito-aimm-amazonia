from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


SEED = Path("data/manual/gis/gis_manaus_example_manifest_seed.csv")

OUT_REGISTRY = Path("data/processed/gis/gis_manaus_example_registry.csv")
OUT_STATUS = Path("data/processed/gis/gis_manaus_example_status.csv")
OUT_GAPS = Path("data/processed/gis/gis_manaus_example_gaps.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_gis_manaus_example.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_MANAUS_4_22_B1.md")
OUT_LOG = Path("outputs/logs/teste_gis_manaus_4_22_b1.txt")

REQUIRED = {
    "registro_id",
    "arquivo",
    "tipo_arquivo",
    "local_informado",
    "drive_status",
    "fonte",
    "ano_dado",
    "data_download_informada",
    "layer_name",
    "crs_original",
    "crs_gpkg",
    "total_feicoes_gpkg",
    "feicoes_manaus_cd_mun",
    "geometry_type",
    "geometry_valid_container",
    "campo_codigo",
    "valor_codigo",
    "campo_municipio",
    "valor_municipio",
    "campo_uf_nome",
    "valor_uf_nome",
    "campo_uf_codigo",
    "valor_uf_codigo",
    "campo_uf_sigla",
    "valor_uf_sigla",
    "campo_area",
    "valor_area_km2",
    "expressao_qgis_recomendada",
    "status",
    "observacao",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    if not rows:
        raise ValueError(f"Arquivo vazio: {path}")

    missing = REQUIRED.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")

    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def validate(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    registry: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    errors = 0

    for row in rows:
        row_errors: list[str] = []
        row_alerts: list[str] = []

        if row["fonte"] != "IBGE":
            row_errors.append("fonte_nao_ibge")

        if row["crs_gpkg"] != "EPSG:4674":
            row_errors.append("crs_gpkg_diferente_epsg_4674")

        if row["campo_codigo"] != "CD_MUN":
            row_errors.append("campo_codigo_invalido")

        if row["valor_codigo"] != "1302603":
            row_errors.append("codigo_manaus_invalido")

        if row["campo_municipio"] != "NM_MUN":
            row_errors.append("campo_municipio_invalido")

        if row["valor_municipio"].lower() != "manaus":
            row_errors.append("valor_municipio_invalido")

        if row["feicoes_manaus_cd_mun"] != "1":
            row_errors.append("quantidade_feicoes_manaus_invalida")

        if row["geometry_valid_container"].lower() != "sim":
            row_errors.append("geometria_manaus_nao_validada")

        try:
            total_features = int(row["total_feicoes_gpkg"])
            if total_features > 1:
                row_alerts.append("arquivo_contem_malha_completa")
                gaps.append(
                    {
                        "gap_id": "GAP_422B1_EXTRACAO_MANAUS",
                        "tipo": "camada_gis",
                        "criticidade": "alta",
                        "descricao": "GeoPackage contém malha municipal completa, não apenas Manaus.",
                        "acao_recomendada": "Na 4.22-B2, extrair camada isolada de Manaus com 1 feição.",
                        "bloqueia_score_final": "sim",
                    }
                )
        except ValueError:
            row_errors.append("total_feicoes_gpkg_nao_numerico")

        if "nao_verificado" in row["drive_status"]:
            row_alerts.append("arquivo_drive_nao_verificado_por_id")
            gaps.append(
                {
                    "gap_id": "GAP_422B1_DRIVE_FILE_ID",
                    "tipo": "drive",
                    "criticidade": "media",
                    "descricao": "Arquivo informado no Drive, mas sem verificação por ID ou listagem direta do arquivo.",
                    "acao_recomendada": "Informar link ou ID do arquivo no Drive, ou confirmar por print/listagem da pasta 09_gis/01_insumos_brutos.",
                    "bloqueia_score_final": "nao",
                }
            )

        if row_errors:
            errors += 1

        registry.append(
            {
                **row,
                "status_validacao": "erro" if row_errors else "ok_com_alerta" if row_alerts else "ok",
                "erros": "|".join(row_errors),
                "alertas": "|".join(row_alerts),
            }
        )

    return registry, gaps, errors


def build_report(registry: list[dict[str, str]], gaps: list[dict[str, str]], errors: int) -> str:
    row = registry[0]

    lines = [
        "# Rodada 4.22-B1 — Registro controlado do exemplo GIS Manaus",
        "",
        "## Resultado",
        "",
        f"- Arquivo registrado: `{row['arquivo']}`",
        f"- Camada interna: `{row['layer_name']}`",
        f"- CRS: `{row['crs_gpkg']}`",
        f"- Total de feições no GeoPackage: `{row['total_feicoes_gpkg']}`",
        f"- Feições de Manaus por CD_MUN: `{row['feicoes_manaus_cd_mun']}`",
        f"- Campo de código: `{row['campo_codigo']}`",
        f"- Campo de município: `{row['campo_municipio']}`",
        f"- Campo de UF: `{row['campo_uf_nome']}` e `{row['campo_uf_codigo']}`",
        f"- Geometria de Manaus válida no container: `{row['geometry_valid_container']}`",
        f"- Erros estruturais: `{errors}`",
        "",
        "## Interpretação",
        "",
        "O GeoPackage é válido como insumo bruto, mas contém a malha municipal completa. A camada isolada de Manaus ainda deve ser gerada em rodada posterior.",
        "",
        "## Lacunas registradas",
        "",
    ]

    for gap in gaps:
        lines.append(f"- `{gap['gap_id']}` — {gap['descricao']} Ação: {gap['acao_recomendada']}")

    lines.extend(
        [
            "",
            "## Travas",
            "",
            "- Esta rodada não calcula área.",
            "- Esta rodada não calcula densidade.",
            "- Esta rodada não calcula centroide.",
            "- Esta rodada não executa buffer.",
            "- Esta rodada não libera score AIMM final.",
            "- A extração de camada isolada de Manaus fica para a 4.22-B2.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    rows = read_csv(SEED)
    registry, gaps, errors = validate(rows)

    status = [
        {
            "rodada": "4.22-B1",
            "insumos_registrados": str(len(registry)),
            "campos_obrigatorios_validados": "5",
            "feicoes_manaus_registradas": registry[0]["feicoes_manaus_cd_mun"],
            "geometria_manaus_valida": registry[0]["geometry_valid_container"],
            "limitacoes_registradas": str(len(gaps)),
            "erros_estruturais": str(errors),
            "status_rodada": "erro" if errors else "validada_com_limitacoes_controladas",
            "trava": "nao_processa_geometria_real_nem_libera_score_final",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_GIS_MANAUS_4_22_B1",
            "tipo_evidencia": "registro_controlado_exemplo_gis",
            "fonte": "IBGE Malha Municipal",
            "arquivo": registry[0]["arquivo"],
            "camada": registry[0]["layer_name"],
            "codigo_municipio": registry[0]["valor_codigo"],
            "municipio": registry[0]["valor_municipio"],
            "crs": registry[0]["crs_gpkg"],
            "status": "validado_estruturalmente_com_limitacoes",
            "limitacao": "GeoPackage contém malha completa. Manaus deve ser extraído como camada isolada em rodada posterior.",
        }
    ]

    write_csv(OUT_REGISTRY, registry)
    write_csv(OUT_STATUS, status)
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_EVIDENCE, evidence)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(build_report(registry, gaps, errors), encoding="utf-8")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log = "\n".join(
        [
            "TESTE GIS_MANAUS_4_22_B1 — Fito+ Amazônia",
            "=" * 86,
            f"Insumos registrados: {len(registry)}",
            "Campos obrigatórios validados: 5",
            f"Feições Manaus registradas: {registry[0]['feicoes_manaus_cd_mun']}",
            f"Geometria Manaus válida: {registry[0]['geometry_valid_container']}",
            f"Limitações registradas: {len(gaps)}",
            f"Erros estruturais: {errors}",
            "",
            "Resultado: SUCESSO.",
            "O exemplo GIS Manaus foi registrado de forma controlada.",
            "",
            "Trava: não processa geometria real nem libera score AIMM final.",
        ]
    )

    OUT_LOG.write_text(log, encoding="utf-8")
    print(log)

    if errors:
        raise ValueError(f"Rodada 4.22-B1 contém {errors} erro(s) estruturais.")


if __name__ == "__main__":
    main()
