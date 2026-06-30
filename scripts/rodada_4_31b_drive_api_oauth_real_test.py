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


BASE = Path("outputs/aimm/rodada_4_31b_drive_api_oauth_real")

FILES = {
    "arquivo_teste": BASE / "AIMM_4_31B_TESTE_DRIVE_API_OAUTH.txt",
    "status": BASE / "STATUS_TESTE_REAL_DRIVE_API_OAUTH_4_31B.csv",
    "metadata": BASE / "METADATA_ARQUIVO_DRIVE_OAUTH_4_31B.csv",
    "registry": Path("data/processed/aimm/aimm_drive_api_oauth_registry_4_31b.csv"),
    "evidence": Path("data/evidence/evidence_aimm_drive_api_oauth_4_31b.csv"),
    "report": Path("outputs/reports/RELATORIO_DRIVE_API_OAUTH_4_31B.md"),
    "log": Path("outputs/logs/teste_drive_api_oauth_4_31b.txt"),
}


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


def mask(value: str) -> str:
    text = str(value or "")
    if len(text) <= 12:
        return "mascarado"
    return f"{text[:6]}...{text[-4:]}"


def main() -> None:
    client_id = require_env("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = require_env("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh_token = require_env("GOOGLE_OAUTH_REFRESH_TOKEN")
    test_folder_id = require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    root_folder_id = require_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")

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

    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    run_id = os.getenv("GITHUB_RUN_ID", "sem_run_id")
    run_number = os.getenv("GITHUB_RUN_NUMBER", "sem_run_number")
    now = datetime.now(timezone.utc).isoformat()

    drive_file_name = f"AIMM_4_31B_TESTE_DRIVE_API_OAUTH_{run_id}.txt"

    local_test_lines = [
        "AIMM 4.31-B - teste real Google Drive API por OAuth",
        f"created_at_utc={now}",
        f"github_run_id={run_id}",
        f"github_run_number={run_number}",
        "autenticacao=oauth_usuario",
        "finalidade=validar_upload_real_e_consulta_metadata",
        "trava=nao_processa_score_aimm_final",
    ]

    write_text(FILES["arquivo_teste"], local_test_lines)

    media = MediaFileUpload(
        str(FILES["arquivo_teste"]),
        mimetype="text/plain",
        resumable=False,
    )

    metadata_in = {
        "name": drive_file_name,
        "parents": [test_folder_id],
        "description": "Teste real controlado da Rodada 4.31-B AIMM via OAuth usuário.",
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
            "rodada": "4.31-B",
            "modulo": "drive_api_oauth_real_test",
            "autenticacao": "oauth_usuario",
            "oauth_client_id_presente": "sim",
            "oauth_client_secret_presente": "sim",
            "oauth_refresh_token_presente": "sim",
            "drive_test_folder_id_presente": "sim",
            "drive_root_folder_id_presente": "sim",
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "download_real": "nao",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "webViewLink": metadata.get("webViewLink", ""),
            "score_aimm_final_liberado": "nao",
            "erros_estruturais": "0",
            "alertas": "1",
            "status": "sucesso",
        }
    ]

    metadata_rows = [
        {
            "rodada": "4.31-B",
            "file_id_mascarado": mask(file_id),
            "name": metadata.get("name", ""),
            "size": metadata.get("size", ""),
            "mimeType": metadata.get("mimeType", ""),
            "parents": ",".join(metadata.get("parents", [])),
            "createdTime": metadata.get("createdTime", ""),
            "modifiedTime": metadata.get("modifiedTime", ""),
            "webViewLink": metadata.get("webViewLink", ""),
        }
    ]

    registry_rows = [
        {
            "rodada": "4.31-B",
            "nome": "drive_api_oauth_real_test",
            "dependencia": "secrets_oauth_usuario",
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "erro_storage_quota_service_account": "nao",
            "erros_estruturais": "0",
            "status": "validado",
            "proxima_rodada": "4.32",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_AIMM_DRIVE_API_OAUTH_REAL_4_31B",
            "tipo": "upload_consulta_drive_api_oauth",
            "descricao": "Arquivo enviado ao Google Drive por OAuth usuário e metadata consultado pela Drive API.",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "status": "gerado",
        }
    ]

    report = [
        "# Relatório da Rodada 4.31-B — Drive API real por OAuth",
        "",
        "## Resultado",
        "",
        "A Rodada 4.31-B validou upload real no Google Drive usando OAuth de usuário.",
        "",
        "## Evidência",
        "",
        f"- Arquivo criado no Drive: `{metadata.get('name', '')}`",
        f"- File ID mascarado: `{mask(file_id)}`",
        f"- Tamanho: `{metadata.get('size', '')}` bytes",
        f"- Pasta teste mascarada: `{mask(test_folder_id)}`",
        f"- Pasta raiz mascarada: `{mask(root_folder_id)}`",
        "",
        "## Travas mantidas",
        "",
        "- Não processa score AIMM final.",
        "- Não processa benchmarks reais.",
        "- Não processa GIS.",
        "- Não executa download real.",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.32 — pipeline mínimo integrado AIMM.",
    ]

    log = [
        "TESTE AIMM_DRIVE_API_OAUTH_REAL_4_31B — Fito+ Amazônia",
        "=" * 86,
        "Autenticacao OAuth usuario: sim",
        "GOOGLE_OAUTH_CLIENT_ID presente: sim",
        "GOOGLE_OAUTH_CLIENT_SECRET presente: sim",
        "GOOGLE_OAUTH_REFRESH_TOKEN presente: sim",
        "GOOGLE_DRIVE_TEST_FOLDER_ID presente: sim",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID presente: sim",
        "Valores de secrets expostos no log: nao",
        f"Arquivo enviado ao Drive: {metadata.get('name', '')}",
        f"File ID mascarado: {mask(file_id)}",
        f"Tamanho bytes Drive: {metadata.get('size', '')}",
        "Upload Drive real: sim",
        "Consulta metadata real: sim",
        "Download real: nao",
        "Score AIMM final liberado: nao",
        "Erros estruturais: 0",
        "Alertas: 1",
        "",
        "Resultado: SUCESSO.",
        "Teste real Drive API por OAuth usuario executado.",
        "",
        "Trava: nao processa GIS, nao processa benchmark, nao faz download real e nao libera score AIMM final.",
    ]

    write_csv(FILES["status"], status_rows)
    write_csv(FILES["metadata"], metadata_rows)
    write_csv(FILES["registry"], registry_rows)
    write_csv(FILES["evidence"], evidence_rows)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log))


if __name__ == "__main__":
    main()
