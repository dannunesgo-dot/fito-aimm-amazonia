from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DRIVE_FIELDS = "id,name,size,mimeType,parents,createdTime,modifiedTime,webViewLink"


@dataclass(frozen=True)
class DriveUploadResult:
    file_id: str
    metadata: dict[str, Any]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Segredo/variável obrigatória ausente: {name}")
    return value


def mask_identifier(value: str) -> str:
    text = str(value or "")
    if len(text) <= 12:
        return "mascarado"
    return f"{text[:6]}...{text[-4:]}"


def load_service_account_info_from_env(name: str = "GDRIVE_SERVICE_ACCOUNT_JSON") -> dict[str, Any]:
    raw = require_env(name)

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} não é JSON válido.") from exc

    required = {"type", "project_id", "private_key", "client_email", "token_uri"}
    missing = sorted(required - set(info.keys()))
    if missing:
        raise RuntimeError(f"{name} incompleto: {', '.join(missing)}")
    if info.get("type") != "service_account":
        raise RuntimeError(f"{name} não é uma credencial service_account.")

    return info


def write_service_account_key_file(info: dict[str, Any], suffix: str = "drive_sync") -> Path:
    key_path = Path(os.getenv("RUNNER_TEMP", "/tmp")) / f"aimm_{suffix}_service_account.json"
    key_path.write_text(json.dumps(info), encoding="utf-8")
    return key_path


def build_service_account_drive_service(
    info: dict[str, Any] | None = None,
    scopes: list[str] | None = None,
):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    service_account_info = info or load_service_account_info_from_env()
    scopes = scopes or ["https://www.googleapis.com/auth/drive"]
    key_path = write_service_account_key_file(service_account_info)
    credentials = service_account.Credentials.from_service_account_file(
        str(key_path),
        scopes=scopes,
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def build_oauth_drive_service(
    scopes: list[str] | None = None,
    client_id_env: str = "GOOGLE_OAUTH_CLIENT_ID",
    client_secret_env: str = "GOOGLE_OAUTH_CLIENT_SECRET",
    refresh_token_env: str = "GOOGLE_OAUTH_REFRESH_TOKEN",
):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
    credentials = Credentials(
        token=None,
        refresh_token=require_env(refresh_token_env),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=require_env(client_id_env),
        client_secret=require_env(client_secret_env),
        scopes=scopes,
    )
    credentials.refresh(Request())
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def fetch_file_metadata(service, file_id: str, fields: str = DEFAULT_DRIVE_FIELDS) -> dict[str, Any]:
    return (
        service.files()
        .get(fileId=file_id, fields=fields, supportsAllDrives=True)
        .execute()
    )


def upload_file(
    service,
    local_path: Path,
    parent_folder_id: str,
    file_name: str,
    description: str,
    mimetype: str,
    fields: str = DEFAULT_DRIVE_FIELDS,
) -> DriveUploadResult:
    from googleapiclient.http import MediaFileUpload

    created = (
        service.files()
        .create(
            body={
                "name": file_name,
                "parents": [parent_folder_id],
                "description": description,
            },
            media_body=MediaFileUpload(str(local_path), mimetype=mimetype, resumable=False),
            fields=fields,
            supportsAllDrives=True,
        )
        .execute()
    )
    file_id = str(created["id"])
    return DriveUploadResult(file_id=file_id, metadata=fetch_file_metadata(service, file_id, fields=fields))
