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

BASE = Path("outputs/aimm/rodada_4_33_operational_controlled_input")

FILES = {
    "pacote_txt": BASE / "AIMM_4_33_OPERACIONAL_CONTROLADO.txt",
    "status": BASE / "STATUS_TESTE_OPERACIONAL_CONTROLADO_AIMM_4_33.csv",
    "entrada_validada": BASE / "ENTRADA_CONTROLADA_VALIDADA_AIMM_4_33.csv",
    "readiness": BASE / "READINESS_OPERACIONAL_CONTROLADO_AIMM_4_33.csv",
    "metadata_drive": BASE / "METADATA_DRIVE_OPERACIONAL_CONTROLADO_AIMM_4_33.csv",
    "checklist": BASE / "CHECKLIST_TESTE_OPERACIONAL_CONTROLADO_AIMM_4_33.csv",
    "registry": Path("data/processed/aimm/aimm_operational_controlled_input_registry_4_33.csv"),
    "evidence": Path("data/evidence/evidence_aimm_operational_controlled_input_4_33.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_OPERACIONAL_CONTROLADO_4_33.md"),
    "log": Path("outputs/logs/teste_aimm_operacional_controlado_4_33.txt"),
}


REQUIRED_FIELDS = [
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Manifesto obrigatorio ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        return [dict(row) for row in reader]


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


def mask(value: str) -> str:
    text = str(value or "")
    if len(text) <= 12:
        return "mascarado"
    return f"{text[:6]}...{text[-4:]}"


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


def validate_input(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    validated: list[dict[str, Any]] = []

    if not rows:
        errors.append("manifesto_sem_linhas")
        return validated, errors

    for idx, row in enumerate(rows, start=1):
        row_errors: list[str] = []

        for field in REQUIRED_FIELDS:
            if not str(row.get(field, "")).strip():
                row_errors.append(f"campo_obrigatorio_ausente:{field}")

        codigo_ibge = str(row.get("codigo_ibge", "")).strip()
        if codigo_ibge != "1302603":
            row_errors.append("codigo_ibge_diferente_do_caso_controlado_manaus_1302603")

        flags = {
            "pacote_gis_validado": norm(row.get("pacote_gis_validado")),
            "pacote_ingestao_validado": norm(row.get("pacote_ingestao_validado")),
            "pacote_benchmark_validado": norm(row.get("pacote_benchmark_validado")),
            "drive_api_oauth_validada": norm(row.get("drive_api_oauth_validada")),
        }

        flags_ok = sum(1 for value in flags.values() if value == "sim")
        readiness = round((flags_ok / len(flags)) * 100, 2)

        status = "ok" if not row_errors and readiness == 100.0 else "alerta"

        validated.append(
            {
                "linha": idx,
                "codigo_ibge": codigo_ibge,
                "nm_mun": row.get("nm_mun", "").strip(),
                "nm_uf": row.get("nm_uf", "").strip(),
                "sigla_uf": row.get("sigla_uf", "").strip(),
                "area_km2": row.get("area_km2", "").strip(),
                "pacote_gis_validado": flags["pacote_gis_validado"],
                "pacote_ingestao_validado": flags["pacote_ingestao_validado"],
                "pacote_benchmark_validado": flags["pacote_benchmark_validado"],
                "drive_api_oauth_validada": flags["drive_api_oauth_validada"],
                "readiness_operacional_controlado_percentual": readiness,
                "score_aimm_final_liberado": "nao",
                "status_linha": status,
                "erros_linha": " | ".join(row_errors),
                "observacao": row.get("observacao", "").strip(),
            }
        )

        errors.extend([f"linha_{idx}:{err}" for err in row_errors])

    return validated, errors


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_id = os.getenv("GITHUB_RUN_ID", "sem_run_id")
    run_number = os.getenv("GITHUB_RUN_NUMBER", "sem_run_number")

    test_folder_id = require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    root_folder_id = require_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    rows = read_csv(MANIFEST)
    validated_rows, validation_errors = validate_input(rows)

    erros_estruturais = len(validation_errors)
    manifest_ok = "sim" if erros_estruturais == 0 else "nao"

    readiness_values = [
        float(row["readiness_operacional_controlado_percentual"])
        for row in validated_rows
    ]

    readiness_medio = round(sum(readiness_values) / len(readiness_values), 2) if readiness_values else 0.0

    pipeline_operacional_controlado = (
        "sim" if manifest_ok == "sim" and readiness_medio == 100.0 else "nao"
    )

    pacote_lines = [
        "AIMM 4.33 - TESTE OPERACIONAL COM PACOTE DE ENTRADA REAL CONTROLADO",
        f"created_at_utc={now}",
        f"github_run_id={run_id}",
        f"github_run_number={run_number}",
        "",
        f"manifesto={MANIFEST}",
        f"manifesto_validado={manifest_ok}",
        f"linhas_validadas={len(validated_rows)}",
        f"readiness_operacional_controlado_percentual={readiness_medio}",
        f"pipeline_operacional_controlado={pipeline_operacional_controlado}",
        "score_aimm_final_liberado=nao",
        "",
        "CASO CONTROLADO:",
    ]

    for row in validated_rows:
        pacote_lines.append(
            f"- {row['codigo_ibge']} | {row['nm_mun']} | {row['sigla_uf']} | readiness={row['readiness_operacional_controlado_percentual']}%"
        )

    pacote_lines.extend(
        [
            "",
            "TRAVAS:",
            "- Nao libera score AIMM final.",
            "- Nao executa benchmark externo real.",
            "- Nao executa nova geometria GIS.",
            "- Nao substitui revisao humana.",
        ]
    )

    write_text(FILES["pacote_txt"], pacote_lines)

    service = oauth_drive_service()

    drive_file_name = f"AIMM_4_33_OPERACIONAL_CONTROLADO_{run_id}.txt"

    media = MediaFileUpload(
        str(FILES["pacote_txt"]),
        mimetype="text/plain",
        resumable=False,
    )

    metadata_in = {
        "name": drive_file_name,
        "parents": [test_folder_id],
        "description": "Rodada 4.33 AIMM — teste operacional com pacote de entrada real controlado.",
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
            "rodada": "4.33",
            "modulo": "operational_controlled_input_test",
            "manifesto_entrada": str(MANIFEST),
            "manifesto_validado": manifest_ok,
            "linhas_entrada": len(rows),
            "linhas_validadas": len(validated_rows),
            "pipeline_operacional_controlado": pipeline_operacional_controlado,
            "readiness_operacional_controlado_percentual": readiness_medio,
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "webViewLink": metadata.get("webViewLink", ""),
            "score_aimm_final_liberado": "nao",
            "erros_estruturais": erros_estruturais,
            "alertas": 1 if pipeline_operacional_controlado == "sim" else 2,
            "resultado": "SUCESSO" if erros_estruturais == 0 else "ERRO",
        }
    ]

    readiness_rows = [
        {
            "rodada": "4.33",
            "codigo_ibge": row["codigo_ibge"],
            "nm_mun": row["nm_mun"],
            "sigla_uf": row["sigla_uf"],
            "readiness_operacional_controlado_percentual": row["readiness_operacional_controlado_percentual"],
            "pacote_gis_validado": row["pacote_gis_validado"],
            "pacote_ingestao_validado": row["pacote_ingestao_validado"],
            "pacote_benchmark_validado": row["pacote_benchmark_validado"],
            "drive_api_oauth_validada": row["drive_api_oauth_validada"],
            "status_linha": row["status_linha"],
            "score_aimm_final_liberado": "nao",
        }
        for row in validated_rows
    ]

    metadata_rows = [
        {
            "rodada": "4.33",
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
            "item": "Manifesto de entrada controlada",
            "status": "ok" if manifest_ok == "sim" else "erro",
            "observacao": f"Arquivo lido: {MANIFEST}",
        },
        {
            "item": "Caso Manaus 1302603",
            "status": "ok" if any(row["codigo_ibge"] == "1302603" for row in validated_rows) else "erro",
            "observacao": "Caso base do teste operacional controlado.",
        },
        {
            "item": "GIS Manaus",
            "status": "ok" if validated_rows and validated_rows[0]["pacote_gis_validado"] == "sim" else "alerta",
            "observacao": "Sinalizado como validado pelo manifesto.",
        },
        {
            "item": "Ingestao 4.28",
            "status": "ok" if validated_rows and validated_rows[0]["pacote_ingestao_validado"] == "sim" else "alerta",
            "observacao": "Sinalizado como validado pelo manifesto.",
        },
        {
            "item": "Benchmark 4.29",
            "status": "ok" if validated_rows and validated_rows[0]["pacote_benchmark_validado"] == "sim" else "alerta",
            "observacao": "Sinalizado como validado pelo manifesto.",
        },
        {
            "item": "Drive API OAuth",
            "status": "ok",
            "observacao": "Upload e consulta metadata executados via OAuth.",
        },
        {
            "item": "Score AIMM final",
            "status": "bloqueado",
            "observacao": "Score final ainda nao liberado nesta rodada.",
        },
    ]

    registry_rows = [
        {
            "rodada": "4.33",
            "nome": "operational_controlled_input_test",
            "municipio_base": "Manaus",
            "codigo_ibge": "1302603",
            "pipeline_operacional_controlado": pipeline_operacional_controlado,
            "readiness_operacional_controlado_percentual": readiness_medio,
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "score_aimm_final_liberado": "nao",
            "erros_estruturais": erros_estruturais,
            "status": "validado" if erros_estruturais == 0 else "erro",
            "proxima_rodada": "4.34",
            "proxima_rodada_descricao": "calculo preliminar controlado sem liberacao final",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_AIMM_OPERACIONAL_CONTROLADO_4_33",
            "tipo": "teste_operacional_controlado",
            "descricao": "Manifesto operacional controlado lido, validado e registrado com upload real no Drive.",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "status": "gerado",
            "limitacao": "nao libera score final e nao executa benchmark externo real",
        }
    ]

    report_lines = [
        "# Relatório da Rodada 4.33 — teste operacional com pacote de entrada real controlado",
        "",
        "## Resultado",
        "",
        "A Rodada 4.33 validou a execução operacional controlada da calculadora AIMM.",
        "",
        f"- Manifesto lido: `{MANIFEST}`",
        f"- Linhas validadas: `{len(validated_rows)}`",
        f"- Readiness operacional controlado: `{readiness_medio}%`",
        f"- Pipeline operacional controlado: `{pipeline_operacional_controlado}`",
        f"- Upload Drive real: `sim`",
        f"- Consulta metadata real: `sim`",
        f"- Arquivo criado no Drive: `{metadata.get('name', '')}`",
        f"- File ID mascarado: `{mask(file_id)}`",
        "",
        "## Travas mantidas",
        "",
        "- Não libera score AIMM final.",
        "- Não executa benchmark externo real.",
        "- Não executa nova geometria GIS.",
        "- Não substitui revisão humana.",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.34 — cálculo preliminar controlado sem liberação final.",
    ]

    log_lines = [
        "TESTE AIMM_OPERATIONAL_CONTROLLED_INPUT_4_33 — Fito+ Amazônia",
        "=" * 86,
        "Manifesto de entrada controlada detectado: sim",
        f"Manifesto: {MANIFEST}",
        f"Linhas de entrada: {len(rows)}",
        f"Linhas validadas: {len(validated_rows)}",
        f"Manifesto validado: {manifest_ok}",
        f"Pipeline operacional controlado: {pipeline_operacional_controlado}",
        f"Readiness operacional controlado: {readiness_medio}%",
        "Upload Drive real: sim",
        "Consulta metadata real: sim",
        f"Arquivo enviado ao Drive: {metadata.get('name', '')}",
        f"File ID mascarado: {mask(file_id)}",
        "Score AIMM final liberado: nao",
        f"Erros estruturais: {erros_estruturais}",
        f"Alertas: {1 if pipeline_operacional_controlado == 'sim' else 2}",
        "",
        "Resultado: SUCESSO." if erros_estruturais == 0 else "Resultado: ERRO.",
        "",
        "Trava: nao libera score final, nao substitui revisao humana, nao executa benchmark externo real e nao executa nova geometria GIS.",
    ]

    write_csv(FILES["status"], status_rows)
    write_csv(FILES["entrada_validada"], validated_rows)
    write_csv(FILES["readiness"], readiness_rows)
    write_csv(FILES["metadata_drive"], metadata_rows)
    write_csv(FILES["checklist"], checklist_rows)
    write_csv(FILES["registry"], registry_rows)
    write_csv(FILES["evidence"], evidence_rows)
    write_text(FILES["report"], report_lines)
    write_text(FILES["log"], log_lines)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    if erros_estruturais:
        raise RuntimeError("Erros estruturais encontrados: " + " | ".join(validation_errors))

    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
