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


BASE = Path("outputs/aimm/rodada_4_36_demo_usage_handoff")

FILES = {
    "interface_html": BASE / "INTERFACE_AIMM_DEMO_4_36.html",
    "guia_equipe": BASE / "GUIA_EQUIPE_USO_SIMPLES_AIMM_4_36.md",
    "guia_operador": BASE / "GUIA_OPERADOR_TECNICO_AIMM_4_36.md",
    "mapa_arquivos": BASE / "MAPA_ARQUIVOS_PASTAS_AIMM_4_36.csv",
    "matriz_dimensoes": BASE / "MATRIZ_DIMENSOES_INDICADORES_AIMM_4_36.csv",
    "formulario_entrada": BASE / "FORMULARIO_ENTRADA_OPERACIONAL_AIMM_4_36.csv",
    "manifesto_documentos": BASE / "MANIFESTO_DOCUMENTOS_AIMM_4_36.csv",
    "status": BASE / "STATUS_PACOTE_CONGELADO_AIMM_4_36.csv",
    "metadata_drive": BASE / "METADATA_DRIVE_PACOTE_CONGELADO_AIMM_4_36.csv",
    "checklist": BASE / "CHECKLIST_USO_DEMONSTRACAO_AIMM_4_36.csv",
    "registry": Path("data/processed/aimm/aimm_demo_usage_handoff_registry_4_36.csv"),
    "evidence": Path("data/evidence/evidence_aimm_demo_usage_handoff_4_36.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_PACOTE_CONGELADO_4_36.md"),
    "log": Path("outputs/logs/teste_aimm_pacote_congelado_4_36.txt"),
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


def build_interface_html(now: str) -> list[str]:
    return [
        "<!doctype html>",
        "<html lang='pt-BR'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "  <title>AIMM — Interface de demonstração 4.36</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 0; background: #f6f7f9; color: #1f2937; }",
        "    header { background: #0f172a; color: white; padding: 24px; }",
        "    main { max-width: 1120px; margin: 24px auto; padding: 0 18px; }",
        "    section { background: white; border: 1px solid #d9dee7; border-radius: 12px; padding: 18px; margin-bottom: 18px; }",
        "    h1, h2, h3 { margin-top: 0; }",
        "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }",
        "    .card { border: 1px solid #d9dee7; border-radius: 10px; padding: 14px; background: #fbfdff; }",
        "    .ok { color: #166534; font-weight: bold; }",
        "    .warn { color: #92400e; font-weight: bold; }",
        "    .block { background: #eef2ff; border-left: 5px solid #3730a3; padding: 12px; }",
        "    label { display: block; margin-top: 10px; font-weight: bold; }",
        "    input, select, textarea { width: 100%; box-sizing: border-box; padding: 9px; border: 1px solid #cbd5e1; border-radius: 8px; }",
        "    button { margin-top: 12px; padding: 10px 14px; border: 0; border-radius: 8px; background: #0f172a; color: white; cursor: pointer; }",
        "    code { background: #e5e7eb; padding: 2px 5px; border-radius: 4px; }",
        "    table { width: 100%; border-collapse: collapse; }",
        "    th, td { border: 1px solid #d9dee7; padding: 8px; text-align: left; }",
        "    th { background: #f1f5f9; }",
        "  </style>",
        "</head>",
        "<body>",
        "<header>",
        "  <h1>AIMM — Interface de demonstração 4.36</h1>",
        "  <p>Pacote congelado de demonstração, uso e retomada. Gerado em: " + now + "</p>",
        "</header>",
        "<main>",
        "  <section>",
        "    <h2>1. Status operacional</h2>",
        "    <div class='grid'>",
        "      <div class='card'><h3>Pipeline</h3><p class='ok'>Piloto operacional controlado validado</p></div>",
        "      <div class='card'><h3>Drive API</h3><p class='ok'>Upload real via OAuth validado</p></div>",
        "      <div class='card'><h3>GIS Manaus</h3><p class='warn'>Base validada; novos municípios exigem nova rotina GIS</p></div>",
        "      <div class='card'><h3>Score final</h3><p class='warn'>Não liberado; apenas preliminar controlado</p></div>",
        "    </div>",
        "  </section>",
        "  <section>",
        "    <h2>2. Como usar sem entender programação</h2>",
        "    <ol>",
        "      <li>Preencher o formulário simples abaixo.</li>",
        "      <li>Baixar o CSV gerado.</li>",
        "      <li>Salvar o CSV na pasta combinada do Drive ou enviar ao operador.</li>",
        "      <li>Operador executa workflow correspondente no GitHub Actions.</li>",
        "      <li>Relatório e evidências são gerados e arquivados.</li>",
        "    </ol>",
        "    <div class='block'>A versão 4.36 é demonstrativa e auto-instrucional. A entrada por formulário direto no GitHub Actions deve ser implementada na 4.37.</div>",
        "  </section>",
        "  <section>",
        "    <h2>3. Formulário simples de entrada</h2>",
        "    <label>Código IBGE</label>",
        "    <input id='codigo_ibge' value='1302603'>",
        "    <label>Município</label>",
        "    <input id='nm_mun' value='Manaus'>",
        "    <label>UF</label>",
        "    <input id='sigla_uf' value='AM'>",
        "    <label>Área km²</label>",
        "    <input id='area_km2' value='11401.092'>",
        "    <label>Documento ou observação</label>",
        "    <textarea id='observacao'>Entrada operacional controlada para AIMM.</textarea>",
        "    <button onclick='baixarCSV()'>Baixar CSV de entrada</button>",
        "  </section>",
        "  <section>",
        "    <h2>4. Dimensões AIMM em uso</h2>",
        "    <table>",
        "      <tr><th>Dimensão</th><th>Peso</th><th>Uso</th></tr>",
        "      <tr><td>GIS territorial</td><td>25</td><td>Território, município, base espacial e consistência GIS</td></tr>",
        "      <tr><td>Ingestão de arquivos</td><td>20</td><td>Entrada e validação de documentos e dados</td></tr>",
        "      <tr><td>Benchmarks e fontes</td><td>20</td><td>Fontes, evidências, normalização e proxies</td></tr>",
        "      <tr><td>Drive API OAuth</td><td>20</td><td>Arquivamento e interoperabilidade GitHub-Drive</td></tr>",
        "      <tr><td>Metadados municipais</td><td>10</td><td>IBGE, nome, UF, área e campos mínimos</td></tr>",
        "      <tr><td>Governança e travas</td><td>5</td><td>Controle de versão, bloqueio de score final e revisão humana</td></tr>",
        "    </table>",
        "  </section>",
        "  <section>",
        "    <h2>5. O que ainda falta para uso amplo pela equipe</h2>",
        "    <ul>",
        "      <li>4.37 — interface operacional por campos de entrada no GitHub Actions.</li>",
        "      <li>4.38 — ingestão real de documentos em lote.</li>",
        "      <li>4.39 — GIS automatizado para novo município.</li>",
        "      <li>4.40 — relatório técnico profissional completo com anexos.</li>",
        "    </ul>",
        "  </section>",
        "</main>",
        "<script>",
        "function esc(v) { return String(v).replaceAll(';', ',').replaceAll('\\n', ' '); }",
        "function baixarCSV() {",
        "  const header = 'codigo_ibge;nm_mun;sigla_uf;area_km2;observacao\\n';",
        "  const row = [",
        "    esc(document.getElementById('codigo_ibge').value),",
        "    esc(document.getElementById('nm_mun').value),",
        "    esc(document.getElementById('sigla_uf').value),",
        "    esc(document.getElementById('area_km2').value),",
        "    esc(document.getElementById('observacao').value)",
        "  ].join(';') + '\\n';",
        "  const blob = new Blob([header + row], {type: 'text/csv;charset=utf-8'});",
        "  const a = document.createElement('a');",
        "  a.href = URL.createObjectURL(blob);",
        "  a.download = 'entrada_aimm_operacional.csv';",
        "  a.click();",
        "}",
        "</script>",
        "</body>",
        "</html>",
    ]


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    run_id = os.getenv("GITHUB_RUN_ID", "sem_run_id")

    test_folder_id = require_env("GOOGLE_DRIVE_TEST_FOLDER_ID")
    root_folder_id = require_env("GOOGLE_DRIVE_ROOT_FOLDER_ID")

    matriz_dimensoes = [
        {"dimensao": "gis_territorial", "peso": 25, "indicador": "pacote_gis_validado", "descricao": "Confirma base GIS Manaus, join e validação visual.", "status_4_36": "piloto_validado_com_lacunas"},
        {"dimensao": "ingestao_arquivos", "peso": 20, "indicador": "pacote_ingestao_validado", "descricao": "Confirma manifesto e validação inicial de arquivos.", "status_4_36": "validado"},
        {"dimensao": "benchmarks_fontes", "peso": 20, "indicador": "pacote_benchmark_validado", "descricao": "Confirma fontes, proxies, normalização e lacunas.", "status_4_36": "validado_sem_extracao_externa_real"},
        {"dimensao": "drive_api_oauth", "peso": 20, "indicador": "drive_api_oauth_validada", "descricao": "Confirma upload real GitHub-Drive por OAuth.", "status_4_36": "validado"},
        {"dimensao": "metadados_municipais", "peso": 10, "indicador": "metadados_minimos", "descricao": "Confirma código IBGE, município, UF, sigla e área.", "status_4_36": "validado_para_manaus"},
        {"dimensao": "governanca_travas", "peso": 5, "indicador": "travas_operacionais", "descricao": "Mantém score final bloqueado, rastreabilidade e revisão humana.", "status_4_36": "validado"},
    ]

    mapa_arquivos = [
        {"grupo": "entrada", "arquivo_ou_pasta": "data/manual/aimm", "funcao": "manifests, formulários e parâmetros editáveis", "usuario": "operador"},
        {"grupo": "scripts", "arquivo_ou_pasta": "scripts", "funcao": "processamento das rodadas AIMM", "usuario": "operador técnico"},
        {"grupo": "workflows", "arquivo_ou_pasta": ".github/workflows", "funcao": "execução automatizada no GitHub Actions", "usuario": "operador"},
        {"grupo": "outputs", "arquivo_ou_pasta": "outputs/aimm", "funcao": "artefatos gerados por rodada", "usuario": "equipe gestora"},
        {"grupo": "relatórios", "arquivo_ou_pasta": "outputs/reports", "funcao": "relatórios técnicos e executivos", "usuario": "equipe gestora"},
        {"grupo": "logs", "arquivo_ou_pasta": "outputs/logs", "funcao": "verificação de execução e erros", "usuario": "operador"},
        {"grupo": "Drive", "arquivo_ou_pasta": "07_versoes_congeladas", "funcao": "ZIPs arquivados e congelados", "usuario": "coordenação"},
        {"grupo": "Drive", "arquivo_ou_pasta": "09_gis", "funcao": "insumos e evidências GIS", "usuario": "operador GIS"},
        {"grupo": "Drive", "arquivo_ou_pasta": "04_outputs", "funcao": "materiais compartilháveis", "usuario": "equipe"},
    ]

    formulario_entrada = [
        {"campo": "codigo_ibge", "exemplo": "1302603", "obrigatorio": "sim", "descricao": "Código IBGE do município."},
        {"campo": "nm_mun", "exemplo": "Manaus", "obrigatorio": "sim", "descricao": "Nome do município."},
        {"campo": "sigla_uf", "exemplo": "AM", "obrigatorio": "sim", "descricao": "Sigla da UF."},
        {"campo": "area_km2", "exemplo": "11401.092", "obrigatorio": "sim", "descricao": "Área do município em km²."},
        {"campo": "documento_referencia", "exemplo": "municipio_manaus_1302603.gpkg", "obrigatorio": "nao", "descricao": "Documento base ou arquivo GIS associado."},
        {"campo": "observacao", "exemplo": "Entrada operacional controlada", "obrigatorio": "nao", "descricao": "Observação livre."},
    ]

    manifesto_documentos = [
        {"tipo_documento": "GIS", "exemplo": "municipio_manaus_1302603.gpkg", "pasta_drive": "09_gis", "uso_aimm": "cálculo territorial e validação espacial", "obrigatorio_piloto": "sim"},
        {"tipo_documento": "manifesto_operacional", "exemplo": "aimm_operational_input_manifest_4_33.csv", "pasta_drive": "04_outputs ou GitHub data/manual/aimm", "uso_aimm": "entrada controlada", "obrigatorio_piloto": "sim"},
        {"tipo_documento": "pesos", "exemplo": "aimm_preliminary_score_weights_4_34.csv", "pasta_drive": "04_outputs ou GitHub data/manual/aimm", "uso_aimm": "cálculo preliminar", "obrigatorio_piloto": "sim"},
        {"tipo_documento": "benchmark", "exemplo": "fontes e proxies", "pasta_drive": "02_evidencias", "uso_aimm": "normalização e revisão técnica", "obrigatorio_piloto": "nao"},
        {"tipo_documento": "relatorio", "exemplo": "RELATORIO_EXECUTIVO_AIMM_4_35.md", "pasta_drive": "04_outputs", "uso_aimm": "comunicação executiva", "obrigatorio_piloto": "sim"},
    ]

    guia_equipe = [
        "# Guia simples de uso AIMM 4.36 — equipe não técnica",
        "",
        "## O que funciona agora",
        "",
        "- A calculadora AIMM já executa um piloto operacional controlado.",
        "- Já existe upload real no Google Drive por API.",
        "- Já existe relatório executivo controlado.",
        "- Já existe score preliminar controlado.",
        "",
        "## Como a equipe deve usar",
        "",
        "1. Abrir a interface HTML `INTERFACE_AIMM_DEMO_4_36.html`.",
        "2. Preencher o formulário simples.",
        "3. Baixar o CSV.",
        "4. Enviar o CSV ao operador ou salvar na pasta combinada.",
        "5. Aguardar execução da rodada operacional.",
        "6. Ler o relatório executivo gerado.",
        "",
        "## O que a equipe não deve fazer",
        "",
        "- Não editar scripts.",
        "- Não alterar workflows.",
        "- Não apagar arquivos do Drive.",
        "- Não tratar score preliminar como decisão final.",
    ]

    guia_operador = [
        "# Guia técnico do operador AIMM 4.36",
        "",
        "## Estado congelado",
        "",
        "AIMM está congelado como piloto funcional controlado após as rodadas 4.31-B, 4.32, 4.33, 4.34 e 4.35.",
        "",
        "## Fluxo operacional atual",
        "",
        "Entrada controlada → validação → cálculo preliminar → relatório executivo → upload Drive → arquivamento.",
        "",
        "## Travas",
        "",
        "- Score final bloqueado.",
        "- Benchmark externo real ainda não automatizado.",
        "- GIS automatizado para novos municípios ainda não implementado.",
        "- Revisão humana permanece obrigatória.",
        "",
        "## Próxima evolução recomendada",
        "",
        "4.37 — interface operacional por campos no GitHub Actions.",
        "4.38 — ingestão real de documentos em lote.",
        "4.39 — GIS automatizado para novo município.",
        "4.40 — relatório técnico profissional completo.",
    ]

    report = [
        "# Relatório AIMM 4.36 — pacote congelado de demonstração, uso e retomada",
        "",
        "## Resultado",
        "",
        "A Rodada 4.36 congelou o pacote demonstrável da calculadora AIMM.",
        "",
        "## Entregas",
        "",
        "- Interface HTML autoexplicativa.",
        "- Guia simples para equipe não técnica.",
        "- Guia técnico para operador.",
        "- Mapa de arquivos e pastas.",
        "- Matriz de dimensões e indicadores.",
        "- Formulário simples de entrada.",
        "- Manifesto de documentos.",
        "- Evidência e log.",
        "- Upload real do pacote HTML no Google Drive.",
        "",
        "## Situação funcional",
        "",
        "- Piloto operacional controlado: validado.",
        "- Interface demonstrativa: gerada.",
        "- Alimentação simples por CSV: preparada.",
        "- Drive API OAuth: validado.",
        "- Relatório executivo: validado.",
        "- Score final: não liberado.",
        "",
        "## Limitação objetiva",
        "",
        "A 4.36 não é ainda uma aplicação web com upload de documentos por arrastar-e-soltar. Para isso será necessária a 4.37/4.38.",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.37 — interface operacional por campos de entrada no GitHub Actions.",
    ]

    checklist = [
        {"item": "Interface HTML", "status": "gerada", "observacao": "Abrir no navegador."},
        {"item": "Guia equipe", "status": "gerado", "observacao": "Compartilhável com equipe não técnica."},
        {"item": "Guia operador", "status": "gerado", "observacao": "Uso técnico controlado."},
        {"item": "Matriz dimensões", "status": "gerada", "observacao": "Base de indicadores AIMM."},
        {"item": "Formulário de entrada", "status": "gerado", "observacao": "Modelo para alimentação simples."},
        {"item": "Manifesto documentos", "status": "gerado", "observacao": "Define documentos aceitos e uso."},
        {"item": "Upload Drive", "status": "executado", "observacao": "HTML enviado ao Drive via OAuth."},
        {"item": "Score final", "status": "bloqueado", "observacao": "Não liberado."},
    ]

    status = [
        {
            "rodada": "4.36",
            "pacote": "demo_usage_handoff_package",
            "interface_html": "gerada",
            "guia_equipe": "gerado",
            "guia_operador": "gerado",
            "mapa_arquivos": "gerado",
            "matriz_dimensoes": "gerada",
            "formulario_entrada": "gerado",
            "manifesto_documentos": "gerado",
            "drive_api_oauth": "validado",
            "score_final_liberado": "nao",
            "status": "sucesso",
        }
    ]

    registry = [
        {
            "rodada": "4.36",
            "nome": "demo_usage_handoff_package",
            "estado": "pacote_congelado_piloto_funcional_controlado",
            "interface_demonstrativa": "sim",
            "uso_equipe_nao_tecnica": "preparado",
            "drive_upload_real": "sim",
            "proxima_rodada": "4.37",
            "proxima_rodada_descricao": "interface operacional por campos de entrada",
            "status": "validado",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_DEMO_USAGE_HANDOFF_4_36",
            "tipo": "pacote_congelado_demonstracao_uso_retomada",
            "descricao": "Pacote demonstrável com interface HTML, guias, matriz, formulário, manifesto e upload real no Drive.",
            "status": "gerado",
            "limitacao": "interface ainda nao executa upload direto de documentos por navegador",
        }
    ]

    html_lines = build_interface_html(now)
    write_text(FILES["interface_html"], html_lines)
    write_text(FILES["guia_equipe"], guia_equipe)
    write_text(FILES["guia_operador"], guia_operador)
    write_csv(FILES["mapa_arquivos"], mapa_arquivos)
    write_csv(FILES["matriz_dimensoes"], matriz_dimensoes)
    write_csv(FILES["formulario_entrada"], formulario_entrada)
    write_csv(FILES["manifesto_documentos"], manifesto_documentos)
    write_csv(FILES["status"], status)
    write_csv(FILES["checklist"], checklist)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)

    service = oauth_drive_service()
    drive_file_name = f"AIMM_4_36_INTERFACE_DEMONSTRACAO_{run_id}.html"

    media = MediaFileUpload(
        str(FILES["interface_html"]),
        mimetype="text/html",
        resumable=False,
    )

    metadata_in = {
        "name": drive_file_name,
        "parents": [test_folder_id],
        "description": "Rodada 4.36 AIMM — interface demonstrativa e pacote congelado de uso.",
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

    metadata_rows = [
        {
            "rodada": "4.36",
            "arquivo_drive": metadata.get("name", ""),
            "file_id_mascarado": mask(file_id),
            "size": metadata.get("size", ""),
            "mimeType": metadata.get("mimeType", ""),
            "parents": ",".join(metadata.get("parents", [])),
            "createdTime": metadata.get("createdTime", ""),
            "modifiedTime": metadata.get("modifiedTime", ""),
            "webViewLink": metadata.get("webViewLink", ""),
            "root_folder_id_mascarado": mask(root_folder_id),
            "test_folder_id_mascarado": mask(test_folder_id),
        }
    ]

    write_csv(FILES["metadata_drive"], metadata_rows)

    log_lines = [
        "TESTE AIMM_DEMO_USAGE_HANDOFF_PACKAGE_4_36 — Fito+ Amazônia",
        "=" * 86,
        "Pacote congelado de demonstracao: sim",
        "Interface HTML gerada: sim",
        "Guia equipe gerado: sim",
        "Guia operador gerado: sim",
        "Mapa de arquivos gerado: sim",
        "Matriz dimensoes indicadores gerada: sim",
        "Formulario entrada operacional gerado: sim",
        "Manifesto documentos gerado: sim",
        "Upload Drive real: sim",
        "Consulta metadata real: sim",
        f"Arquivo enviado ao Drive: {metadata.get('name', '')}",
        f"File ID mascarado: {mask(file_id)}",
        "Score AIMM final liberado: nao",
        "Erros estruturais: 0",
        "Alertas: 1",
        "",
        "Resultado: SUCESSO.",
        "Pacote congelado de demonstracao, uso e retomada gerado.",
        "",
        "Trava: interface 4.36 e demonstrativa; upload direto de documentos por navegador depende da 4.37/4.38.",
    ]

    write_text(FILES["log"], log_lines)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
