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

BASE = Path("outputs/aimm/rodada_4_34_preliminary_controlled_score")

FILES = {
    "pacote_txt": BASE / "AIMM_4_34_SCORE_PRELIMINAR_CONTROLADO.txt",
    "status": BASE / "STATUS_CALCULO_PRELIMINAR_CONTROLADO_AIMM_4_34.csv",
    "score": BASE / "SCORE_PRELIMINAR_CONTROLADO_AIMM_4_34.csv",
    "componentes": BASE / "COMPONENTES_SCORE_AIMM_4_34.csv",
    "pesos": BASE / "PESOS_APLICADOS_AIMM_4_34.csv",
    "metadata_drive": BASE / "METADATA_DRIVE_SCORE_PRELIMINAR_AIMM_4_34.csv",
    "checklist": BASE / "CHECKLIST_CALCULO_PRELIMINAR_AIMM_4_34.csv",
    "registry": Path("data/processed/aimm/aimm_preliminary_controlled_score_registry_4_34.csv"),
    "evidence": Path("data/evidence/evidence_aimm_preliminary_controlled_score_4_34.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_SCORE_PRELIMINAR_CONTROLADO_4_34.md"),
    "log": Path("outputs/logs/teste_aimm_score_preliminar_controlado_4_34.txt"),
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


def parse_weight(value: str) -> float:
    text = str(value or "").strip().replace(",", ".")
    try:
        number = float(text)
    except ValueError as exc:
        raise RuntimeError(f"Peso invalido: {value}") from exc

    if number < 0:
        raise RuntimeError(f"Peso negativo invalido: {value}")

    return number


def score_dimension(row: dict[str, str], weight_row: dict[str, str]) -> tuple[str, float, float, str]:
    variavel = weight_row["variavel_manifesto"].strip()
    criterio_ok = norm(weight_row["criterio_ok"])
    peso = parse_weight(weight_row["peso"])

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
    status = "ok" if ok else "alerta"

    return valor_detectado, peso, pontos, status


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_id = os.getenv("GITHUB_RUN_ID", "sem_run_id")
    run_number = os.getenv("GITHUB_RUN_NUMBER", "sem_run_number")

    test_folder_id = require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    root_folder_id = require_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    manifest_rows = read_csv(MANIFEST, REQUIRED_MANIFEST_FIELDS)
    weight_rows = read_csv(WEIGHTS, REQUIRED_WEIGHT_FIELDS)

    if len(manifest_rows) != 1:
        raise RuntimeError("A Rodada 4.34 espera exatamente 1 linha no manifesto controlado.")

    row = manifest_rows[0]

    total_peso = sum(parse_weight(item["peso"]) for item in weight_rows)
    if round(total_peso, 6) != 100.0:
        raise RuntimeError(f"Soma dos pesos deve ser 100. Soma detectada: {total_peso}")

    componentes_rows: list[dict[str, Any]] = []
    score_total = 0.0
    alertas_componentes = 0

    for item in weight_rows:
        valor_detectado, peso, pontos, status = score_dimension(row, item)
        score_total += pontos
        if status != "ok":
            alertas_componentes += 1

        componentes_rows.append(
            {
                "rodada": "4.34",
                "codigo_ibge": row.get("codigo_ibge", ""),
                "municipio": row.get("nm_mun", ""),
                "dimensao": item["dimensao"],
                "variavel_manifesto": item["variavel_manifesto"],
                "valor_detectado": valor_detectado,
                "criterio_ok": norm(item["criterio_ok"]),
                "peso": peso,
                "pontos_obtidos": pontos,
                "status": status,
                "descricao": item["descricao"],
            }
        )

    score_total = round(score_total, 2)

    if score_total >= 90:
        classificacao = "piloto_controlado_apto"
    elif score_total >= 70:
        classificacao = "piloto_controlado_com_alertas"
    else:
        classificacao = "piloto_controlado_nao_apto"

    score_final_liberado = "nao"

    pacote_lines = [
        "AIMM 4.34 - CALCULO PRELIMINAR CONTROLADO",
        f"created_at_utc={now}",
        f"github_run_id={run_id}",
        f"github_run_number={run_number}",
        "",
        f"codigo_ibge={row.get('codigo_ibge', '')}",
        f"municipio={row.get('nm_mun', '')}",
        f"uf={row.get('sigla_uf', '')}",
        f"area_km2={row.get('area_km2', '')}",
        "",
        f"score_preliminar_controlado={score_total}",
        f"classificacao_preliminar={classificacao}",
        f"score_aimm_final_liberado={score_final_liberado}",
        "",
        "COMPONENTES:",
    ]

    for comp in componentes_rows:
        pacote_lines.append(
            f"- {comp['dimensao']}: {comp['pontos_obtidos']}/{comp['peso']} | {comp['status']}"
        )

    pacote_lines.extend(
        [
            "",
            "TRAVAS:",
            "- Este score e preliminar.",
            "- Nao libera decisao final automatica.",
            "- Nao substitui revisao humana.",
            "- Nao executa benchmark externo real.",
            "- Nao executa nova geometria GIS.",
        ]
    )

    write_text(FILES["pacote_txt"], pacote_lines)

    service = oauth_drive_service()

    drive_file_name = f"AIMM_4_34_SCORE_PRELIMINAR_CONTROLADO_{run_id}.txt"

    media = MediaFileUpload(
        str(FILES["pacote_txt"]),
        mimetype="text/plain",
        resumable=False,
    )

    metadata_in = {
        "name": drive_file_name,
        "parents": [test_folder_id],
        "description": "Rodada 4.34 AIMM — calculo preliminar controlado sem liberacao final.",
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

    score_rows = [
        {
            "rodada": "4.34",
            "codigo_ibge": row.get("codigo_ibge", ""),
            "nm_mun": row.get("nm_mun", ""),
            "nm_uf": row.get("nm_uf", ""),
            "sigla_uf": row.get("sigla_uf", ""),
            "area_km2": row.get("area_km2", ""),
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "score_aimm_final_liberado": score_final_liberado,
            "peso_total": total_peso,
            "componentes_total": len(componentes_rows),
            "componentes_alerta": alertas_componentes,
            "status": "sucesso",
        }
    ]

    status_rows = [
        {
            "rodada": "4.34",
            "modulo": "preliminary_controlled_score",
            "manifesto_entrada": str(MANIFEST),
            "arquivo_pesos": str(WEIGHTS),
            "calculo_preliminar_executado": "sim",
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "webViewLink": metadata.get("webViewLink", ""),
            "score_aimm_final_liberado": score_final_liberado,
            "erros_estruturais": 0,
            "alertas": alertas_componentes + 1,
            "resultado": "SUCESSO",
        }
    ]

    pesos_rows = [
        {
            "rodada": "4.34",
            "dimensao": item["dimensao"],
            "variavel_manifesto": item["variavel_manifesto"],
            "peso": parse_weight(item["peso"]),
            "criterio_ok": norm(item["criterio_ok"]),
            "descricao": item["descricao"],
        }
        for item in weight_rows
    ]

    metadata_rows = [
        {
            "rodada": "4.34",
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
            "item": "Manifesto operacional 4.33",
            "status": "ok",
            "observacao": f"Arquivo lido: {MANIFEST}",
        },
        {
            "item": "Pesos preliminares 4.34",
            "status": "ok",
            "observacao": f"Soma dos pesos: {total_peso}",
        },
        {
            "item": "Calculo preliminar",
            "status": "ok",
            "observacao": f"Score preliminar controlado: {score_total}",
        },
        {
            "item": "Upload Drive API OAuth",
            "status": "ok",
            "observacao": "Arquivo de resultado enviado ao Drive.",
        },
        {
            "item": "Score final AIMM",
            "status": "bloqueado",
            "observacao": "Score final ainda nao liberado.",
        },
    ]

    registry_rows = [
        {
            "rodada": "4.34",
            "nome": "preliminary_controlled_score",
            "municipio_base": row.get("nm_mun", ""),
            "codigo_ibge": row.get("codigo_ibge", ""),
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "upload_drive_real": "sim",
            "consulta_metadata_real": "sim",
            "score_aimm_final_liberado": score_final_liberado,
            "erros_estruturais": 0,
            "status": "validado",
            "proxima_rodada": "4.35",
            "proxima_rodada_descricao": "teste ponta a ponta controlado com relatorio executivo",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_AIMM_SCORE_PRELIMINAR_4_34",
            "tipo": "calculo_preliminar_controlado",
            "descricao": "Score preliminar AIMM calculado com pesos explicitos e upload real no Drive.",
            "score_preliminar_controlado": score_total,
            "classificacao_preliminar": classificacao,
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "status": "gerado",
            "limitacao": "nao libera score final e nao executa benchmark externo real",
        }
    ]

    report_lines = [
        "# Relatório da Rodada 4.34 — cálculo preliminar controlado sem liberação final",
        "",
        "## Resultado",
        "",
        "A Rodada 4.34 calculou o score preliminar controlado da calculadora AIMM.",
        "",
        f"- Município: `{row.get('nm_mun', '')}`",
        f"- Código IBGE: `{row.get('codigo_ibge', '')}`",
        f"- Score preliminar controlado: `{score_total}`",
        f"- Classificação preliminar: `{classificacao}`",
        f"- Score AIMM final liberado: `{score_final_liberado}`",
        f"- Upload Drive real: `sim`",
        f"- Consulta metadata real: `sim`",
        f"- Arquivo criado no Drive: `{metadata.get('name', '')}`",
        f"- File ID mascarado: `{mask(file_id)}`",
        "",
        "## Pesos aplicados",
        "",
    ]

    for item in pesos_rows:
        report_lines.append(
            f"- `{item['dimensao']}` — peso `{item['peso']}` — variável `{item['variavel_manifesto']}`"
        )

    report_lines.extend(
        [
            "",
            "## Travas mantidas",
            "",
            "- Não libera score AIMM final.",
            "- Não substitui revisão humana.",
            "- Não executa benchmark externo real.",
            "- Não executa nova geometria GIS.",
            "",
            "## Próxima rodada",
            "",
            "Rodada 4.35 — teste ponta a ponta controlado com relatório executivo.",
        ]
    )

    log_lines = [
        "TESTE AIMM_PRELIMINARY_CONTROLLED_SCORE_4_34 — Fito+ Amazônia",
        "=" * 86,
        "Manifesto operacional detectado: sim",
        "Pesos preliminares detectados: sim",
        f"Soma dos pesos: {total_peso}",
        "Calculo preliminar executado: sim",
        f"Municipio: {row.get('nm_mun', '')}",
        f"Codigo IBGE: {row.get('codigo_ibge', '')}",
        f"Score preliminar controlado: {score_total}",
        f"Classificacao preliminar: {classificacao}",
        "Upload Drive real: sim",
        "Consulta metadata real: sim",
        f"Arquivo enviado ao Drive: {metadata.get('name', '')}",
        f"File ID mascarado: {mask(file_id)}",
        "Score AIMM final liberado: nao",
        "Erros estruturais: 0",
        f"Alertas: {alertas_componentes + 1}",
        "",
        "Resultado: SUCESSO.",
        "Calculo preliminar controlado AIMM executado.",
        "",
        "Trava: nao libera score final, nao substitui revisao humana, nao executa benchmark externo real e nao executa nova geometria GIS.",
    ]

    write_csv(FILES["status"], status_rows)
    write_csv(FILES["score"], score_rows)
    write_csv(FILES["componentes"], componentes_rows)
    write_csv(FILES["pesos"], pesos_rows)
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

    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
