# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from pypdf import PdfReader
from docx import Document


BASE = Path("outputs/aimm/rodada_4_38_final_ifc_aimm_operational_package")

FILES = {
    "status": BASE / "STATUS_FINAL_OPERACIONAL_IFC_AIMM_4_38.csv",
    "documentos": BASE / "MATRIZ_DOCUMENTOS_IFC_AIMM_4_38.csv",
    "dimensoes": BASE / "MATRIZ_DIMENSOES_IFC_AIMM_4_38.csv",
    "lacunas": BASE / "MATRIZ_LACUNAS_RECOMENDACOES_IFC_AIMM_4_38.csv",
    "gis": BASE / "STATUS_GIS_IFC_AIMM_4_38.csv",
    "score": BASE / "SCORE_FINAL_PRELIMINAR_IFC_AIMM_4_38.csv",
    "metadata_drive": BASE / "METADATA_DRIVE_RELATORIOS_IFC_AIMM_4_38.csv",
    "relatorio_tecnico": Path("outputs/reports/RELATORIO_TECNICO_PROFISSIONAL_IFC_AIMM_4_38.md"),
    "relatorio_executivo": Path("outputs/reports/RELATORIO_EXECUTIVO_IFC_AIMM_4_38.md"),
    "relatorio_uso": Path("outputs/reports/GUIA_USO_FINAL_IFC_AIMM_4_38.md"),
    "registry": Path("data/processed/aimm/aimm_final_ifc_operational_registry_4_38.csv"),
    "evidence": Path("data/evidence/evidence_aimm_final_ifc_operational_4_38.csv"),
    "log": Path("outputs/logs/teste_aimm_final_ifc_operational_4_38.txt"),
}


MAX_FILES = int(os.getenv("AIMM_MAX_FILES", "120"))
MAX_TEXT_CHARS = int(os.getenv("AIMM_MAX_TEXT_CHARS", "14000"))
MAX_BYTES_PER_FILE = int(os.getenv("AIMM_MAX_BYTES_PER_FILE", str(20 * 1024 * 1024)))


DIMENSIONS = [
    {
        "dimensao": "territorial_gis",
        "peso": 12,
        "nome": "Territorial / GIS",
        "descricao": "Município, base territorial, arquivos espaciais, coerência geográfica e lacunas GIS.",
        "keywords": ["gis", "geopackage", "shapefile", "geojson", "território", "territorial", "município", "ibge", "mapa", "coordenada", "área", "solo", "água", "geográfico"],
    },
    {
        "dimensao": "desenho_projeto_ifc",
        "peso": 16,
        "nome": "Desenho do projeto IFC/AIMM",
        "descricao": "Objetivo, problema público, lógica de intervenção, entregáveis, adicionalidade e maturidade do projeto.",
        "keywords": ["ifc", "aimm", "projeto", "objetivo", "impacto", "resultado", "indicador", "entregável", "teoria da mudança", "adicionalidade", "maturidade"],
    },
    {
        "dimensao": "mercado_cadeia_valor",
        "peso": 16,
        "nome": "Mercado e cadeia de valor",
        "descricao": "Demanda, oferta, compradores, fornecedores, preços, produtividade, agregação de valor e escalabilidade.",
        "keywords": ["mercado", "cadeia de valor", "comprador", "fornecedor", "preço", "demanda", "oferta", "produção", "produtividade", "exportação", "importação", "renda"],
    },
    {
        "dimensao": "evidencias_benchmarks",
        "peso": 16,
        "nome": "Evidências e benchmarks",
        "descricao": "Artigos, relatórios, literatura, bases de dados, benchmarks, metodologia e rastreabilidade das fontes.",
        "keywords": ["artigo", "estudo", "evidência", "benchmark", "fonte", "referência", "literatura", "ensaio", "metodologia", "relatório", "dados"],
    },
    {
        "dimensao": "risco_socioambiental",
        "peso": 14,
        "nome": "Risco socioambiental",
        "descricao": "Riscos, salvaguardas, biodiversidade, água, solo, comunidades, consulta, licenças e medidas de mitigação.",
        "keywords": ["risco", "salvaguarda", "ambiental", "social", "biodiversidade", "comunidade", "consulta", "mitigação", "licença", "regularização", "impacto ambiental"],
    },
    {
        "dimensao": "financeiro_operacional",
        "peso": 16,
        "nome": "Financeiro-operacional",
        "descricao": "CAPEX, OPEX, orçamento, custos, receitas, produtividade, cronograma, execução e viabilidade.",
        "keywords": [
            "capex",
            "opex",
            "custo",
            "receita",
            "investimento",
            "tir",
            "vpl",
            "payback",
            "orçamento",
            "financeiro",
            "operacional",
            "cronograma",
            "crédito",
            "credito",
            "créditos",
            "creditos",
            "financiamento",
            "linha de crédito",
            "linha de credito",
            "microcrédito",
            "microcredito",
        ],
    },
    {
        "dimensao": "governanca_execucao",
        "peso": 10,
        "nome": "Governança e execução",
        "descricao": "Instituições, responsáveis, governança, auditoria, monitoramento, qualidade, cronograma e revisão humana.",
        "keywords": ["governança", "responsável", "auditoria", "controle", "monitoramento", "execução", "comitê", "gestão", "qualidade", "prestação de contas"],
    },
]


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
    for pattern in [r"/folders/([a-zA-Z0-9_-]+)", r"/file/d/([a-zA-Z0-9_-]+)", r"[?&]id=([a-zA-Z0-9_-]+)"]:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return text


