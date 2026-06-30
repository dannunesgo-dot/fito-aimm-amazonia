from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


SEED = Path("data/reference/gis_baseline_control_seed.csv")

OUT_CONTROL = Path("data/processed/gis/gis_baseline_control_registry.csv")
OUT_STATUS = Path("data/processed/gis/gis_baseline_preparation_status.csv")
OUT_GAPS = Path("data/processed/gis/gis_baseline_open_gaps.csv")

OUT_MUN_TEMPLATE = Path("data/manual/gis/gis_municipality_baseline_manual_template.csv")
OUT_LAYER_MANIFEST = Path("data/manual/gis/gis_layer_submission_manifest_template.csv")
OUT_CRS_TEMPLATE = Path("data/manual/gis/gis_municipality_metric_crs_template.csv")

OUT_EVIDENCE = Path("data/evidence/evidence_gis_baseline_preparation.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_BASELINE_PREPARACAO.md")
OUT_QGIS = Path("outputs/reports/GUIA_QGIS_3_40_14_MANAUS_4_22B.md")
OUT_LOG = Path("outputs/logs/teste_gis_baseline_preparacao_4_22.txt")

REQUIRED_COLUMNS = {
    "tipo",
    "id",
    "codigo_ibge",
    "municipio",
    "uf",
    "item",
    "formato_preferencial",
    "campos_obrigatorios",
    "status",
    "destino",
    "observacao",
}

