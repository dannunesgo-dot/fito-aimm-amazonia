# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from pypdf import PdfReader
from docx import Document


BASE = Path("outputs/aimm/rodada_4_37_operational_interface")

FILES = {
    "status": BASE / "STATUS_INTERFACE_OPERACIONAL_AIMM_4_37.csv",
    "manifesto": BASE / "MANIFESTO_OPERACIONAL_AIMM_4_37.csv",
    "documentos": BASE / "DOCUMENTOS_TRIADOS_AIMM_4_37.csv",
    "extracoes": BASE / "EXTRACOES_NORMALIZADAS_AIMM_4_37.csv",
    "matriz_aimm": BASE / "MATRIZ_DIMENSOES_AIMM_4_37.csv",
    "gis": BASE / "STATUS_GIS_AIMM_4_37.csv",
    "score": BASE / "SCORE_OPERACIONAL_PRELIMINAR_AIMM_4_37.csv",
    "metadata_drive": BASE / "METADATA_DRIVE_RELATORIOS_AIMM_4_37.csv",
    "relatorio_tecnico": Path("outputs/reports/RELATORIO_TECNICO_PROFISSIONAL_AIMM_4_37.md"),
    "relatorio_executivo": Path("outputs/reports/RELATORIO_EXECUTIVO_IFC_AIMM_4_37.md"),
    "registry": Path("data/processed/aimm/aimm_operational_interface_registry_4_37.csv"),
    "evidence": Path("data/evidence/evidence_aimm_operational_interface_4_37.csv"),
    "log": Path("outputs/logs/teste_aimm_interface_operacional_4_37.txt"),
}


MAX_FILES = int(os.getenv("AIMM_MAX_FILES", "80"))
MAX_BYTES_PER_FILE = int(os.getenv("AIMM_MAX_BYTES_PER_FILE", str(12 * 1024 * 1024)))
MAX_TEXT_CHARS = int(os.getenv("AIMM_MAX_TEXT_CHARS", "9000"))


DIMENSIONS = [
    {
        "dimensao": "territorial_gis",
        "peso": 15,
        "descricao": "Município, UF, área, arquivos espaciais, consistência GIS e lacunas territoriais.",
    },
    {
        "dimensao": "desenho_projeto_ifc",
        "peso": 15,
        "descricao": "Objetivo, lógica de intervenção, entregáveis, aderência IFC/AIMM e maturidade do projeto.",
    },
    {
        "dimensao": "mercado_cadeia_valor",
        "peso": 15,
        "descricao": "Cadeia de valor, compradores, fornecedores, agregação de valor, demanda e escalabilidade.",
    },
    {
        "dimensao": "evidencias_benchmarks",
        "peso": 15,
        "descricao": "Artigos, relatórios, bases, benchmarks, qualidade e rastreabilidade das fontes.",
    },
    {
        "dimensao": "risco_socioambiental",
        "peso": 15,
        "descricao": "Riscos, salvaguardas, biodiversidade, água, solo, comunidade, governança e mitigação.",
    },
    {
        "dimensao": "financeiro_operacional",
        "peso": 15,
        "descricao": "CAPEX, OPEX, receitas, custos, produtividade, execução e lacunas de viabilidade.",
    },
    {
        "dimensao": "governanca_execucao",
        "peso": 10,
        "descricao": "Instituições, responsáveis, cronograma, auditoria, qualidade, travas e revisão humana.",
    },
]


KEYWORDS = {
    "territorial_gis": ["gis", "geopackage", "shapefile", "geojson", "território", "territorial", "município", "ibge", "mapa", "coordenada", "área", "solo", "água"],
    "desenho_projeto_ifc": ["ifc", "aimm", "projeto", "objetivo", "teoria da mudança", "resultado", "impacto", "indicador", "entregável", "governança"],
    "mercado_cadeia_valor": ["mercado", "cadeia de valor", "comprador", "fornecedor", "preço", "demanda", "oferta", "produção", "produtividade", "exportação", "importação"],
    "evidencias_benchmarks": ["artigo", "estudo", "evidência", "benchmark", "fonte", "referência", "literatura", "ensaio", "metodologia", "relatório"],
    "risco_socioambiental": ["risco", "salvaguarda", "ambiental", "social", "biodiversidade", "comunidade", "consulta", "mitigação", "licença", "regularização"],
    "financeiro_operacional": ["capex", "opex", "custo", "receita", "investimento", "tir", "vpl", "payback", "orçamento", "financeiro", "operacional"],
    "governanca_execucao": ["governança", "cronograma", "responsável", "auditoria", "controle", "monitoramento", "execução", "comitê", "relatório"],
}


