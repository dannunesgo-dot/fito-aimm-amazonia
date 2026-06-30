# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


MANIFEST = Path("data/manual/aimm/aimm_operational_input_manifest_4_33.csv")
WEIGHTS = Path("data/manual/aimm/aimm_preliminary_score_weights_4_34.csv")
CONFIG = Path("data/manual/aimm/aimm_executive_report_config_4_35.csv")

BASE = Path("outputs/aimm/rodada_4_35_end_to_end_controlled")

FILES = {
    "executive_report_base": BASE / "RELATORIO_EXECUTIVO_AIMM_4_35.md",
    "executive_report_outputs": Path("outputs/reports/RELATORIO_EXECUTIVO_AIMM_4_35.md"),
    "status": BASE / "STATUS_TESTE_PONTA_A_PONTA_AIMM_4_35.csv",
    "score": BASE / "SCORE_EXECUTIVO_CONTROLADO_AIMM_4_35.csv",
    "componentes": BASE / "COMPONENTES_EXECUTIVOS_AIMM_4_35.csv",
    "metadata_drive": BASE / "METADATA_DRIVE_RELATORIO_EXECUTIVO_AIMM_4_35.csv",
    "checklist": BASE / "CHECKLIST_TESTE_PONTA_A_PONTA_AIMM_4_35.csv",
    "registry": Path("data/processed/aimm/aimm_end_to_end_controlled_registry_4_35.csv"),
    "evidence": Path("data/evidence/evidence_aimm_end_to_end_controlled_4_35.csv"),
    "log": Path("outputs/logs/teste_aimm_ponta_a_ponta_controlado_4_35.txt"),
}


REQUIRED_MANIFEST_FIELDS = [
    "codigo_ibge",
    "nm_mun",
    "nm_uf",
    "sigla_uf",
    "area_km2",
    "pacote_gis_validado",
    "pacote_ingestao_validado",
    "pacote_benchmark_validado",
    "drive_api_oauth_validada",
]

REQUIRED_WEIGHT_FIELDS = [
    "dimensao",
    "variavel_manifesto",
    "peso",
    "criterio_ok",
    "descricao",
]

REQUIRED_CONFIG_FIELDS = [
    "chave",
    "valor",
    "descricao",
]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Secret obrigatorio ausente: {name}")
    return value


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        rows = [{"status": "sem_linhas"}]

    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    normalized = [{key: row.get(key, "") for key in fieldnames} for row in rows]

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path, required_fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatorio ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        rows = [dict(row) for row in reader]

    if not rows:
        raise RuntimeError(f"Arquivo sem linhas: {path}")

    header = set(rows[0].keys())
    missing = [field for field in required_fields if field not in header]
    if missing:
        raise RuntimeError(f"Campos ausentes em {path}: {', '.join(missing)}")

    return rows


def config_dict(rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        str(row.get("chave", "")).strip(): str(row.get("valor", "")).strip()
        for row in rows
        if str(row.get("chave", "")).strip()
    }


def norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    replacements = {
        "s": "sim",
        "yes": "sim",
        "true": "sim",
        "1": "sim",
        "n": "nao",
        "no": "nao",
        "false": "nao",
        "0": "nao",
    }
    return replacements.get(text, text)


def parse_float(value: Any, label: str) -> float:
    text = str(value or "").strip().replace(",", ".")
    try:
        number = float(text)
    except ValueError as exc:
        raise RuntimeError(f"Valor numerico invalido em {label}: {value}") from exc
    return number


def mask(value: str) -> str:
    text = str(value or "")
    if len(text) <= 12:
        return "mascarado"
    return f"{text[:6]}...{text[-4:]}"


def has_minimum_metadata(row: dict[str, str]) -> bool:
    for field in ["codigo_ibge", "nm_mun", "nm_uf", "sigla_uf", "area_km2"]:
        if not str(row.get(field, "")).strip():
            return False
    return str(row.get("codigo_ibge", "")).strip() == "1302603"


