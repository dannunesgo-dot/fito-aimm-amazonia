from __future__ import annotations

import csv
import shutil
import sqlite3
from pathlib import Path
from typing import Any


SEED = Path("data/manual/gis/gis_manaus_attribute_recomposition_seed.csv")
GPKG_IN = Path("data/raw/gis/municipio_manaus_1302603.gpkg")

OUT_GPKG = Path("outputs/gis/municipio_manaus_1302603_atributos.gpkg")
OUT_REGISTRY = Path("data/processed/gis/gis_manaus_attribute_recomposition_registry.csv")
OUT_STATUS = Path("data/processed/gis/gis_manaus_attribute_recomposition_status.csv")
OUT_GAPS = Path("data/processed/gis/gis_manaus_attribute_recomposition_gaps.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_gis_manaus_attribute_recomposition.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_MANAUS_4_22_C.md")
OUT_LOG = Path("outputs/logs/teste_gis_manaus_4_22_c.txt")


REQUIRED_COLUMNS = {
    "registro_id",
    "arquivo_entrada",
    "arquivo_saida",
    "codigo_ibge",
    "campo_codigo",
    "nm_mun",
    "nm_uf",
    "cd_uf",
    "sigla_uf",
    "area_km2",
    "fonte_atributos",
    "status",
    "observacao",
}


