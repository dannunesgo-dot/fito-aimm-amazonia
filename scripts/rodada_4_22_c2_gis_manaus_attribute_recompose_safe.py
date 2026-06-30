from __future__ import annotations

import csv
import shutil
import sqlite3
from pathlib import Path
from typing import Any


SEED = Path("data/manual/gis/gis_manaus_attribute_recomposition_seed.csv")
GPKG_IN = Path("data/raw/gis/municipio_manaus_1302603.gpkg")

OUT_GPKG = Path("outputs/gis/municipio_manaus_1302603_atributos.gpkg")
OUT_REGISTRY = Path("data/processed/gis/gis_manaus_attribute_recomposition_registry_c2.csv")
OUT_STATUS = Path("data/processed/gis/gis_manaus_attribute_recomposition_status_c2.csv")
OUT_GAPS = Path("data/processed/gis/gis_manaus_attribute_recomposition_gaps_c2.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_gis_manaus_attribute_recomposition_c2.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_MANAUS_4_22_C2.md")
OUT_LOG = Path("outputs/logs/teste_gis_manaus_4_22_c2.txt")


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


def table_columns(cur: sqlite3.Cursor, table_name: str) -> list[str]:
    return [
        row[1]
        for row in cur.execute(f"pragma table_info({qident(table_name)})").fetchall()
    ]


def inspect_gpkg(conn: sqlite3.Connection) -> dict[str, Any]:
    cur = conn.cursor()

    content = cur.execute(
        """
        select table_name, data_type, identifier, srs_id
        from gpkg_contents
        where data_type = 'features'
        limit 1
        """
    ).fetchone()

    if content is None:
        raise ValueError("GeoPackage sem camada vetorial registrada em gpkg_contents.")

    table_name, data_type, identifier, srs_id = content

    geom = cur.execute(
        """
        select table_name, column_name, geometry_type_name, srs_id
        from gpkg_geometry_columns
        where table_name = ?
        limit 1
        """,
        (table_name,),
    ).fetchone()

    if geom is None:
        raise ValueError("GeoPackage sem registro correspondente em gpkg_geometry_columns.")

    _, geom_column, geometry_type, geom_srs = geom

    feature_count = cur.execute(
        f"select count(*) from {qident(table_name)}"
    ).fetchone()[0]

    geometry_blob_count = cur.execute(
        f"""
        select count(*)
        from {qident(table_name)}
        where {qident(geom_column)} is not null
          and length({qident(geom_column)}) > 0
        """
    ).fetchone()[0]

    return {
        "table_name": table_name,
        "data_type": data_type,
        "identifier": identifier,
        "srs_id": str(srs_id),
        "geom_column": geom_column,
        "geometry_type": str(geometry_type).upper(),
        "geom_srs": str(geom_srs),
        "feature_count": int(feature_count),
        "geometry_blob_count": int(geometry_blob_count),
        "columns": table_columns(cur, table_name),
    }


