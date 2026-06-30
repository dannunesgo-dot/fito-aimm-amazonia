# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_31_drive_api_real")

FILES = {
    "arquivo_teste": BASE / "AIMM_4_31_TESTE_DRIVE_API.txt",
    "status": BASE / "STATUS_TESTE_REAL_DRIVE_API_4_31.csv",
    "metadata": BASE / "METADATA_ARQUIVO_DRIVE_4_31.csv",
    "checklist": BASE / "CHECKLIST_POS_TESTE_DRIVE_API_4_31.csv",
    "registry": Path("data/processed/aimm/aimm_drive_api_real_registry_4_31.csv"),
    "evidence": Path("data/evidence/evidence_aimm_drive_api_real_4_31.csv"),
    "report": Path("outputs/reports/RELATORIO_DRIVE_API_REAL_4_31.md"),
    "log": Path("outputs/logs/teste_drive_api_real_4_31.txt"),
}


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


def mask_id(value: str) -> str:
    text = str(value or "")
    if len(text) <= 12:
        return "mascarado"
    return f"{text[:6]}...{text[-4:]}"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Secret/variavel obrigatorio ausente: {name}")
    return value


def load_service_account_json() -> tuple[dict[str, Any], Path]:
    raw = require_env("GDRIVE_SERVICE_ACCOUNT_JSON")

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GDRIVE_SERVICE_ACCOUNT_JSON nao e JSON valido.") from exc

    required = {"type", "project_id", "private_key", "client_email", "token_uri"}
    missing = sorted(required - set(info.keys()))
    if missing:
        raise RuntimeError("GDRIVE_SERVICE_ACCOUNT_JSON incompleto: " + ",".join(missing))

    if info.get("type") != "service_account":
        raise RuntimeError("GDRIVE_SERVICE_ACCOUNT_JSON nao e credencial service_account.")

    key_path = Path(os.getenv("RUNNER_TEMP", "/tmp")) / "aimm_gdrive_service_account_4_31.json"
    key_path.write_text(json.dumps(info), encoding="utf-8")

    return info, key_path