def qident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def parse_area(value: str) -> float:
    value = str(value).strip()

    if "," in value:
        value = value.replace(".", "").replace(",", ".")

    return float(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    if not rows:
        raise ValueError(f"Arquivo vazio: {path}")

    missing = REQUIRED_COLUMNS.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Colunas ausentes no seed: {sorted(missing)}")

    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def get_single_row(cur: sqlite3.Cursor, sql: str) -> tuple[Any, ...]:
    row = cur.execute(sql).fetchone()

    if row is None:
        raise ValueError(f"Consulta sem retorno: {sql}")

    return row


def get_gpkg_info(conn: sqlite3.Connection) -> dict[str, Any]:
    cur = conn.cursor()

    content = cur.execute(
        "select table_name, data_type, identifier, srs_id from gpkg_contents limit 1"
    ).fetchone()

    if content is None:
        raise ValueError("GeoPackage sem registro em gpkg_contents.")

    table_name, data_type, identifier, srs_id = content

    geometry = cur.execute(
        "select table_name, column_name, geometry_type_name, srs_id from gpkg_geometry_columns limit 1"
    ).fetchone()

    if geometry is None:
        raise ValueError("GeoPackage sem registro em gpkg_geometry_columns.")

    geom_table, geom_column, geometry_type, geom_srs = geometry

    feature_count = get_single_row(
        cur,
        f"select count(*) from {qident(table_name)}",
    )[0]

    geometry_blob_count = get_single_row(
        cur,
        f"""
        select count(*)
        from {qident(table_name)}
        where {qident(geom_column)} is not null
          and length({qident(geom_column)}) > 0
        """,
    )[0]

    columns_info = cur.execute(
        f"pragma table_info({qident(table_name)})"
    ).fetchall()

    columns = [item[1] for item in columns_info]

    return {
        "table_name": table_name,
        "data_type": data_type,
        "identifier": identifier,
        "srs_id": str(srs_id),
        "geom_table": geom_table,
        "geom_column": geom_column,
        "geometry_type": str(geometry_type).upper(),
        "geom_srs": str(geom_srs),
        "feature_count": int(feature_count),
        "geometry_blob_count": int(geometry_blob_count),
        "columns": columns,
    }


def add_column_if_missing(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    cur = conn.cursor()

    existing_columns = [
        item[1]
        for item in cur.execute(f"pragma table_info({qident(table_name)})").fetchall()
    ]

    if column_name not in existing_columns:
        cur.execute(
            f"alter table {qident(table_name)} add column {qident(column_name)} {column_type}"
        )


def validate_initial_state(
    row: dict[str, str],
    info: dict[str, Any],
    cur: sqlite3.Cursor,
) -> list[str]:
    errors: list[str] = []

    table_name = info["table_name"]
    campo_codigo = row["campo_codigo"]

    if info["srs_id"] != "4674":
        errors.append("crs_diferente_epsg_4674")

    if info["geom_srs"] != "4674":
        errors.append("crs_geometria_diferente_epsg_4674")

    if info["feature_count"] != 1:
        errors.append("numero_feicoes_diferente_de_1")

    if info["geometry_blob_count"] != 1:
        errors.append("geometria_nula_ou_sem_blob")

    if info["geometry_type"] != "MULTIPOLYGON":
        errors.append("tipo_geometrico_diferente_multipolygon")

    if campo_codigo not in info["columns"]:
        errors.append("campo_codigo_ausente")
        return errors

    codigo_detectado = get_single_row(
        cur,
        f"select cast({qident(campo_codigo)} as text) from {qident(table_name)} limit 1",
    )[0]

    if str(codigo_detectado) != row["codigo_ibge"]:
        errors.append("codigo_ibge_divergente")

    return errors


def recompose_attributes(row: dict[str, str]) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, str]]]:
    if not GPKG_IN.exists():
        raise FileNotFoundError(f"GeoPackage obrigatório ausente: {GPKG_IN}")

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GPKG_IN, OUT_GPKG)

    errors: list[str] = []
    alerts: list[str] = []
    gaps: list[dict[str, str]] = []

    conn = sqlite3.connect(OUT_GPKG)
    cur = conn.cursor()

    info_before = get_gpkg_info(conn)
    table_name = info_before["table_name"]
    campo_codigo = row["campo_codigo"]

    errors.extend(validate_initial_state(row, info_before, cur))

    if not errors:
        add_column_if_missing(conn, table_name, "NM_MUN", "TEXT")
        add_column_if_missing(conn, table_name, "NM_UF", "TEXT")
        add_column_if_missing(conn, table_name, "CD_UF", "TEXT")
        add_column_if_missing(conn, table_name, "SIGLA_UF", "TEXT")
        add_column_if_missing(conn, table_name, "AREA_KM2", "REAL")

        area = parse_area(row["area_km2"])

        cur.execute(
            f"""
            update {qident(table_name)}
            set
                {qident("NM_MUN")} = ?,
                {qident("NM_UF")} = ?,
                {qident("CD_UF")} = ?,
                {qident("SIGLA_UF")} = ?,
                {qident("AREA_KM2")} = ?
            where cast({qident(campo_codigo)} as text) = ?
            """,
            (
                row["nm_mun"],
                row["nm_uf"],
                row["cd_uf"],
                row["sigla_uf"],
                area,
                row["codigo_ibge"],
            ),
        )

        if cur.rowcount != 1:
            errors.append(f"linhas_atualizadas_incorretas_{cur.rowcount}")

    conn.commit()

    info_after = get_gpkg_info(conn)

    values = cur.execute(
        f"""
        select
            cast({qident(campo_codigo)} as text),
            {qident("NM_MUN")},
            {qident("NM_UF")},
            cast({qident("CD_UF")} as text),
            {qident("SIGLA_UF")},
            {qident("AREA_KM2")}
        from {qident(table_name)}
        limit 1
        """
    ).fetchone()

    conn.close()

    if values is None:
        errors.append("registro_recomposto_nao_encontrado")
        values = ("", "", "", "", "", "")

    codigo, nm_mun, nm_uf, cd_uf, sigla_uf, area_km2 = values

    if str(codigo) != row["codigo_ibge"]:
        errors.append("codigo_recomposto_divergente")

    if str(nm_mun) != row["nm_mun"]:
        errors.append("nm_mun_divergente")

    if str(nm_uf) != row["nm_uf"]:
        errors.append("nm_uf_divergente")

    if str(cd_uf) != row["cd_uf"]:
        errors.append("cd_uf_divergente")

    if str(sigla_uf) != row["sigla_uf"]:
        errors.append("sigla_uf_divergente")

    if abs(float(area_km2) - parse_area(row["area_km2"])) > 0.000001:
        errors.append("area_km2_divergente")

    alerts.append("area_km2_recomposta_como_atributo_nao_calculada")

    gaps.append(
        {
            "gap_id": "GAP_422C_VALIDACAO_VISUAL_QGIS",
            "tipo": "validacao_visual",
            "criticidade": "baixa",
            "descricao": "A recomposição foi estrutural. Validação visual em QGIS deve ser registrada em rodada posterior.",
            "acao_recomendada": "Abrir o GeoPackage recomposto no QGIS e confirmar visualmente geometria e tabela de atributos.",
            "bloqueia_score_final": "nao",
        }
    )

    registry = {
        "rodada": "4.22-C",
        "registro_id": row["registro_id"],
        "arquivo_entrada": str(GPKG_IN),
        "arquivo_saida": str(OUT_GPKG),
        "table_name": info_after["table_name"],
        "crs_detectado": f"EPSG:{info_after['srs_id']}",
        "geometry_type": info_after["geometry_type"],
        "feature_count": str(info_after["feature_count"]),
        "geometry_blob_count": str(info_after["geometry_blob_count"]),
        "campo_codigo": campo_codigo,
        "codigo_ibge": row["codigo_ibge"],
        "NM_MUN": str(nm_mun),
        "NM_UF": str(nm_uf),
        "CD_UF": str(cd_uf),
        "SIGLA_UF": str(sigla_uf),
        "AREA_KM2": str(float(area_km2)),
        "colunas_finais": ",".join(info_after["columns"]),
        "status_validacao": "erro" if errors else "ok_com_alerta",
        "erros": "|".join(errors),
        "alertas": "|".join(alerts),
    }

    return registry, errors, alerts, gaps