def oauth_drive_service():
    client_id = require_env("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = require_env("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh_token = require_env("GOOGLE_OAUTH_REFRESH_TOKEN")

    scopes = ["https://www.googleapis.com/auth/drive.file"]

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )

    creds.refresh(Request())

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def score_dimension(row: dict[str, str], weight_row: dict[str, str]) -> dict[str, Any]:
    variavel = weight_row["variavel_manifesto"].strip()
    criterio_ok = norm(weight_row["criterio_ok"])
    peso = parse_float(weight_row["peso"], f"peso:{weight_row['dimensao']}")

    if variavel == "metadados_minimos":
        ok = has_minimum_metadata(row)
        valor_detectado = "sim" if ok else "nao"
    elif variavel == "travas_operacionais":
        ok = True
        valor_detectado = "sim"
    else:
        valor_detectado = norm(row.get(variavel, ""))
        ok = valor_detectado == criterio_ok

    pontos = peso if ok else 0.0

    return {
        "rodada": "4.35",
        "dimensao": weight_row["dimensao"],
        "variavel_manifesto": variavel,
        "valor_detectado": valor_detectado,
        "criterio_ok": criterio_ok,
        "peso": peso,
        "pontos_obtidos": pontos,
        "status": "ok" if ok else "alerta",
        "descricao": weight_row["descricao"],
    }