def drive_service():
    creds = Credentials(
        token=None,
        refresh_token=require_env("GOOGLE_OAUTH_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=require_env("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=require_env("GOOGLE_OAUTH_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_drive_files(service, folder_id: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed=false"

    while True:
        result = service.files().list(
            q=query,
            pageSize=min(MAX_FILES, 100),
            pageToken=page_token,
            fields="nextPageToken, files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

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


def normalize_for_match(value: str) -> str:
    """Normaliza texto para comparação sem sensibilidade a acentos."""
    text = str(value or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def extract_text(service, item: dict[str, Any]) -> tuple[str, str]:
    file_id = item.get("id", "")
    name = item.get("name", "")
    mime = item.get("mimeType", "")
    suffix = Path(name).suffix.lower()
    size = int(item.get("size", "0") or "0") if str(item.get("size", "")).isdigit() else 0

    if size and size > MAX_BYTES_PER_FILE:
        return "", "arquivo_acima_do_limite"

    try:
        if mime == "application/vnd.google-apps.document":
            return safe_decode(download_bytes(service, file_id, "text/plain"))[:MAX_TEXT_CHARS], "google_docs_exportado"

        if mime == "application/vnd.google-apps.spreadsheet":
            return safe_decode(download_bytes(service, file_id, "text/csv"))[:MAX_TEXT_CHARS], "google_sheets_exportado"

        if mime == "application/vnd.google-apps.presentation":
            return safe_decode(download_bytes(service, file_id, "text/plain"))[:MAX_TEXT_CHARS], "google_slides_exportado"

        data = download_bytes(service, file_id)

        if suffix in {".txt", ".csv", ".md", ".json"} or mime.startswith("text/"):
            return safe_decode(data)[:MAX_TEXT_CHARS], "texto_extraido"

        if suffix == ".pdf" or mime == "application/pdf":
            reader = PdfReader(io.BytesIO(data))
            pages = []
            for page in list(reader.pages)[:35]:
                pages.append(page.extract_text() or "")
            return "\n".join(pages)[:MAX_TEXT_CHARS], "pdf_extraido"

        if suffix == ".docx" or mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)[:MAX_TEXT_CHARS], "docx_extraido"

        return "", "metadata_only"

    except Exception as exc:
        return "", f"erro_extracao_{type(exc).__name__}"


def classify(name: str, mime: str, text: str) -> dict[str, Any]:
    suffix = Path(name).suffix.lower()
    name_l = normalize_for_match(name)
    text_l = normalize_for_match(text)

    if suffix in GIS_EXTENSIONS:
        doc_type = "gis"
    elif suffix == ".pdf" or "pdf" in mime:
        doc_type = "pdf"
    elif suffix == ".docx" or "wordprocessingml" in mime:
        doc_type = "docx"
    elif suffix in {".csv", ".xlsx"} or "spreadsheet" in mime:
        doc_type = "planilha"
    elif "google-apps.document" in mime:
        doc_type = "google_docs"
    else:
        doc_type = "outro"

    hits: dict[str, int] = {}

    for dim in DIMENSIONS:
        count = 0
        for kw in dim["keywords"]:
            kw_l = normalize_for_match(kw)
            if kw_l in name_l:
                count += 3
            if kw_l in text_l:
                count += 1
        hits[dim["dimensao"]] = count

    best = max(hits, key=hits.get)

    if doc_type == "gis":
        best = "territorial_gis"
        hits[best] = max(hits[best], 5)

    if hits[best] == 0:
        best = "evidencias_benchmarks"
        hits[best] = 1

    return {
        "tipo_documento": doc_type,
        "dimensao_aimm_predominante": best,
        "hits_por_dimensao": " | ".join(f"{k}={v}" for k, v in hits.items()),
        "pontuacao_triagem": hits[best],
    }


def build_scores(document_rows: list[dict[str, Any]], codigo_ibge: str, usar_gis: str) -> tuple[list[dict[str, Any]], float, str]:
    total_docs = len(document_rows)
    extracted_docs = sum(1 for r in document_rows if "extraido" in str(r.get("status_extracao", "")) or "exportado" in str(r.get("status_extracao", "")))
    gis_docs = sum(1 for r in document_rows if r.get("tipo_documento") == "gis")

    rows: list[dict[str, Any]] = []
    total = 0.0

    for dim in DIMENSIONS:
        dim_name = dim["dimensao"]
        peso = float(dim["peso"])
        docs_dim = sum(1 for r in document_rows if r.get("dimensao_aimm_predominante") == dim_name)

        if dim_name == "territorial_gis":
            if usar_gis == "sim" and codigo_ibge == "1302603":
                status = "ok_base_manaus_validada"
                pontos = peso
            elif usar_gis == "sim" and gis_docs > 0:
                status = "parcial_gis_requer_validacao"
                pontos = peso * 0.60
            elif usar_gis == "sim":
                status = "lacuna_gis"
                pontos = peso * 0.35
            else:
                status = "nao_usado"
                pontos = 0
        else:
            if docs_dim >= 2:
                status = "ok"
                pontos = peso
            elif docs_dim == 1:
                status = "parcial"
                pontos = peso * 0.65
            elif extracted_docs >= 5:
                status = "evidencia_indireta_requer_revisao"
                pontos = peso * 0.35
            elif total_docs >= 5:
                status = "documentos_presentes_sem_classificacao"
                pontos = peso * 0.25
            else:
                status = "lacuna"
                pontos = 0

        total += pontos

        rows.append(
            {
                "dimensao": dim_name,
                "nome": dim["nome"],
                "peso": peso,
                "documentos_associados": docs_dim,
                "pontos_obtidos": round(pontos, 2),
                "status": status,
                "descricao": dim["descricao"],
            }
        )

    total = round(total, 2)

    if total >= 80:
        classification = "apto_para_relatorio_profissional_com_revisao_humana"
    elif total >= 60:
        classification = "apto_com_lacunas_para_complementacao"
    else:
        classification = "nao_apto_sem_recomposicao_documental"

    return rows, total, classification


def upload_file(service, folder_id: str, path: Path, mime: str, prefix: str, run_id: str) -> dict[str, Any]:
    metadata_in = {
        "name": f"{prefix}_{run_id}_{path.name}",
        "parents": [folder_id],
        "description": "Arquivo gerado pela Rodada 4.38 AIMM/IFC.",
    }

    media = MediaFileUpload(str(path), mimetype=mime, resumable=False)

    created = service.files().create(
        body=metadata_in,
        media_body=media,
        fields="id,name,size,mimeType,parents,createdTime,modifiedTime,webViewLink",
        supportsAllDrives=True,
    ).execute()

    return service.files().get(
        fileId=created["id"],
        fields="id,name,size,mimeType,parents,createdTime,modifiedTime,webViewLink",
        supportsAllDrives=True,
    ).execute()


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_id = env("GITHUB_RUN_ID", "sem_run_id")

    service = drive_service()

    case_id = require_env("AIMM_CASE_ID")
    codigo_ibge = require_env("AIMM_CODIGO_IBGE")
    municipio = require_env("AIMM_MUNICIPIO")
    uf = require_env("AIMM_UF")
    area_km2 = require_env("AIMM_AREA_KM2")
    drive_input_folder = extract_drive_id(require_env("AIMM_DRIVE_INPUT_FOLDER"))
    output_folder_raw = env("AIMM_DRIVE_OUTPUT_FOLDER", "")
    output_folder = extract_drive_id(output_folder_raw) if output_folder_raw else require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    objetivo = require_env("AIMM_OBJETIVO_PROJETO")
    tipo_projeto = require_env("AIMM_TIPO_PROJETO")
    nivel_relatorio = require_env("AIMM_NIVEL_RELATORIO")
    usar_gis = norm_bool(require_env("AIMM_USAR_GIS"))
    extrair_documentos = norm_bool(require_env("AIMM_EXTRAIR_DOCUMENTOS"))
    observacao = env("AIMM_OBSERVACAO", "")

    files = list_drive_files(service, drive_input_folder)

    document_rows: list[dict[str, Any]] = []

    for idx, item in enumerate(files, start=1):
        text = ""
        extraction_status = "nao_executada"

        if extrair_documentos == "sim":
            text, extraction_status = extract_text(service, item)

        triage = classify(item.get("name", ""), item.get("mimeType", ""), text)

        document_rows.append(
            {
                "ordem": idx,
                "nome_arquivo": item.get("name", ""),
                "file_id_mascarado": mask(item.get("id", "")),
                "mimeType": item.get("mimeType", ""),
                "size": item.get("size", ""),
                "webViewLink": item.get("webViewLink", ""),
                "tipo_documento": triage["tipo_documento"],
                "dimensao_aimm_predominante": triage["dimensao_aimm_predominante"],
                "pontuacao_triagem": triage["pontuacao_triagem"],
                "status_extracao": extraction_status,
                "texto_amostra": text[:1000].replace("\n", " ").replace(";", ","),
                "hits_por_dimensao": triage["hits_por_dimensao"],
            }
        )

    dimension_rows, score, classification = build_scores(document_rows, codigo_ibge, usar_gis)

    gis_docs = [r for r in document_rows if r["tipo_documento"] == "gis"]

    if usar_gis == "sim" and codigo_ibge == "1302603":
        gis_status = "validado_manaus_reutilizado"
        gis_note = "A base GIS Manaus validada nas rodadas 4.22/4.23 foi considerada como referência territorial."
    elif usar_gis == "sim" and gis_docs:
        gis_status = "documento_gis_detectado_requer_validacao"
        gis_note = "Há arquivo GIS, mas novo município exige validação espacial específica."
    elif usar_gis == "sim":
        gis_status = "gis_pendente"
        gis_note = "Não foi detectado arquivo GIS na pasta; novo cálculo territorial depende de inclusão e validação."
    else:
        gis_status = "nao_usado"
        gis_note = "GIS não foi solicitado."

    lacunas = []
    for row in dimension_rows:
        status = row["status"]
        if status.startswith("ok"):
            recomendacao = "Manter evidências e registrar revisão humana."
            prioridade = "baixa"
        elif "parcial" in status or "indireta" in status:
            recomendacao = "Complementar com documentos específicos, dados quantitativos e fonte verificável."
            prioridade = "média"
        else:
            recomendacao = "Recompor documentação antes de decisão ou apresentação externa."
            prioridade = "alta"

        lacunas.append(
            {
                "dimensao": row["dimensao"],
                "status": status,
                "prioridade": prioridade,
                "recomendacao": recomendacao,
            }
        )

    status_rows = [
        {
            "rodada": "4.38",
            "case_id": case_id,
            "municipio": municipio,
            "codigo_ibge": codigo_ibge,
            "uf": uf,
            "documentos_detectados": len(document_rows),
            "documentos_extraidos": sum(1 for r in document_rows if "extraido" in r["status_extracao"] or "exportado" in r["status_extracao"]),
            "arquivos_gis_detectados": len(gis_docs),
            "status_gis": gis_status,
            "score_final_preliminar": score,
            "classificacao": classification,
            "relatorio_tecnico_profissional": "sim",
            "relatorio_executivo_ifc": "sim",
            "guia_uso": "sim",
            "upload_drive_real": "sim",
            "score_final_liberado": "nao",
            "erros_estruturais": 0,
            "resultado": "SUCESSO",
        }
    ]

    score_rows = [
        {
            "rodada": "4.38",
            "case_id": case_id,
            "score_final_preliminar": score,
            "classificacao": classification,
            "score_final_liberado": "nao",
            "observacao": "Resultado profissional preliminar; decisão final exige revisão humana e validação GIS/documental.",
        }
    ]

    gis_rows = [
        {
            "rodada": "4.38",
            "case_id": case_id,
            "usar_gis": usar_gis,
            "status_gis": gis_status,
            "arquivos_gis_detectados": len(gis_docs),
            "observacao": gis_note,
        }
    ]

    tecnico = [
        "# Relatório técnico profissional IFC/AIMM — Rodada 4.38",
        "",
        "## 1. Identificação",
        "",
        f"- Caso: `{case_id}`",
        f"- Município: `{municipio}/{uf}`",
        f"- Código IBGE: `{codigo_ibge}`",
        f"- Área informada: `{area_km2} km²`",
        f"- Tipo de projeto: `{tipo_projeto}`",
        f"- Gerado em UTC: `{now}`",
        "",
        "## 2. Objetivo informado",
        "",
        objetivo,
        "",
        "## 3. Resultado AIMM preliminar",
        "",
        f"- Score final preliminar: **{score} / 100**",
        f"- Classificação: **{classification}**",
        "- Score final liberado: **não**",
        "",
        "## 4. Base documental processada",
        "",
        f"- Documentos detectados: **{len(document_rows)}**",
        f"- Documentos com texto extraído/exportado: **{sum(1 for r in document_rows if 'extraido' in r['status_extracao'] or 'exportado' in r['status_extracao'])}**",
        f"- Arquivos GIS detectados: **{len(gis_docs)}**",
        "",
        "## 5. Status GIS",
        "",
        f"**{gis_status}** — {gis_note}",
        "",
        "## 6. Matriz AIMM por dimensão",
        "",
    ]

    for row in dimension_rows:
        tecnico.append(
            f"- **{row['nome']}**: {row['pontos_obtidos']} / {row['peso']} — `{row['status']}`. {row['descricao']}"
        )

    tecnico.extend(
        [
            "",
            "## 7. Documentos triados",
            "",
        ]
    )

    for row in document_rows[:80]:
        tecnico.append(
            f"- `{row['nome_arquivo']}` — tipo `{row['tipo_documento']}` — dimensão `{row['dimensao_aimm_predominante']}` — extração `{row['status_extracao']}`."
        )

    tecnico.extend(
        [
            "",
            "## 8. Lacunas e recomendações",
            "",
        ]
    )

    for row in lacunas:
        tecnico.append(
            f"- **{row['dimensao']}** — prioridade `{row['prioridade']}` — {row['recomendacao']}"
        )

    tecnico.extend(
        [
            "",
            "## 9. Conclusão técnica",
            "",
            "A ferramenta está funcionando como pacote operacional preliminar para apoio à elaboração e avaliação de projetos IFC/AIMM. O uso adequado exige alimentação documental organizada, validação GIS quando houver novo território, e revisão técnica humana antes de decisão final.",
        ]
    )

    executivo = [
        "# Relatório executivo IFC/AIMM — Rodada 4.38",
        "",
        "## Resultado executivo",
        "",
        f"O caso **{case_id}**, referente a **{municipio}/{uf}**, foi processado pela ferramenta AIMM.",
        "",
        f"- Documentos detectados: **{len(document_rows)}**",
        f"- Score final preliminar: **{score} / 100**",
        f"- Classificação: **{classification}**",
        f"- Status GIS: **{gis_status}**",
        "- Score final liberado: **não**",
        "",
        "## Interpretação",
        "",
        "A ferramenta já apoia triagem, extração, organização metodológica, leitura por dimensões AIMM e geração de relatórios. O resultado não deve ser tratado como decisão automática. Ele deve orientar a revisão técnica, a complementação documental e a preparação profissional do projeto.",
        "",
        "## Decisão operacional recomendada",
        "",
        "1. Usar o relatório técnico como base de revisão.",
        "2. Complementar as dimensões com lacunas médias ou altas.",
        "3. Validar GIS antes de qualquer decisão territorial fora de Manaus.",
        "4. Consolidar anexos e fontes antes de apresentação externa.",
    ]

    guia = [
        "# Guia de uso final IFC/AIMM — Rodada 4.38",
        "",
        "## Como usar agora",
        "",
        "1. Criar uma pasta Drive por caso/projeto.",
        "2. Colocar nela PDFs, DOCX, planilhas, artigos, relatórios e arquivos GIS.",
        "3. Rodar o workflow 4.38 no GitHub Actions.",
        "4. Colar o link da pasta de entrada.",
        "5. Conferir os relatórios gerados no Drive.",
        "",
        "## Regra operacional",
        "",
        "- Usuários comuns não mexem em código.",
        "- Usuários só alimentam a pasta Drive.",
        "- Você executa o workflow protegido.",
        "- O sistema gera relatório técnico, executivo, matrizes e evidências.",
        "",
        "## Limites",
        "",
        "- PDF escaneado sem texto pode não extrair corretamente.",
        "- Novo município precisa validação GIS.",
        "- Score final continua bloqueado sem revisão humana.",
    ]

    write_csv(FILES["status"], status_rows)
    write_csv(FILES["documentos"], document_rows)
    write_csv(FILES["dimensoes"], dimension_rows)
    write_csv(FILES["lacunas"], lacunas)
    write_csv(FILES["gis"], gis_rows)
    write_csv(FILES["score"], score_rows)
    write_text(FILES["relatorio_tecnico"], tecnico)
    write_text(FILES["relatorio_executivo"], executivo)
    write_text(FILES["relatorio_uso"], guia)

    uploaded = []
    uploaded.append(upload_file(service, output_folder, FILES["relatorio_tecnico"], "text/markdown", "AIMM_4_38_TECNICO", run_id))
    uploaded.append(upload_file(service, output_folder, FILES["relatorio_executivo"], "text/markdown", "AIMM_4_38_EXECUTIVO", run_id))
    uploaded.append(upload_file(service, output_folder, FILES["relatorio_uso"], "text/markdown", "AIMM_4_38_GUIA_USO", run_id))

    metadata_rows = [
        {
            "rodada": "4.38",
            "arquivo_drive": item.get("name", ""),
            "file_id_mascarado": mask(item.get("id", "")),
            "webViewLink": item.get("webViewLink", ""),
            "size": item.get("size", ""),
        }
        for item in uploaded
    ]

    registry = [
        {
            "rodada": "4.38",
            "estado": "operacional_final_preliminar",
            "case_id": case_id,
            "municipio": municipio,
            "documentos_detectados": len(document_rows),
            "score_final_preliminar": score,
            "classificacao": classification,
            "status": "validado",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_FINAL_IFC_OPERATIONAL_4_38",
            "tipo": "pacote_final_operacional_ifc_aimm",
            "descricao": "Leitura Drive, triagem documental, extração, normalização AIMM, GIS, relatórios e upload Drive.",
            "case_id": case_id,
            "documentos_detectados": len(document_rows),
            "status": "gerado",
        }
    ]

    log = [
        "TESTE AIMM_FINAL_IFC_OPERATIONAL_PACKAGE_4_38",
        "=" * 90,
        "Pacote final operacional IFC/AIMM: sim",
        f"Case ID: {case_id}",
        f"Município: {municipio}",
        f"Código IBGE: {codigo_ibge}",
        f"Documentos detectados: {len(document_rows)}",
        f"Documentos extraídos/exportados: {sum(1 for r in document_rows if 'extraido' in r['status_extracao'] or 'exportado' in r['status_extracao'])}",
        f"Arquivos GIS detectados: {len(gis_docs)}",
        f"Status GIS: {gis_status}",
        f"Score final preliminar: {score}",
        f"Classificação: {classification}",
        "Relatório técnico profissional gerado: sim",
        "Relatório executivo IFC gerado: sim",
        "Guia de uso gerado: sim",
        "Upload Drive real: sim",
        "Score final liberado: nao",
        "Erros estruturais: 0",
        "",
        "Resultado: SUCESSO.",
    ]

    write_csv(FILES["metadata_drive"], metadata_rows)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["log"], log)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log))


if __name__ == "__main__":
    main()