def build_report(
    registry: dict[str, Any],
    gaps: list[dict[str, str]],
    errors: list[str],
    alerts: list[str],
) -> str:
    lines = [
        "# Rodada 4.22-C — Recomposição de atributos municipais de Manaus",
        "",
        "## Resultado",
        "",
        f"- Arquivo de entrada: `{registry['arquivo_entrada']}`",
        f"- Arquivo de saída: `{registry['arquivo_saida']}`",
        f"- CRS detectado: `{registry['crs_detectado']}`",
        f"- Tipo geométrico: `{registry['geometry_type']}`",
        f"- Feições: `{registry['feature_count']}`",
        f"- Geometrias com blob: `{registry['geometry_blob_count']}`",
        f"- Código IBGE: `{registry['codigo_ibge']}`",
        f"- Município: `{registry['NM_MUN']}`",
        f"- UF: `{registry['NM_UF']}`",
        f"- Sigla UF: `{registry['SIGLA_UF']}`",
        f"- Área recomposta como atributo: `{registry['AREA_KM2']}` km²",
        f"- Erros estruturais: `{len(errors)}`",
        f"- Alertas: `{len(alerts)}`",
        "",
        "## Interpretação",
        "",
        "A camada isolada de Manaus teve seus atributos municipais recompostos. A geometria não foi alterada e a área não foi recalculada.",
        "",
        "## Travas",
        "",
        "- Não houve cálculo espacial.",
        "- Não houve cálculo de área.",
        "- Não houve cálculo de densidade.",
        "- Não houve cálculo de centroide.",
        "- Não houve cálculo de buffer.",
        "- Score AIMM final permanece bloqueado.",
    ]

    if gaps:
        lines.append("")
        lines.append("## Lacunas")
        lines.append("")

        for gap in gaps:
            lines.append(f"- `{gap['gap_id']}` — {gap['descricao']}")

    return "\n".join(lines)


def main() -> None:
    rows = read_csv(SEED)
    row = rows[0]

    registry, errors, alerts, gaps = recompose_attributes(row)

    status = {
        "rodada": "4.22-C",
        "arquivo_saida": str(OUT_GPKG),
        "atributos_recompostos": "5",
        "feicoes_atualizadas": "1",
        "erros_estruturais": str(len(errors)),
        "alertas": str(len(alerts)),
        "lacunas_registradas": str(len(gaps)),
        "status_rodada": "erro" if errors else "validada_com_alerta_controlado",
        "trava": "nao_calcula_area_densidade_centroide_buffer_nem_score_final",
    }

    evidence = {
        "id_evidencia": "EVD_GIS_MANAUS_ATTR_4_22_C",
        "tipo_evidencia": "recomposicao_atributaria",
        "arquivo_entrada": str(GPKG_IN),
        "arquivo_saida": str(OUT_GPKG),
        "codigo_ibge": row["codigo_ibge"],
        "municipio": row["nm_mun"],
        "uf": row["sigla_uf"],
        "area_km2": str(parse_area(row["area_km2"])),
        "status": "validado_estruturalmente" if not errors else "erro",
        "limitacao": "AREA_KM2 foi recomposta como atributo informado, não calculada espacialmente.",
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
            "TESTE GIS_MANAUS_4_22_C — Fito+ Amazônia",
            "=" * 86,
            f"Arquivo de entrada: {GPKG_IN}",
            f"Arquivo de saída: {OUT_GPKG}",
            "Atributos recompostos: 5",
            "Feições atualizadas: 1",
            f"Município: {registry['NM_MUN']}",
            f"UF: {registry['SIGLA_UF']}",
            f"Área km² recomposta: {registry['AREA_KM2']}",
            f"Erros estruturais: {len(errors)}",
            f"Alertas: {len(alerts)}",
            f"Lacunas registradas: {len(gaps)}",
            "",
            "Resultado: SUCESSO." if not errors else "Resultado: ERRO.",
            "A camada isolada de Manaus teve seus atributos municipais recompostos.",
            "",
            "Trava: não calcula área, densidade, centroide, buffer nem score AIMM final.",
        ]
    )

    OUT_LOG.write_text(log, encoding="utf-8")
    print(log)

    if errors:
        raise ValueError(f"Rodada 4.22-C contém {len(errors)} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
