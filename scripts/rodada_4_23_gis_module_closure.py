# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


SEED = Path("data/manual/gis/gis_module_closure_4_23_seed.csv")

OUT_REGISTRY = Path("data/processed/gis/gis_module_closure_registry_4_23.csv")
OUT_STATUS = Path("data/processed/gis/gis_module_closure_status_4_23.csv")
OUT_GAPS = Path("data/processed/gis/gis_module_closure_gaps_4_23.csv")
OUT_AIMM_LINK = Path("data/processed/gis/gis_to_aimm_integration_map_4_23.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_gis_module_closure_4_23.csv")
OUT_REPORT = Path("outputs/reports/RELATORIO_GIS_MODULO_MANAUS_4_23.md")
OUT_LOG = Path("outputs/logs/teste_gis_modulo_manaus_4_23.txt")


REQUIRED_COLUMNS = {
    "rodada",
    "modulo",
    "municipio_base",
    "codigo_ibge",
    "rodadas_validadas",
    "drive_gis",
    "baseline_gis_validado",
    "join_qgis_validado",
    "pacote_replicacao_validado",
    "segundo_municipio_testado",
    "score_aimm_liberado",
    "status_modulo",
    "observacao",
}


def read_seed(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    if len(rows) != 1:
        raise ValueError(f"O seed deve conter exatamente 1 linha de dados. Linhas encontradas: {len(rows)}")

    missing = REQUIRED_COLUMNS.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")

    return rows[0]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Nenhuma linha para gravar em {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def norm(value: str) -> str:
    return str(value).strip().lower()


def main() -> None:
    row = read_seed(SEED)

    errors: list[str] = []
    alerts: list[str] = []

    checks = {
        "rodada": row["rodada"] == "4.23",
        "modulo": row["modulo"] == "GIS",
        "municipio_base": row["municipio_base"] == "Manaus",
        "codigo_ibge": row["codigo_ibge"] == "1302603",
        "baseline_gis_validado": norm(row["baseline_gis_validado"]) == "sim",
        "join_qgis_validado": norm(row["join_qgis_validado"]) == "sim",
        "pacote_replicacao_validado": norm(row["pacote_replicacao_validado"]) == "sim",
        "score_aimm_liberado": norm(row["score_aimm_liberado"]) == "nao",
        "status_modulo": norm(row["status_modulo"]) == "encerrado_com_lacunas_controladas",
    }

    for check_name, passed in checks.items():
        if not passed:
            errors.append(f"falha_validacao_{check_name}")

    if norm(row["segundo_municipio_testado"]) != "sim":
        alerts.append("replicacao_em_segundo_municipio_nao_testada")

    alerts.append("modulo_gis_encerrado_sem_liberar_score_aimm_final")

    registry = [
        {
            "rodada": "4.23",
            "modulo": "GIS",
            "municipio_base": row["municipio_base"],
            "codigo_ibge": row["codigo_ibge"],
            "rodadas_validadas": row["rodadas_validadas"],
            "baseline_gis_validado": row["baseline_gis_validado"],
            "join_qgis_validado": row["join_qgis_validado"],
            "pacote_replicacao_validado": row["pacote_replicacao_validado"],
            "segundo_municipio_testado": row["segundo_municipio_testado"],
            "score_aimm_liberado": row["score_aimm_liberado"],
            "status_modulo": "erro" if errors else "encerrado_com_lacunas_controladas",
            "erros": "|".join(errors),
            "alertas": "|".join(alerts),
            "observacao": row["observacao"],
        }
    ]

    status = [
        {
            "rodada": "4.23",
            "modulo_gis_manaus": "encerrado" if not errors else "erro",
            "baseline_operacional_manaus": row["baseline_gis_validado"],
            "integracao_aimm_preparada": "sim" if not errors else "nao",
            "replicacao_segundo_municipio": row["segundo_municipio_testado"],
            "score_aimm_final": row["score_aimm_liberado"],
            "erros_estruturais": str(len(errors)),
            "alertas": str(len(alerts)),
            "lacunas_registradas": "5",
            "proxima_rodada": "4.24",
            "proxima_rodada_descricao": "documentacao operacional AIMM e fechamento tecnico para retomada",
        }
    ]

    gaps = [
        {
            "gap_id": "GAP_423_SEM_SEGUNDO_MUNICIPIO",
            "tipo": "replicabilidade",
            "criticidade": "media",
            "descricao": "O fluxo GIS foi validado para Manaus, mas ainda não foi testado em segundo município.",
            "acao_recomendada": "Executar rodada futura 4.22-F quando houver necessidade de validar replicação territorial.",
            "bloqueia_modulo_manaus": "nao",
            "bloqueia_generalizacao": "sim",
        },
        {
            "gap_id": "GAP_423_SEM_AREA_CALCULADA",
            "tipo": "geometria",
            "criticidade": "controlada",
            "descricao": "A rodada GIS não calculou área geométrica real em projeção métrica.",
            "acao_recomendada": "Criar rodada espacial específica para cálculo de área com CRS projetado adequado.",
            "bloqueia_modulo_manaus": "nao",
            "bloqueia_generalizacao": "nao",
        },
        {
            "gap_id": "GAP_423_SEM_DENSIDADE",
            "tipo": "indicador",
            "criticidade": "controlada",
            "descricao": "Não foi calculada densidade territorial ou populacional.",
            "acao_recomendada": "Integrar população, área validada e cálculo de densidade em rodada própria.",
            "bloqueia_modulo_manaus": "nao",
            "bloqueia_generalizacao": "nao",
        },
        {
            "gap_id": "GAP_423_SEM_CENTROIDE_BUFFER",
            "tipo": "analise_espacial",
            "criticidade": "controlada",
            "descricao": "Não foram calculados centroide, buffer, distância ou acessibilidade.",
            "acao_recomendada": "Executar rodada GIS espacial com QGIS ou biblioteca GIS adequada.",
            "bloqueia_modulo_manaus": "nao",
            "bloqueia_generalizacao": "nao",
        },
        {
            "gap_id": "GAP_423_SCORE_NAO_LIBERADO",
            "tipo": "aimm",
            "criticidade": "alta",
            "descricao": "O módulo GIS não libera score AIMM final.",
            "acao_recomendada": "Integrar GIS aos demais blocos AIMM antes de qualquer score final.",
            "bloqueia_modulo_manaus": "nao",
            "bloqueia_generalizacao": "sim",
        },
    ]

    aimm_link = [
        {
            "componente_aimm": "territorio",
            "entrada_gis": "municipio_base",
            "valor_validado": row["municipio_base"],
            "codigo_ibge": row["codigo_ibge"],
            "uso_no_aimm": "baseline territorial inicial",
            "status": "utilizavel_com_lacuna_controlada",
        },
        {
            "componente_aimm": "governanca_gis",
            "entrada_gis": "pacote_replicacao_validado",
            "valor_validado": row["pacote_replicacao_validado"],
            "codigo_ibge": row["codigo_ibge"],
            "uso_no_aimm": "procedimento operacional para novos municipios",
            "status": "utilizavel_com_lacuna_de_replicacao",
        },
        {
            "componente_aimm": "score_final",
            "entrada_gis": "score_aimm_liberado",
            "valor_validado": row["score_aimm_liberado"],
            "codigo_ibge": row["codigo_ibge"],
            "uso_no_aimm": "bloqueio metodologico",
            "status": "nao_liberado",
        },
    ]

    evidence = [
        {
            "id_evidencia": "EVD_GIS_MODULE_CLOSURE_4_23",
            "tipo_evidencia": "encerramento_modulo_gis",
            "municipio_base": row["municipio_base"],
            "codigo_ibge": row["codigo_ibge"],
            "status": "encerrado_com_lacunas_controladas" if not errors else "erro",
            "limitacao": "Não houve teste em segundo município e não há score AIMM final liberado.",
        }
    ]

    report = f"""
# Rodada 4.23 — encerramento do módulo GIS Manaus e integração ao AIMM geral

## Resultado

O módulo GIS Manaus foi encerrado operacionalmente.

## Base validada

- Município: `{row["municipio_base"]}`
- Código IBGE: `{row["codigo_ibge"]}`
- Drive GIS: `{row["drive_gis"]}`
- Rodadas validadas: `{row["rodadas_validadas"]}`

## Integração AIMM

O GIS Manaus passa a ser baseline territorial inicial do AIMM.

## Situação da 4.22-F

A aplicação em segundo município não foi realizada nesta fase.

Isso não bloqueia o encerramento do módulo GIS Manaus, mas impede declarar que o fluxo está empiricamente testado para múltiplos municípios.

## Travas

- Não processa geometria.
- Não altera GeoPackage.
- Não calcula área.
- Não calcula densidade.
- Não calcula centroide.
- Não calcula buffer.
- Não libera score AIMM final.

## Conclusão

Status: `encerrado_com_lacunas_controladas`
"""

    log = "\n".join(
        [
            "TESTE GIS_MODULE_CLOSURE_4_23 — Fito+ Amazônia",
            "=" * 86,
            f"Módulo: {row['modulo']}",
            f"Município base: {row['municipio_base']}",
            f"Código IBGE: {row['codigo_ibge']}",
            f"Baseline GIS validado: {row['baseline_gis_validado']}",
            f"Join QGIS validado: {row['join_qgis_validado']}",
            f"Pacote replicação validado: {row['pacote_replicacao_validado']}",
            f"Segundo município testado: {row['segundo_municipio_testado']}",
            f"Score AIMM liberado: {row['score_aimm_liberado']}",
            f"Erros estruturais: {len(errors)}",
            f"Alertas: {len(alerts)}",
            "Lacunas registradas: 5",
            "",
            "Resultado: SUCESSO." if not errors else "Resultado: ERRO.",
            "Módulo GIS Manaus encerrado e preparado para integração ao AIMM geral.",
            "",
            "Trava: não processa geometria, não calcula área, densidade, centroide, buffer nem score AIMM final.",
        ]
    )

    write_csv(OUT_REGISTRY, registry)
    write_csv(OUT_STATUS, status)
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_AIMM_LINK, aimm_link)
    write_csv(OUT_EVIDENCE, evidence)
    write_text(OUT_REPORT, report)
    write_text(OUT_LOG, log)

    for path in [OUT_REGISTRY, OUT_STATUS, OUT_GAPS, OUT_AIMM_LINK, OUT_EVIDENCE, OUT_REPORT, OUT_LOG]:
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {path}")

    print(log)

    if errors:
        raise ValueError(f"Rodada 4.23 contém {len(errors)} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