def classify_score(score: float, limiar_apto: float, limiar_alerta: float) -> str:
    if score >= limiar_apto:
        return "piloto_controlado_apto_para_demonstracao"
    if score >= limiar_alerta:
        return "piloto_controlado_com_alertas"
    return "piloto_controlado_nao_apto"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_id = os.getenv("GITHUB_RUN_ID", "sem_run_id")
    run_number = os.getenv("GITHUB_RUN_NUMBER", "sem_run_number")

    test_folder_id = require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    root_folder_id = require_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    manifest_rows = read_csv(MANIFEST, REQUIRED_MANIFEST_FIELDS)
    weight_rows = read_csv(WEIGHTS, REQUIRED_WEIGHT_FIELDS)
    cfg_rows = read_csv(CONFIG, REQUIRED_CONFIG_FIELDS)
    cfg = config_dict(cfg_rows)

    if len(manifest_rows) != 1:
        raise RuntimeError("A Rodada 4.35 espera exatamente 1 linha no manifesto controlado.")

    row = manifest_rows[0]

    municipio_base = cfg.get("municipio_base", "Manaus")
    codigo_ibge_base = cfg.get("codigo_ibge_base", "1302603")
    titulo_relatorio = cfg.get("titulo_relatorio", "Relatório executivo AIMM 4.35")
    publico_alvo = cfg.get("publico_alvo", "equipe_gestora")
    limiar_apto = parse_float(cfg.get("limiar_apto", "90"), "limiar_apto")
    limiar_alerta = parse_float(cfg.get("limiar_alerta", "70"), "limiar_alerta")
    score_final_liberado = norm(cfg.get("score_final_liberado", "nao"))

    if score_final_liberado != "nao":
        raise RuntimeError("Trava violada: score_final_liberado deve permanecer 'nao' na Rodada 4.35.")

    if str(row.get("codigo_ibge", "")).strip() != codigo_ibge_base:
        raise RuntimeError("Codigo IBGE do manifesto nao corresponde ao caso controlado.")

    if str(row.get("nm_mun", "")).strip().lower() != municipio_base.lower():
        raise RuntimeError("Municipio do manifesto nao corresponde ao caso controlado.")

    total_peso = sum(parse_float(item["peso"], f"peso:{item['dimensao']}") for item in weight_rows)
    if round(total_peso, 6) != 100.0:
        raise RuntimeError(f"Soma dos pesos deve ser 100. Soma detectada: {total_peso}")

    componentes_rows = [score_dimension(row, item) for item in weight_rows]

    score_total = round(sum(float(item["pontos_obtidos"]) for item in componentes_rows), 2)
    alertas_componentes = sum(1 for item in componentes_rows if item["status"] != "ok")
    classificacao = classify_score(score_total, limiar_apto, limiar_alerta)

    demonstravel = "sim" if score_total >= limiar_apto and alertas_componentes == 0 else "nao"

    executive_lines = [
        f"# {titulo_relatorio}",
        "",
        "## 1. Resultado executivo",
        "",
        f"- Município testado: **{row.get('nm_mun', '')} / {row.get('sigla_uf', '')}**",
        f"- Código IBGE: **{row.get('codigo_ibge', '')}**",
        f"- Área territorial registrada: **{row.get('area_km2', '')} km²**",
        f"- Score preliminar controlado: **{score_total} / 100**",
        f"- Classificação preliminar: **{classificacao}**",
        f"- Piloto demonstrável: **{demonstravel}**",
        f"- Score AIMM final liberado: **{score_final_liberado}**",
        "",
        "## 2. Interpretação",
        "",
        "A rodada executou um teste ponta a ponta controlado da calculadora AIMM: entrada controlada, validação de campos, cálculo preliminar, geração de relatório executivo e upload real no Google Drive por OAuth.",
        "",
        "## 3. Componentes avaliados",
        "",
    ]

    for item in componentes_rows:
        executive_lines.append(
            f"- **{item['dimensao']}**: {item['pontos_obtidos']} / {item['peso']} pontos — status: `{item['status']}`."
        )

    executive_lines.extend(
        [
            "",
            "## 4. Evidência operacional",
            "",
            "- Manifesto de entrada controlada lido.",
            "- Pesos de cálculo preliminar aplicados.",
            "- Relatório executivo gerado.",
            "- Upload real no Google Drive executado.",
            "- Metadata do arquivo criado consultado pela Drive API.",
            "",
            "## 5. Travas mantidas",
            "",
            "- O score AIMM final **não** está liberado.",
            "- O resultado ainda exige revisão humana.",
            "- Benchmark externo real ainda não foi executado.",
            "- Nova geometria GIS não foi processada nesta rodada.",
            "",
            "## 6. Uso pela equipe",
            "",
            "Este relatório pode ser compartilhado como demonstração controlada do funcionamento inicial da calculadora AIMM. Ele ainda não deve ser usado como decisão final de política pública ou priorização definitiva.",
            "",
            "## 7. Próxima rodada",
            "",
            "Rodada 4.36 — pacote congelado de demonstração, uso e retomada.",
        ]
    )

    write_text(FILES["executive_report_base"], executive_lines)
    write_text(FILES["executive_report_outputs"], executive_lines)

    service = oauth_drive_service()

    drive_file_name = f"AIMM_4_35_RELATORIO_EXECUTIVO_CONTROLADO_{run_id}.md"

    media = MediaFileUpload(
        str(FILES["executive_report_base"]),
        mimetype="text/markdown",
        resumable=False,
    )

    metadata_in = {
        "name": drive_file_name,
        "parents": [test_folder_id],
        "description": "Rodada 4.35 AIMM — teste ponta a ponta controlado com relatorio executivo.",
    }

    created = (
        service.files()
        .create(
            body=metadata_in,
            media_body=media,
            fields="id,name,size,mimeType,parents,createdTime,modifiedTime,webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )

    file_id = created["id"]

    metadata = (
        service.files()
        .get(
            fileId=file_id,
            fields="id,name,size,mimeType,parents,createdTime,modifiedTime,webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )

    status_rows = [
        {
            "rodada": "4.35",
            "modulo": "end_to_end_controlled_executive_report",
            "entrada_controlada_lida": "sim",
            "calculo_preliminar_executado": "sim",
            "relatorio_executivo_gerado": "sim",
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "piloto_demonstravel": demonstravel,
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "webViewLink": metadata.get("webViewLink", ""),
            "score_aimm_final_liberado": score_final_liberado,
            "erros_estruturais": 0,
            "alertas": alertas_componentes + 1,
            "resultado": "SUCESSO",
        }
    ]

    score_rows = [
        {
            "rodada": "4.35",
            "codigo_ibge": row.get("codigo_ibge", ""),
            "nm_mun": row.get("nm_mun", ""),
            "nm_uf": row.get("nm_uf", ""),
            "sigla_uf": row.get("sigla_uf", ""),
            "area_km2": row.get("area_km2", ""),
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "piloto_demonstravel": demonstravel,
            "score_aimm_final_liberado": score_final_liberado,
            "limiar_apto": limiar_apto,
            "limiar_alerta": limiar_alerta,
            "publico_alvo": publico_alvo,
            "status": "sucesso",
        }
    ]

    metadata_rows = [
        {
            "rodada": "4.35",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "size": metadata.get("size", ""),
            "mimeType": metadata.get("mimeType", ""),
            "parents": ",".join(metadata.get("parents", [])),
            "createdTime": metadata.get("createdTime", ""),
            "modifiedTime": metadata.get("modifiedTime", ""),
            "webViewLink": metadata.get("webViewLink", ""),
        }
    ]

    checklist_rows = [
        {
            "item": "Entrada controlada",
            "status": "ok",
            "observacao": f"Manifesto lido: {MANIFEST}",
        },
        {
            "item": "Pesos preliminares",
            "status": "ok",
            "observacao": f"Pesos lidos: {WEIGHTS}; soma={total_peso}",
        },
        {
            "item": "Calculo preliminar",
            "status": "ok",
            "observacao": f"Score={score_total}; classificacao={classificacao}",
        },
        {
            "item": "Relatorio executivo",
            "status": "ok",
            "observacao": "Relatorio markdown gerado.",
        },
        {
            "item": "Upload Drive",
            "status": "ok",
            "observacao": "Relatorio executivo enviado ao Drive por OAuth.",
        },
        {
            "item": "Score final",
            "status": "bloqueado",
            "observacao": "Score final nao liberado nesta rodada.",
        },
    ]

    registry_rows = [
        {
            "rodada": "4.35",
            "nome": "end_to_end_controlled_executive_report",
            "municipio_base": row.get("nm_mun", ""),
            "codigo_ibge": row.get("codigo_ibge", ""),
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "piloto_demonstravel": demonstravel,
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "score_aimm_final_liberado": score_final_liberado,
            "erros_estruturais": 0,
            "status": "validado",
            "proxima_rodada": "4.36",
            "proxima_rodada_descricao": "pacote congelado de demonstracao uso e retomada",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_AIMM_END_TO_END_4_35",
            "tipo": "teste_ponta_a_ponta_controlado",
            "descricao": "Entrada controlada, calculo preliminar, relatorio executivo e upload real no Drive executados.",
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "status": "gerado",
            "limitacao": "nao libera score final e nao executa benchmark externo real",
        }
    ]

    log_lines = [
        "TESTE AIMM_END_TO_END_CONTROLLED_EXECUTIVE_REPORT_4_35 — Fito+ Amazônia",
        "=" * 86,
        "Entrada controlada lida: sim",
        "Pesos preliminares lidos: sim",
        f"Soma dos pesos: {total_peso}",
        "Calculo preliminar executado: sim",
        "Relatorio executivo gerado: sim",
        "Upload Drive real: sim",
        "Consulta metadata real: sim",
        f"Municipio: {row.get('nm_mun', '')}",
        f"Codigo IBGE: {row.get('codigo_ibge', '')}",
        f"Score preliminar controlado: {score_total}",
        f"Classificacao preliminar: {classificacao}",
        f"Piloto demonstravel: {demonstravel}",
        f"Arquivo enviado ao Drive: {metadata.get('name', '')}",
        f"File ID mascarado: {mask(file_id)}",
        "Score AIMM final liberado: nao",
        "Erros estruturais: 0",
        f"Alertas: {alertas_componentes + 1}",
        "",
        "Resultado: SUCESSO.",
        "Teste ponta a ponta controlado com relatorio executivo executado.",
        "",
        "Trava: nao libera score final, nao substitui revisao humana, nao executa benchmark externo real e nao executa nova geometria GIS.",
    ]

    write_csv(FILES["status"], status_rows)
    write_csv(FILES["score"], score_rows)
    write_csv(FILES["componentes"], componentes_rows)
    write_csv(FILES["metadata_drive"], metadata_rows)
    write_csv(FILES["checklist"], checklist_rows)
    write_csv(FILES["registry"], registry_rows)
    write_csv(FILES["evidence"], evidence_rows)
    write_text(FILES["log"], log_lines)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