def main() -> None:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    test_folder_id = require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    root_folder_id = require_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    info, key_path = load_service_account_json()

    service_account_email = info.get("client_email", "")
    run_id = os.getenv("GITHUB_RUN_ID", "sem_run_id")
    run_number = os.getenv("GITHUB_RUN_NUMBER", "sem_run_number")
    created_at = datetime.now(timezone.utc).isoformat()

    scopes = ["https://www.googleapis.com/auth/drive"]
    credentials = service_account.Credentials.from_service_account_file(
        str(key_path),
        scopes=scopes,
    )

    service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    test_file_name = f"AIMM_4_31_TESTE_DRIVE_API_{run_id}.txt"

    test_lines = [
        "AIMM 4.31 - teste real controlado Google Drive API",
        f"created_at_utc={created_at}",
        f"github_run_id={run_id}",
        f"github_run_number={run_number}",
        "finalidade=validar_upload_e_consulta_metadata_sem_score_final",
        "trava=nao_processa_score_aimm_final",
    ]

    write_text(FILES["arquivo_teste"], test_lines)

    file_metadata = {
        "name": test_file_name,
        "parents": [test_folder_id],
        "description": "Teste real controlado da Rodada 4.31 AIMM. Pode ser mantido como evidencia.",
    }

    media = MediaFileUpload(
        str(FILES["arquivo_teste"]),
        mimetype="text/plain",
        resumable=False,
    )

    created = (
        service.files()
        .create(
            body=file_metadata,
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
            "rodada": "4.31",
            "modulo": "drive_api_real_test",
            "status": "sucesso",
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "download_real": "nao",
            "drive_test_folder_id_presente": "sim",
            "drive_root_folder_id_presente": "sim",
            "service_account_json_presente": "sim",
            "service_account_email": service_account_email,
            "file_id_mascarado": mask_id(file_id),
            "nome_arquivo_drive": metadata.get("name", ""),
            "tamanho_bytes": metadata.get("size", ""),
            "webViewLink": metadata.get("webViewLink", ""),
            "score_aimm_final_liberado": "nao",
            "erros_estruturais": "0",
            "alertas": "1",
        }
    ]

    metadata_rows = [
        {
            "rodada": "4.31",
            "file_id": file_id,
            "file_id_mascarado": mask_id(file_id),
            "name": metadata.get("name", ""),
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
            "item": "Secret GDRIVE_SERVICE_ACCOUNT_JSON",
            "status": "ok",
            "observacao": "JSON carregado sem expor private_key no log.",
        },
        {
            "item": "Secret GOOGLE_DRIVE_TEST_FOLDER_ID",
            "status": "ok",
            "observacao": "ID de pasta teste recebido pelo workflow.",
        },
        {
            "item": "Secret GOOGLE_DRIVE_ROOT_FOLDER_ID",
            "status": "ok",
            "observacao": "ID de pasta raiz recebido pelo workflow.",
        },
        {
            "item": "Upload real no Drive",
            "status": "ok",
            "observacao": "Arquivo TXT criado na pasta teste configurada.",
        },
        {
            "item": "Consulta metadata",
            "status": "ok",
            "observacao": "Metadata recuperado por fileId.",
        },
        {
            "item": "Score AIMM final",
            "status": "bloqueado",
            "observacao": "Rodada 4.31 testa API Drive, nao calcula score final.",
        },
    ]

    registry_rows = [
        {
            "rodada": "4.31",
            "nome": "drive_api_real_test",
            "autenticacao": "service_account_json",
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "download_real": "nao",
            "file_id_mascarado": mask_id(file_id),
            "erros_estruturais": "0",
            "alertas": "1",
            "status": "validado",
            "proxima_rodada": "4.32",
            "proxima_rodada_descricao": "pipeline minimo integrado AIMM",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_AIMM_DRIVE_API_REAL_4_31",
            "tipo": "upload_consulta_drive_api",
            "descricao": "Arquivo pequeno enviado ao Google Drive e metadata consultado via Drive API.",
            "file_id_mascarado": mask_id(file_id),
            "nome_arquivo_drive": metadata.get("name", ""),
            "status": "gerado",
            "limitacao": "nao executa download, nao processa benchmark real, nao processa GIS e nao libera score final",
        }
    ]

    report = [
        "# Relatório da Rodada 4.31 — teste real Google Drive API",
        "",
        "## Resultado",
        "",
        "A Rodada 4.31 executou upload real de arquivo pequeno no Google Drive e consulta real de metadata pela Drive API.",
        "",
        "## Evidência principal",
        "",
        f"- Arquivo criado no Drive: `{metadata.get('name', '')}`",
        f"- File ID mascarado: `{mask_id(file_id)}`",
        f"- Tamanho informado pelo Drive: `{metadata.get('size', '')}` bytes",
        f"- Service Account: `{service_account_email}`",
        f"- Pasta teste ID mascarado: `{mask_id(test_folder_id)}`",
        f"- Pasta raiz ID mascarado: `{mask_id(root_folder_id)}`",
        "",
        "## Travas",
        "",
        "- Não executa download real.",
        "- Não processa GIS.",
        "- Não processa benchmarks.",
        "- Não libera score AIMM final.",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.32 — pipeline mínimo integrado AIMM.",
    ]

    log = [
        "TESTE AIMM_DRIVE_API_REAL_4_31 — Fito+ Amazônia",
        "=" * 86,
        "Autenticacao: service_account_json",
        f"Service account: {service_account_email}",
        "GDRIVE_SERVICE_ACCOUNT_JSON exposto no log: nao",
        "GOOGLE_DRIVE_TEST_FOLDER_ID presente: sim",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID presente: sim",
        f"Arquivo enviado ao Drive: {metadata.get('name', '')}",
        f"File ID mascarado: {mask_id(file_id)}",
        f"Tamanho bytes Drive: {metadata.get('size', '')}",
        "Upload Drive real: sim",
        "Consulta metadata real: sim",
        "Download real: nao",
        "Score AIMM final liberado: nao",
        "Erros estruturais: 0",
        "Alertas: 1",
        "",
        "Resultado: SUCESSO.",
        "Teste real controlado Drive API executado.",
        "",
        "Trava: nao processa GIS, nao processa benchmark, nao faz download real e nao libera score AIMM final.",
    ]

    write_csv(FILES["status"], status_rows)
    write_csv(FILES["metadata"], metadata_rows)
    write_csv(FILES["checklist"], checklist_rows)
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