def add_column_if_missing(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    cur = conn.cursor()
    existing = table_columns(cur, table_name)

    if column_name not in existing:
        cur.execute(
            f"alter table {qident(table_name)} add column {qident(column_name)} {column_type}"
        )


def main() -> None:
    rows = read_csv(SEED)
    seed = rows[0]

    if not GPKG_IN.exists():
        raise FileNotFoundError(f"GeoPackage obrigatório ausente: {GPKG_IN}")

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GPKG_IN, OUT_GPKG)

    errors: list[str] = []
    alerts: list[str] = []
    gaps: list[dict[str, str]] = []

    conn = sqlite3.connect(OUT_GPKG)
    cur = conn.cursor()

    info_before = inspect_gpkg(conn)
    table_name = info_before["table_name"]
    campo_codigo = seed["campo_codigo"]

    if info_before["srs_id"] != "4674":
        errors.append("crs_diferente_epsg_4674")

    if info_before["geom_srs"] != "4674":
        errors.append("crs_geometria_diferente_epsg_4674")

    if info_before["geometry_type"] != "MULTIPOLYGON":
        errors.append("tipo_geometrico_diferente_multipolygon")

    if info_before["feature_count"] != 1:
        errors.append("numero_feicoes_diferente_de_1")

    if info_before["geometry_blob_count"] != 1:
        errors.append("geometria_nula_ou_sem_blob")

    if campo_codigo not in info_before["columns"]:
        errors.append("campo_codigo_ausente")

    if not errors:
        codigo_detectado = cur.execute(
            f"""
            select cast({qident(campo_codigo)} as text)
            from {qident(table_name)}
            limit 1
            """
        ).fetchone()[0]

        if str(codigo_detectado) != seed["codigo_ibge"]:
            errors.append("codigo_ibge_divergente")

    if not errors:
        add_column_if_missing(conn, table_name, "NM_MUN", "TEXT")
        add_column_if_missing(conn, table_name, "NM_UF", "TEXT")
        add_column_if_missing(conn, table_name, "CD_UF", "TEXT")
        add_column_if_missing(conn, table_name, "SIGLA_UF", "TEXT")
        add_column_if_missing(conn, table_name, "AREA_KM2", "REAL")

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
                seed["nm_mun"],
                seed["nm_uf"],
                seed["cd_uf"],
                seed["sigla_uf"],
                parse_area(seed["area_km2"]),
                seed["codigo_ibge"],
            ),
        )

        if cur.rowcount != 1:
            errors.append(f"linhas_atualizadas_incorretas_{cur.rowcount}")

    conn.commit()

    info_after = inspect_gpkg(conn)

    final_values = cur.execute(
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

    if final_values is None:
        errors.append("registro_final_nao_encontrado")
        final_values = ("", "", "", "", "", "")

    codigo_final, nm_mun, nm_uf, cd_uf, sigla_uf, area_km2 = final_values

    if str(codigo_final) != seed["codigo_ibge"]:
        errors.append("codigo_final_divergente")

    if str(nm_mun) != seed["nm_mun"]:
        errors.append("nm_mun_divergente")

    if str(nm_uf) != seed["nm_uf"]:
        errors.append("nm_uf_divergente")

    if str(cd_uf) != seed["cd_uf"]:
        errors.append("cd_uf_divergente")

    if str(sigla_uf) != seed["sigla_uf"]:
        errors.append("sigla_uf_divergente")

    if abs(float(area_km2) - parse_area(seed["area_km2"])) > 0.000001:
        errors.append("area_km2_divergente")

    alerts.append("area_km2_recomposta_como_atributo_nao_calculada")

    gaps.append(
        {
            "gap_id": "GAP_422C2_VALIDACAO_VISUAL_QGIS",
            "tipo": "validacao_visual",
            "criticidade": "baixa",
            "descricao": "Validação visual no QGIS ainda deve ser feita após download do GeoPackage recomposto.",
            "acao_recomendada": "Abrir o arquivo municipio_manaus_1302603_atributos.gpkg no QGIS e conferir tabela de atributos.",
            "bloqueia_score_final": "nao",
        }
    )

    registry = {
        "rodada": "4.22-C2",
        "registro_id": seed["registro_id"],
        "arquivo_entrada": str(GPKG_IN),
        "arquivo_saida": str(OUT_GPKG),
        "table_name": info_after["table_name"],
        "crs_detectado": f"EPSG:{info_after['srs_id']}",
        "geometry_type": info_after["geometry_type"],
        "feature_count": str(info_after["feature_count"]),
        "geometry_blob_count": str(info_after["geometry_blob_count"]),
        "campo_codigo": campo_codigo,
        "codigo_ibge": str(codigo_final),
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

    status = {
        "rodada": "4.22-C2",
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
        "id_evidencia": "EVD_GIS_MANAUS_ATTR_4_22_C2",
        "tipo_evidencia": "recomposicao_atributaria_sqlite_segura",
        "arquivo_entrada": str(GPKG_IN),
        "arquivo_saida": str(OUT_GPKG),
        "codigo_ibge": str(codigo_final),
        "municipio": str(nm_mun),
        "uf": str(sigla_uf),
        "area_km2": str(float(area_km2)),
        "status": "validado_estruturalmente" if not errors else "erro",
        "limitacao": "AREA_KM2 foi recomposta como atributo informado, sem cálculo espacial.",
    }

    report = "\n".join(
        [
            "# Rodada 4.22-C2 — Recomposição segura de atributos municipais de Manaus",
            "",
            "## Resultado",
            "",
            f"- Arquivo de entrada: `{GPKG_IN}`",
            f"- Arquivo de saída: `{OUT_GPKG}`",
            f"- CRS detectado: `EPSG:{info_after['srs_id']}`",
            f"- Tipo geométrico: `{info_after['geometry_type']}`",
            f"- Feições: `{info_after['feature_count']}`",
            f"- Geometrias com blob: `{info_after['geometry_blob_count']}`",
            f"- Código IBGE: `{codigo_final}`",
            f"- Município: `{nm_mun}`",
            f"- UF: `{nm_uf}`",
            f"- Sigla UF: `{sigla_uf}`",
            f"- Área recomposta como atributo: `{float(area_km2)}` km²",
            f"- Erros estruturais: `{len(errors)}`",
            f"- Alertas: `{len(alerts)}`",
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
    )

    write_csv(OUT_REGISTRY, [registry])
    write_csv(OUT_STATUS, [status])
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_EVIDENCE, [evidence])

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log = "\n".join(
        [
            "TESTE GIS_MANAUS_4_22_C2 — Fito+ Amazônia",
            "=" * 86,
            f"Arquivo de entrada: {GPKG_IN}",
            f"Arquivo de saída: {OUT_GPKG}",
            "Atributos recompostos: 5",
            "Feições atualizadas: 1",
            f"Município: {nm_mun}",
            f"UF: {sigla_uf}",
            f"Área km² recomposta: {float(area_km2)}",
            f"Erros estruturais: {len(errors)}",
            f"Alertas: {len(alerts)}",
            f"Lacunas registradas: {len(gaps)}",
            "",
            "Resultado: SUCESSO." if not errors else "Resultado: ERRO.",
            "A camada isolada de Manaus teve seus atributos municipais recompostos por script SQLite seguro.",
            "",
            "Trava: não calcula área, densidade, centroide, buffer nem score AIMM final.",
        ]
    )

    OUT_LOG.write_text(log, encoding="utf-8")
    print(log)

    if errors:
        raise ValueError(f"Rodada 4.22-C2 contém {len(errors)} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