VALID_TIPOS = {"municipio", "requisito"}
VALID_UF = {"AM", "PA"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    if not rows:
        raise ValueError(f"Arquivo vazio: {path}")

    missing = REQUIRED_COLUMNS.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Colunas ausentes em {path}: {sorted(missing)}")

    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def validate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    validated: list[dict[str, str]] = []

    for row in rows:
        errors: list[str] = []
        alerts: list[str] = []

        tipo = row.get("tipo", "").strip()

        if tipo not in VALID_TIPOS:
            errors.append("tipo_invalido")

        if tipo == "municipio":
            codigo = row.get("codigo_ibge", "").strip()
            uf = row.get("uf", "").strip()

            if len(codigo) != 7 or not codigo.isdigit():
                errors.append("codigo_ibge_invalido")

            if uf not in VALID_UF:
                errors.append("uf_fora_do_escopo")

            alerts.append("municipio_sem_geometria_real")

        if tipo == "requisito":
            if not row.get("campos_obrigatorios", "").strip():
                errors.append("campos_obrigatorios_vazio")

            alerts.append("requisito_pendente")

        validated.append(
            {
                **row,
                "status_validacao": "erro" if errors else "ok_com_lacuna",
                "erros": "|".join(errors),
                "alertas": "|".join(alerts),
            }
        )

    return validated


def build_templates(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    municipios = [row for row in rows if row["tipo"] == "municipio"]

    municipality_template: list[dict[str, str]] = []
    crs_template: list[dict[str, str]] = []

    for row in municipios:
        municipality_template.append(
            {
                "codigo_ibge": row["codigo_ibge"],
                "municipio": row["municipio"],
                "uf": row["uf"],
                "area_km2": "",
                "populacao": "",
                "ano_populacao": "",
                "centroide_lat": "",
                "centroide_lon": "",
                "crs_entrada": "EPSG:4674",
                "crs_metrico_usado": "",
                "fonte_area": "",
                "fonte_populacao": "",
                "arquivo_gis_referencia": "",
                "status_revisao": "pendente",
                "observacao_revisor": "",
            }
        )

        crs_template.append(
            {
                "codigo_ibge": row["codigo_ibge"],
                "municipio": row["municipio"],
                "uf": row["uf"],
                "crs_metrico": "",
                "justificativa": "",
                "status_conferencia": "pendente",
                "observacao": "Preencher antes de calcular área, distância, centroide métrico ou buffer.",
            }
        )

    layer_manifest = [
        {
            "layer_id": "GIS_LYR_001",
            "arquivo": "",
            "tipo_arquivo": "GPKG_ZIP_SHP_GEOJSON",
            "origem": "IBGE_MALHA_MUNICIPAL",
            "codigo_ibge": "",
            "municipio": "",
            "uf": "",
            "crs": "EPSG:4674",
            "campo_codigo_ibge": "",
            "campo_municipio": "",
            "campo_uf": "",
            "numero_feicoes": "",
            "status_revisao_qgis": "pendente",
            "observacao": "",
        },
        {
            "layer_id": "GIS_LYR_001_MANAUS_EXEMPLO",
            "arquivo": "municipio_manaus.gpkg",
            "tipo_arquivo": "GPKG",
            "origem": "IBGE_MALHA_MUNICIPAL_EXPORTADA_NO_QGIS",
            "codigo_ibge": "1302603",
            "municipio": "Manaus",
            "uf": "AM",
            "crs": "EPSG:4674",
            "campo_codigo_ibge": "",
            "campo_municipio": "",
            "campo_uf": "",
            "numero_feicoes": "1",
            "status_revisao_qgis": "pendente",
            "observacao": "Preencher somente após conferência no QGIS.",
        },
    ]

    return municipality_template, layer_manifest, crs_template


def build_gaps(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []

    for row in rows:
        if row["tipo"] == "municipio":
            gaps.append(
                {
                    "id_lacuna": f"GAP_422_{row['codigo_ibge']}",
                    "tipo": "municipio",
                    "item": f"{row['municipio']}/{row['uf']}",
                    "criticidade": "alta",
                    "descricao": "Sem geometria, área, população e centroide validados no baseline GIS.",
                    "acao_recomendada": "Preparar GeoPackage/manifesto no QGIS ou preencher template manual para 4.22-B.",
                    "bloqueia_score_final": "sim",
                }
            )

        if row["tipo"] == "requisito":
            gaps.append(
                {
                    "id_lacuna": f"GAP_422_{row['id']}",
                    "tipo": "requisito",
                    "item": row["item"],
                    "criticidade": "alta" if row["id"] in {"GIS_REQ_001", "GIS_REQ_005"} else "media",
                    "descricao": f"Requisito pendente: {row['item']}",
                    "acao_recomendada": "Inserir arquivo/registro no local indicado e reexecutar a rodada adequada.",
                    "bloqueia_score_final": "sim",
                }
            )

    return gaps


def build_report(status: dict[str, str], gaps: list[dict[str, str]]) -> str:
    lines = [
        "# Rodada 4.22-A — Baseline GIS territorial preparado",
        "",
        "## Resultado",
        "",
        f"- Municípios preparados: `{status['municipios_preparados']}`",
        f"- Requisitos GIS registrados: `{status['requisitos_registrados']}`",
        f"- Templates gerados: `{status['templates_gerados']}`",
        f"- Lacunas abertas: `{status['lacunas_abertas']}`",
        f"- Erros estruturais: `{status['erros_estruturais']}`",
        "- Readiness GIS real: `0.0%`",
        "",
        "## Função da rodada",
        "",
        "Esta rodada prepara o sistema para receber dados GIS no GitHub/Drive e para revisão posterior no QGIS 3.40.14. Ela não processa geometrias reais.",
        "",
        "## Lacunas principais",
        "",
    ]

    for gap in gaps:
        lines.append(f"- `{gap['id_lacuna']}` — {gap['item']}: {gap['acao_recomendada']}")

    lines.extend(
        [
            "",
            "## Travas",
            "",
            "- Não calcular área, distância, densidade, centroide ou buffer nesta rodada.",
            "- Não processar GeoPackage, Shapefile ou GeoJSON nesta rodada.",
            "- Não liberar score AIMM final.",
            "- Exemplo real de Manaus depende de GeoPackage/manifesto validado ou template manual preenchido.",
        ]
    )

    return "\n".join(lines)


def build_qgis_guide() -> str:
    return """# Guia QGIS 3.40.14 — preparação de Manaus para Rodada 4.22-B

## Objetivo

Gerar um arquivo municipal validado de Manaus para processamento futuro.

## Dados mínimos a confirmar

- Fonte da malha municipal.
- CRS da camada.
- Nome do campo do código IBGE.
- Nome do campo de município.
- Nome do campo UF.
- Número de feições selecionadas: deve ser 1 para Manaus.

## Passo a passo no QGIS

1. Abrir QGIS 3.40.14.
2. Menu Camada > Adicionar Camada > Adicionar Camada Vetorial.
3. Carregar a malha municipal oficial.
4. Abrir Propriedades da camada > Fonte e anotar o CRS.
5. Abrir a tabela de atributos.
6. Localizar o campo de código municipal.
7. Selecionar Manaus pelo código 1302603.
8. Clicar com botão direito na camada > Exportar > Salvar Feições Como.
9. Formato: GeoPackage.
10. Nome: municipio_manaus.gpkg.
11. Marcar opção para salvar apenas feições selecionadas.
12. CRS: manter o CRS original da malha, preferencialmente EPSG:4674 quando a fonte estiver em SIRGAS 2000.
13. Salvar e reabrir o GeoPackage.
14. Confirmar que existe 1 feição.
15. Preencher o manifesto gerado pela 4.22-A.

## Proibição operacional

Não calcular área, distância, centroide métrico ou buffer antes de registrar um CRS métrico adequado.
"""


def main() -> None:
    rows = validate_rows(read_csv(SEED))

    errors = sum(1 for row in rows if row["status_validacao"] == "erro")
    municipios = [row for row in rows if row["tipo"] == "municipio"]
    requisitos = [row for row in rows if row["tipo"] == "requisito"]
    gaps = build_gaps(rows)

    municipality_template, layer_manifest, crs_template = build_templates(rows)

    status = {
        "rodada": "4.22-A",
        "municipios_preparados": str(len(municipios)),
        "requisitos_registrados": str(len(requisitos)),
        "templates_gerados": "3",
        "lacunas_abertas": str(len(gaps)),
        "erros_estruturais": str(errors),
        "readiness_gis_real_percentual": "0.0",
        "status_rodada": "erro" if errors else "validada_com_lacunas_controladas",
        "trava": "nao_processa_geometria_real_nem_libera_score_final",
    }

    evidence = [
        {
            "id_evidencia": "EVD_GIS_BASELINE_PREP_4_22_A",
            "tipo_evidencia": "preparacao_operacional_gis",
            "fonte_1": "IBGE Malhas Territoriais",
            "fonte_2": "QGIS 3.40 Vector Geometry",
            "fonte_3": "GeoPandas read_file/to_crs/sjoin",
            "uso_na_calculadora": "Preparar baseline GIS, templates e travas para processamento futuro.",
            "status_conferencia": "validado_estruturalmente",
            "limitacoes": "Sem processamento real de geometrias.",
        }
    ]

    write_csv(OUT_CONTROL, rows)
    write_csv(OUT_STATUS, [status])
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_MUN_TEMPLATE, municipality_template)
    write_csv(OUT_LAYER_MANIFEST, layer_manifest)
    write_csv(OUT_CRS_TEMPLATE, crs_template)
    write_csv(OUT_EVIDENCE, evidence)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(build_report(status, gaps), encoding="utf-8")

    OUT_QGIS.parent.mkdir(parents=True, exist_ok=True)
    OUT_QGIS.write_text(build_qgis_guide(), encoding="utf-8")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log = "\n".join(
        [
            "TESTE GIS_BASELINE_PREPARACAO — Fito+ Amazônia",
            "=" * 86,
            f"Municípios preparados: {len(municipios)}",
            f"Requisitos GIS registrados: {len(requisitos)}",
            "Templates gerados: 3",
            f"Lacunas abertas: {len(gaps)}",
            f"Erros estruturais: {errors}",
            "Readiness GIS real: 0.0%",
            "",
            "Resultado: SUCESSO.",
            "A Rodada 4.22-A preparou o baseline GIS territorial para QGIS/GitHub/Drive.",
            "",
            "Trava: não processa geometria real nem libera score AIMM final.",
        ]
    )

    OUT_LOG.write_text(log, encoding="utf-8")
    print(log)

    if errors:
        raise ValueError(f"Rodada 4.22-A contém {errors} erro(s) estruturais.")


if __name__ == "__main__":
    main()
