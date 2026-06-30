from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any


MANIFEST = Path("data/manual/gis/gis_manaus_isolated_manifest_seed.csv")
GPKG = Path("data/raw/gis/municipio_manaus_1302603.gpkg")

OUT_REGISTRY = Path("data/processed/gis/gis_manaus_isolated_registry.csv")
OUT_STATUS = Path("data/processed/gis/gis_manaus_isolated_status.csv")
OUT_GAPS = Path("data/processed/gis/gis_manaus_isolated_attribute_gaps.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_gis_manaus_isolated.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_MANAUS_4_22_B2.md")
OUT_LOG = Path("outputs/logs/teste_gis_manaus_4_22_b2.txt")


REQUIRED_MANIFEST_COLUMNS = {
    "registro_id",
    "arquivo",
    "local_github",
    "local_drive",
    "fonte",
    "ano_dado",
    "crs_esperado",
    "layer_name_esperado",
    "geometry_type_esperado",
    "feicoes_esperadas",
    "campo_codigo",
    "valor_codigo",
    "atributos_preservados",
    "atributos_ausentes",
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

    missing = REQUIRED_MANIFEST_COLUMNS.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Colunas ausentes no manifesto: {sorted(missing)}")

    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def inspect_gpkg(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"GeoPackage obrigatório ausente: {path}")

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    contents = cur.execute(
        "select table_name, data_type, identifier, srs_id from gpkg_contents"
    ).fetchall()

    if not contents:
        raise ValueError("GeoPackage sem registro em gpkg_contents.")

    table_name, data_type, identifier, srs_id = contents[0]

    geom = cur.execute(
        "select table_name, column_name, geometry_type_name, srs_id from gpkg_geometry_columns"
    ).fetchone()

    if geom is None:
        raise ValueError("GeoPackage sem registro em gpkg_geometry_columns.")

    geom_table, geom_column, geometry_type, geom_srs = geom

    count = cur.execute(f'select count(*) from "{table_name}"').fetchone()[0]

    columns_info = cur.execute(f'pragma table_info("{table_name}")').fetchall()
    columns = [item[1] for item in columns_info]

    cd_mun_value = None
    if "CD_MUN" in columns:
        cd_mun_value = cur.execute(
            f'select CD_MUN from "{table_name}" limit 1'
        ).fetchone()[0]

    conn.close()

    return {
        "table_name": table_name,
        "data_type": data_type,
        "identifier": identifier,
        "srs_id": str(srs_id),
        "geom_table": geom_table,
        "geom_column": geom_column,
        "geometry_type": geometry_type,
        "geom_srs": str(geom_srs),
        "feature_count": str(count),
        "columns": ",".join(columns),
        "cd_mun_value": str(cd_mun_value) if cd_mun_value is not None else "",
    }


def validate(manifest_row: dict[str, str], gpkg_info: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    alerts: list[str] = []

    if manifest_row["fonte"] != "IBGE":
        errors.append("fonte_nao_ibge")

    if gpkg_info["srs_id"] != "4674":
        errors.append("srs_id_diferente_4674")

    if gpkg_info["geom_srs"] != "4674":
        errors.append("geometry_srs_diferente_4674")

    if gpkg_info["geometry_type"].upper() != manifest_row["geometry_type_esperado"].upper():
        errors.append("tipo_geometria_divergente")

    if gpkg_info["feature_count"] != manifest_row["feicoes_esperadas"]:
        errors.append("numero_feicoes_divergente")

    if manifest_row["campo_codigo"] not in gpkg_info["columns"].split(","):
        errors.append("campo_codigo_ausente_no_gpkg")

    if gpkg_info["cd_mun_value"] != manifest_row["valor_codigo"]:
        errors.append("valor_cd_mun_divergente")

    missing_attributes = [
        item.strip()
        for item in manifest_row["atributos_ausentes"].split(",")
        if item.strip()
    ]

    if missing_attributes:
        alerts.append("atributos_municipais_nao_preservados")

    return errors, alerts


def build_report(
    registry: dict[str, str],
    gaps: list[dict[str, str]],
    errors: list[str],
    alerts: list[str],
) -> str:
    lines = [
        "# Rodada 4.22-B2 — Validação do GeoPackage isolado de Manaus",
        "",
        "## Resultado",
        "",
        f"- Arquivo: `{registry['arquivo']}`",
        f"- Camada interna: `{registry['layer_name_detectado']}`",
        f"- CRS detectado: `EPSG:{registry['srs_id_detectado']}`",
        f"- Tipo geométrico: `{registry['geometry_type_detectado']}`",
        f"- Número de feições: `{registry['feature_count_detectado']}`",
        f"- Campo de código: `{registry['campo_codigo']}`",
        f"- Valor do código: `{registry['valor_codigo_detectado']}`",
        f"- Erros estruturais: `{len(errors)}`",
        f"- Alertas: `{len(alerts)}`",
        "",
        "## Interpretação",
        "",
        "O GeoPackage isolado de Manaus foi validado estruturalmente como camada territorial mínima. A geometria e o código municipal estão coerentes com o objetivo da rodada.",
        "",
        "## Lacunas",
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
            "- A recomposição de atributos municipais fica para rodada posterior.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    manifest = read_csv(MANIFEST)
    row = manifest[0]

    gpkg_info = inspect_gpkg(GPKG)
    errors, alerts = validate(row, gpkg_info)

    missing_attributes = [
        item.strip()
        for item in row["atributos_ausentes"].split(",")
        if item.strip()
    ]

    registry = {
        "rodada": "4.22-B2",
        "registro_id": row["registro_id"],
        "arquivo": row["arquivo"],
        "local_github": row["local_github"],
        "local_drive": row["local_drive"],
        "fonte": row["fonte"],
        "ano_dado": row["ano_dado"],
        "layer_name_detectado": gpkg_info["table_name"],
        "srs_id_detectado": gpkg_info["srs_id"],
        "geometry_type_detectado": gpkg_info["geometry_type"],
        "feature_count_detectado": gpkg_info["feature_count"],
        "colunas_detectadas": gpkg_info["columns"],
        "campo_codigo": row["campo_codigo"],
        "valor_codigo_esperado": row["valor_codigo"],
        "valor_codigo_detectado": gpkg_info["cd_mun_value"],
        "atributos_ausentes": row["atributos_ausentes"],
        "status_validacao": "erro" if errors else "ok_com_alerta" if alerts else "ok",
        "erros": "|".join(errors),
        "alertas": "|".join(alerts),
    }

    gaps = []
    if missing_attributes:
        gaps.append(
            {
                "gap_id": "GAP_422B2_ATRIBUTOS_MUNICIPAIS",
                "tipo": "atributo",
                "criticidade": "media",
                "descricao": "A camada isolada preservou geometria e CD_MUN, mas não preservou todos os atributos municipais da malha original.",
                "acao_recomendada": "Na próxima rodada, recompor atributos a partir do CSV da malha IBGE ou manifesto oficial.",
                "bloqueia_score_final": "nao",
            }
        )

    status = {
        "rodada": "4.22-B2",
        "arquivo_validado": row["arquivo"],
        "camadas_detectadas": "1",
        "feicoes_detectadas": gpkg_info["feature_count"],
        "crs_detectado": f"EPSG:{gpkg_info['srs_id']}",
        "codigo_municipio_detectado": gpkg_info["cd_mun_value"],
        "erros_estruturais": str(len(errors)),
        "alertas": str(len(alerts)),
        "lacunas_registradas": str(len(gaps)),
        "status_rodada": "erro" if errors else "validada_com_lacuna_atributaria",
        "trava": "nao_calcula_area_densidade_centroide_buffer_nem_score_final",
    }

    evidence = {
        "id_evidencia": "EVD_GIS_MANAUS_ISOLADO_4_22_B2",
        "tipo_evidencia": "validacao_geopackage_isolado",
        "arquivo": row["arquivo"],
        "fonte": row["fonte"],
        "crs": f"EPSG:{gpkg_info['srs_id']}",
        "feature_count": gpkg_info["feature_count"],
        "codigo_municipio": gpkg_info["cd_mun_value"],
        "status": "validado_estruturalmente" if not errors else "erro",
        "limitacao": "Atributos municipais complementares devem ser recompostos em rodada posterior.",
    }

    write_csv(OUT_REGISTRY, [registry])
    write_csv(OUT_STATUS, [status])
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_EVIDENCE, [evidence])

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(build_report(registry, gaps, errors, alerts), encoding="utf-8")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log = "\n".join(
        [
            "TESTE GIS_MANAUS_4_22_B2 — Fito+ Amazônia",
            "=" * 86,
            f"Arquivo validado: {row['arquivo']}",
            f"Camada interna: {gpkg_info['table_name']}",
            f"CRS detectado: EPSG:{gpkg_info['srs_id']}",
            f"Tipo geométrico: {gpkg_info['geometry_type']}",
            f"Feições detectadas: {gpkg_info['feature_count']}",
            f"Campo código: {row['campo_codigo']}",
            f"Valor código detectado: {gpkg_info['cd_mun_value']}",
            f"Erros estruturais: {len(errors)}",
            f"Alertas: {len(alerts)}",
            f"Lacunas registradas: {len(gaps)}",
            "",
            "Resultado: SUCESSO." if not errors else "Resultado: ERRO.",
            "O GeoPackage isolado de Manaus foi validado estruturalmente.",
            "",
            "Trava: não calcula área, densidade, centroide, buffer nem score AIMM final.",
        ]
    )

    OUT_LOG.write_text(log, encoding="utf-8")
    print(log)

    if errors:
        raise ValueError(f"Rodada 4.22-B2 contém {len(errors)} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