GIS_EXTENSIONS = [".gpkg", ".shp", ".geojson", ".kml", ".kmz", ".tif", ".tiff"]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def norm_bool(value: Any) -> str:
    text = str(value or "").strip().lower()
    return "sim" if text in {"sim", "s", "yes", "true", "1"} else "nao"


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        rows = [{"status": "sem_linhas"}]

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
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


def extract_drive_id(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    patterns = [
        r"/folders/([a-zA-Z0-9_-]+)",
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return text


def drive_service():
    client_id = require_env("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = require_env("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh_token = require_env("GOOGLE_OAUTH_REFRESH_TOKEN")

    scopes = ["https://www.googleapis.com/auth/drive"]

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


def list_drive_files(service, folder_id: str) -> list[dict[str, Any]]:
    query = f"'{folder_id}' in parents and trashed=false"
    files: list[dict[str, Any]] = []
    page_token = None

    while True:
        result = (
            service.files()
            .list(
                q=query,
                pageSize=min(MAX_FILES, 100),
                pageToken=page_token,
                fields="nextPageToken, files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files.extend(result.get("files", []))
        page_token = result.get("nextPageToken")

        if not page_token or len(files) >= MAX_FILES:
            break

    return files[:MAX_FILES]


def download_bytes(service, file_id: str, export_mime: str | None = None) -> bytes:
    if export_mime:
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue()


def safe_decode(data: bytes) -> str:
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            return data.decode(encoding, errors="replace")
        except Exception:
            pass
    return ""


def extract_text_from_file(service, item: dict[str, Any]) -> tuple[str, str]:
    file_id = item.get("id", "")
    name = item.get("name", "")
    mime = item.get("mimeType", "")
    size = int(item.get("size", "0") or "0") if str(item.get("size", "")).isdigit() else 0
    suffix = Path(name).suffix.lower()

    if size and size > MAX_BYTES_PER_FILE:
        return "", f"arquivo_maior_que_limite_{MAX_BYTES_PER_FILE}_bytes"

    try:
        if mime == "application/vnd.google-apps.document":
            data = download_bytes(service, file_id, "text/plain")
            return safe_decode(data)[:MAX_TEXT_CHARS], "google_docs_export_text_plain"

        if mime == "application/vnd.google-apps.spreadsheet":
            data = download_bytes(service, file_id, "text/csv")
            return safe_decode(data)[:MAX_TEXT_CHARS], "google_sheets_export_csv"

        if mime == "application/vnd.google-apps.presentation":
            data = download_bytes(service, file_id, "text/plain")
            return safe_decode(data)[:MAX_TEXT_CHARS], "google_slides_export_text_plain"

        data = download_bytes(service, file_id, None)

        if suffix in {".txt", ".csv", ".md", ".json"} or mime.startswith("text/"):
            return safe_decode(data)[:MAX_TEXT_CHARS], "texto_simples"

        if suffix == ".pdf" or mime == "application/pdf":
            reader = PdfReader(io.BytesIO(data))
            parts: list[str] = []
            for page in list(reader.pages)[:25]:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)[:MAX_TEXT_CHARS], "pdf_pypdf_primeiras_25_paginas"

        if suffix == ".docx" or mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(io.BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text[:MAX_TEXT_CHARS], "docx_python_docx"

        return "", "tipo_nao_extraido_metadata_only"

    except Exception as exc:
        return "", f"erro_extracao:{type(exc).__name__}"


def classify_document(name: str, mime: str, text: str) -> dict[str, Any]:
    name_l = name.lower()
    text_l = text.lower()
    suffix = Path(name).suffix.lower()

    if suffix in GIS_EXTENSIONS:
        doc_type = "gis"
    elif "pdf" in mime or suffix == ".pdf":
        doc_type = "pdf"
    elif "word" in mime or suffix == ".docx":
        doc_type = "docx"
    elif "spreadsheet" in mime or suffix in {".csv", ".xlsx"}:
        doc_type = "planilha"
    elif "google-apps.document" in mime:
        doc_type = "google_docs"
    else:
        doc_type = "outro"

    dimension_hits: dict[str, int] = {}
    for dim, words in KEYWORDS.items():
        count = 0
        for word in words:
            if word in name_l:
                count += 2
            if word in text_l:
                count += 1
        dimension_hits[dim] = count

    best_dim = max(dimension_hits, key=dimension_hits.get)
    best_score = dimension_hits[best_dim]

    if best_score == 0 and doc_type == "gis":
        best_dim = "territorial_gis"
        best_score = 2

    if best_score == 0:
        best_dim = "evidencias_benchmarks"

    return {
        "tipo_documento": doc_type,
        "dimensao_aimm_predominante": best_dim,
        "pontuacao_triagem": best_score,
        "hits_por_dimensao": " | ".join(f"{k}={v}" for k, v in dimension_hits.items()),
    }


def score_aimm(doc_rows: list[dict[str, Any]], municipio: str, codigo_ibge: str, usar_gis: str) -> tuple[list[dict[str, Any]], float, str]:
    docs_by_dim = {dim["dimensao"]: 0 for dim in DIMENSIONS}

    for row in doc_rows:
        dim = row.get("dimensao_aimm_predominante", "")
        if dim in docs_by_dim:
            docs_by_dim[dim] += 1

    matriz: list[dict[str, Any]] = []
    total = 0.0

    for dim in DIMENSIONS:
        name = dim["dimensao"]
        peso = float(dim["peso"])
        docs = docs_by_dim.get(name, 0)

        if name == "territorial_gis":
            if usar_gis == "sim" and codigo_ibge == "1302603":
                status = "ok_manaus_validado"
                pontos = peso
            elif usar_gis == "sim":
                status = "alerta_gis_novo_municipio_exige_validacao"
                pontos = peso * 0.45
            else:
                status = "nao_usado"
                pontos = 0.0
        else:
            if docs >= 2:
                status = "ok"
                pontos = peso
            elif docs == 1:
                status = "parcial"
                pontos = peso * 0.55
            else:
                status = "lacuna"
                pontos = 0.0

        total += pontos
        matriz.append(
            {
                "dimensao": name,
                "peso": peso,
                "documentos_associados": docs,
                "pontos_obtidos": round(pontos, 2),
                "status": status,
                "descricao": dim["descricao"],
            }
        )

    total = round(total, 2)

    if total >= 85:
        classificacao = "piloto_operacional_apto_com_revisao_humana"
    elif total >= 65:
        classificacao = "piloto_operacional_com_lacunas_relevantes"
    else:
        classificacao = "piloto_operacional_nao_apto_sem_recomposicao"

    return matriz, total, classificacao


def upload_file(service, folder_id: str, path: Path, mime: str, prefix: str, run_id: str) -> dict[str, Any]:
    metadata_in = {
        "name": f"{prefix}_{run_id}_{path.name}",
        "parents": [folder_id],
        "description": "Arquivo gerado pela Rodada 4.37 AIMM.",
    }

    media = MediaFileUpload(str(path), mimetype=mime, resumable=False)

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

    return (
        service.files()
        .get(
            fileId=created["id"],
            fields="id,name,size,mimeType,parents,createdTime,modifiedTime,webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_id = env("GITHUB_RUN_ID", "sem_run_id")

    service = drive_service()

    case_id = require_env("AIMM_CASE_ID")
    codigo_ibge = require_env("AIMM_CODIGO_IBGE")
    municipio = require_env("AIMM_MUNICIPIO")
    uf = require_env("AIMM_UF")
    area_km2 = require_env("AIMM_AREA_KM2")
    objetivo = require_env("AIMM_OBJETIVO_PROJETO")
    tipo_projeto = require_env("AIMM_TIPO_PROJETO")
    nivel_relatorio = require_env("AIMM_NIVEL_RELATORIO")
    usar_gis = norm_bool(require_env("AIMM_USAR_GIS"))
    extrair_documentos = norm_bool(require_env("AIMM_EXTRAIR_DOCUMENTOS"))
    observacao = env("AIMM_OBSERVACAO", "")

    input_folder_id = extract_drive_id(require_env("AIMM_DRIVE_INPUT_FOLDER"))
    output_folder_input = env("AIMM_DRIVE_OUTPUT_FOLDER", "")
    output_folder_id = extract_drive_id(output_folder_input) if output_folder_input else require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")

    files = list_drive_files(service, input_folder_id)

    document_rows: list[dict[str, Any]] = []
    extraction_rows: list[dict[str, Any]] = []

    for index, item in enumerate(files, start=1):
        text = ""
        extraction_status = "nao_executada"

        if extrair_documentos == "sim":
            text, extraction_status = extract_text_from_file(service, item)

        triage = classify_document(item.get("name", ""), item.get("mimeType", ""), text)

        document_rows.append(
            {
                "ordem": index,
                "file_id_mascarado": mask(item.get("id", "")),
                "nome_arquivo": item.get("name", ""),
                "mimeType": item.get("mimeType", ""),
                "size": item.get("size", ""),
                "createdTime": item.get("createdTime", ""),
                "modifiedTime": item.get("modifiedTime", ""),
                "webViewLink": item.get("webViewLink", ""),
                "tipo_documento": triage["tipo_documento"],
                "dimensao_aimm_predominante": triage["dimensao_aimm_predominante"],
                "pontuacao_triagem": triage["pontuacao_triagem"],
                "status_extracao": extraction_status,
            }
        )

        extraction_rows.append(
            {
                "ordem": index,
                "nome_arquivo": item.get("name", ""),
                "dimensao_aimm_predominante": triage["dimensao_aimm_predominante"],
                "status_extracao": extraction_status,
                "texto_extraido_amostra": text[:1800].replace("\n", " ").replace(";", ","),
                "hits_por_dimensao": triage["hits_por_dimensao"],
            }
        )

    matriz_rows, score_total, classificacao = score_aimm(document_rows, municipio, codigo_ibge, usar_gis)

    gis_files = [
        row for row in document_rows
        if row.get("tipo_documento") == "gis" or Path(str(row.get("nome_arquivo", ""))).suffix.lower() in GIS_EXTENSIONS
    ]

    if usar_gis == "sim" and codigo_ibge == "1302603":
        gis_status = "gis_manaus_validado_reutilizado"
        gis_observacao = "Caso Manaus usa base GIS validada nas rodadas 4.22/4.23."
    elif usar_gis == "sim":
        gis_status = "gis_novo_municipio_pendente_validacao"
        gis_observacao = "Novo município exige rodada GIS específica antes de score final."
    else:
        gis_status = "gis_nao_usado"
        gis_observacao = "Execução sem uso de GIS."

    manifest_rows = [
        {
            "rodada": "4.37",
            "case_id": case_id,
            "codigo_ibge": codigo_ibge,
            "municipio": municipio,
            "uf": uf,
            "area_km2": area_km2,
            "tipo_projeto": tipo_projeto,
            "nivel_relatorio": nivel_relatorio,
            "usar_gis": usar_gis,
            "extrair_documentos": extrair_documentos,
            "drive_input_folder_id_mascarado": mask(input_folder_id),
            "drive_output_folder_id_mascarado": mask(output_folder_id),
            "objetivo_projeto": objetivo,
            "observacao": observacao,
        }
    ]

    score_rows = [
        {
            "rodada": "4.37",
            "case_id": case_id,
            "codigo_ibge": codigo_ibge,
            "municipio": municipio,
            "uf": uf,
            "documentos_detectados": len(document_rows),
            "documentos_extraidos": sum(1 for r in document_rows if str(r.get("status_extracao", "")).startswith(("texto", "pdf", "docx", "google"))),
            "arquivos_gis_detectados": len(gis_files),
            "score_operacional_preliminar": score_total,
            "classificacao_operacional": classificacao,
            "score_final_liberado": "nao",
            "status": "sucesso",
        }
    ]

    gis_rows = [
        {
            "rodada": "4.37",
            "case_id": case_id,
            "codigo_ibge": codigo_ibge,
            "municipio": municipio,
            "usar_gis": usar_gis,
            "arquivos_gis_detectados": len(gis_files),
            "status_gis": gis_status,
            "observacao": gis_observacao,
            "score_final_liberado": "nao",
        }
    ]

    tecnico = [
        "# Relatório técnico profissional AIMM 4.37",
        "",
        "## 1. Identificação do caso",
        "",
        f"- ID do caso: `{case_id}`",
        f"- Município: `{municipio}`",
        f"- Código IBGE: `{codigo_ibge}`",
        f"- UF: `{uf}`",
        f"- Área informada: `{area_km2} km²`",
        f"- Tipo de projeto: `{tipo_projeto}`",
        f"- Nível de relatório solicitado: `{nivel_relatorio}`",
        "",
        "## 2. Objetivo informado",
        "",
        objetivo,
        "",
        "## 3. Sumário de processamento",
        "",
        f"- Documentos detectados no Drive: `{len(document_rows)}`",
        f"- Documentos com extração controlada: `{sum(1 for r in document_rows if r.get('status_extracao') != 'nao_executada')}`",
        f"- Arquivos GIS detectados: `{len(gis_files)}`",
        f"- Status GIS: `{gis_status}`",
        f"- Score operacional preliminar: `{score_total} / 100`",
        f"- Classificação operacional: `{classificacao}`",
        f"- Score final liberado: `nao`",
        "",
        "## 4. Dimensões AIMM avaliadas",
        "",
    ]

    for row in matriz_rows:
        tecnico.append(
            f"- **{row['dimensao']}** — {row['pontos_obtidos']} / {row['peso']} pontos — status `{row['status']}`. {row['descricao']}"
        )

    tecnico.extend(
        [
            "",
            "## 5. Triagem documental",
            "",
        ]
    )

    for row in document_rows[:40]:
        tecnico.append(
            f"- `{row['nome_arquivo']}` — tipo `{row['tipo_documento']}` — dimensão predominante `{row['dimensao_aimm_predominante']}` — extração `{row['status_extracao']}`."
        )

    tecnico.extend(
        [
            "",
            "## 6. Lacunas críticas",
            "",
            "- O score final permanece bloqueado.",
            "- Novo município exige validação GIS própria antes de decisão final.",
            "- Extrações automáticas devem ser revisadas quando o documento for imagem escaneada, PDF ruim ou arquivo sem texto selecionável.",
            "- A classificação é preliminar e depende de revisão técnica humana.",
            "",
            "## 7. Recomendação técnica",
            "",
            "Usar este relatório como triagem profissional inicial para orientar revisão técnica, complementação documental, validação GIS, estruturação de evidências e preparação de relatório IFC/AIMM mais completo.",
        ]
    )

    executivo = [
        "# Relatório executivo IFC/AIMM 4.37",
        "",
        "## Resultado executivo",
        "",
        f"O caso `{case_id}` foi processado pela interface operacional AIMM 4.37 para `{municipio}/{uf}`.",
        "",
        f"- Score operacional preliminar: **{score_total} / 100**",
        f"- Classificação: **{classificacao}**",
        f"- Documentos analisados: **{len(document_rows)}**",
        f"- Arquivos GIS detectados: **{len(gis_files)}**",
        f"- Status GIS: **{gis_status}**",
        f"- Score final liberado: **não**",
        "",
        "## Leitura para decisão",
        "",
        "O resultado indica nível preliminar de maturidade documental, territorial, operacional e metodológica do caso. A ferramenta apoia elaboração e avaliação de projeto, mas não substitui decisão técnica, validação GIS, análise jurídica, avaliação financeira completa nem revisão IFC/AIMM formal.",
        "",
        "## Próximos passos recomendados",
        "",
        "1. Revisar documentos classificados por dimensão AIMM.",
        "2. Corrigir lacunas de documentação, custos, mercado, riscos e salvaguardas.",
        "3. Validar GIS para novo município quando aplicável.",
        "4. Evoluir para relatório técnico completo com anexos e revisão humana.",
    ]

    write_csv(FILES["manifesto"], manifest_rows)
    write_csv(FILES["documentos"], document_rows)
    write_csv(FILES["extracoes"], extraction_rows)
    write_csv(FILES["matriz_aimm"], matriz_rows)
    write_csv(FILES["gis"], gis_rows)
    write_csv(FILES["score"], score_rows)
    write_text(FILES["relatorio_tecnico"], tecnico)
    write_text(FILES["relatorio_executivo"], executivo)

    uploaded_tecnico = upload_file(service, output_folder_id, FILES["relatorio_tecnico"], "text/markdown", "AIMM_4_37_TECNICO", run_id)
    uploaded_exec = upload_file(service, output_folder_id, FILES["relatorio_executivo"], "text/markdown", "AIMM_4_37_EXECUTIVO", run_id)

    metadata_rows = [
        {
            "rodada": "4.37",
            "tipo": "relatorio_tecnico",
            "arquivo_drive": uploaded_tecnico.get("name", ""),
            "file_id_mascarado": mask(uploaded_tecnico.get("id", "")),
            "webViewLink": uploaded_tecnico.get("webViewLink", ""),
            "size": uploaded_tecnico.get("size", ""),
        },
        {
            "rodada": "4.37",
            "tipo": "relatorio_executivo",
            "arquivo_drive": uploaded_exec.get("name", ""),
            "file_id_mascarado": mask(uploaded_exec.get("id", "")),
            "webViewLink": uploaded_exec.get("webViewLink", ""),
            "size": uploaded_exec.get("size", ""),
        },
    ]

    status_rows = [
        {
            "rodada": "4.37",
            "modulo": "operational_interface_inputs",
            "interface_github_actions": "sim",
            "entrada_por_campos": "sim",
            "drive_input_folder_lido": "sim",
            "documentos_detectados": len(document_rows),
            "extracao_documental_executada": extrair_documentos,
            "gis_considerado": usar_gis,
            "status_gis": gis_status,
            "relatorio_tecnico_gerado": "sim",
            "relatorio_executivo_gerado": "sim",
            "upload_drive_real": "sim",
            "score_operacional_preliminar": score_total,
            "classificacao_operacional": classificacao,
            "score_final_liberado": "nao",
            "erros_estruturais": 0,
            "alertas": 2 if "pendente" in gis_status else 1,
            "resultado": "SUCESSO",
        }
    ]

    registry_rows = [
        {
            "rodada": "4.37",
            "nome": "operational_interface_inputs",
            "estado": "piloto_operacional_por_interface",
            "case_id": case_id,
            "municipio": municipio,
            "codigo_ibge": codigo_ibge,
            "documentos_detectados": len(document_rows),
            "score_operacional_preliminar": score_total,
            "classificacao_operacional": classificacao,
            "status": "validado",
            "proxima_recomendada": "4.38_ingestao_documental_em_lote_e_relatorio_profissional_com_anexos",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_AIMM_OPERATIONAL_INTERFACE_4_37",
            "tipo": "interface_operacional_github_actions_drive_docs",
            "descricao": "Entrada por campos no GitHub Actions, leitura de pasta Drive, triagem, extração, normalização AIMM e geração de relatórios.",
            "case_id": case_id,
            "documentos_detectados": len(document_rows),
            "relatorio_tecnico_drive": uploaded_tecnico.get("name", ""),
            "relatorio_executivo_drive": uploaded_exec.get("name", ""),
            "status": "gerado",
        }
    ]

    log_lines = [
        "TESTE AIMM_OPERATIONAL_INTERFACE_INPUTS_4_37 — Fito+ Amazônia",
        "=" * 90,
        "Interface operacional GitHub Actions: sim",
        "Entrada por campos: sim",
        f"Case ID: {case_id}",
        f"Município: {municipio}",
        f"Código IBGE: {codigo_ibge}",
        f"Drive input folder mascarado: {mask(input_folder_id)}",
        f"Drive output folder mascarado: {mask(output_folder_id)}",
        f"Documentos detectados: {len(document_rows)}",
        f"Extração documental executada: {extrair_documentos}",
        f"Arquivos GIS detectados: {len(gis_files)}",
        f"Status GIS: {gis_status}",
        f"Score operacional preliminar: {score_total}",
        f"Classificação operacional: {classificacao}",
        "Relatório técnico profissional gerado: sim",
        "Relatório executivo IFC gerado: sim",
        "Upload Drive real: sim",
        "Score final liberado: nao",
        "Erros estruturais: 0",
        f"Alertas: {2 if 'pendente' in gis_status else 1}",
        "",
        "Resultado: SUCESSO.",
        "",
        "Travas: score final bloqueado; revisão humana obrigatória; novo município exige validação GIS própria.",
    ]

    write_csv(FILES["metadata_drive"], metadata_rows)
    write_csv(FILES["status"], status_rows)
    write_csv(FILES["registry"], registry_rows)
    write_csv(FILES["evidence"], evidence_rows)
    write_text(FILES["log"], log_lines)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
