# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_30_api_drive_github_dryrun")

FILES = {
    "diagnostico": BASE / "DIAGNOSTICO_API_DRIVE_GITHUB_DRYRUN_4_30.md",
    "secrets": BASE / "STATUS_SECRETS_DRIVE_GITHUB_4_30.csv",
    "estrategia": BASE / "ESTRATEGIA_SEGURA_API_DRIVE_GITHUB_4_30.csv",
    "checklist": BASE / "CHECKLIST_CONFIGURACAO_API_DRIVE_GITHUB_4_30.csv",
    "plano_431": BASE / "PLANO_TESTE_REAL_DRIVE_GITHUB_4_31.csv",
    "registry": Path("data/processed/aimm/aimm_drive_github_auth_dryrun_registry_4_30.csv"),
    "status": Path("data/processed/aimm/aimm_drive_github_auth_dryrun_status_4_30.csv"),
    "evidence": Path("data/evidence/evidence_aimm_drive_github_auth_dryrun_4_30.csv"),
    "report": Path("outputs/reports/RELATORIO_API_DRIVE_GITHUB_DRYRUN_4_30.md"),
    "log": Path("outputs/logs/teste_api_drive_github_dryrun_4_30.txt"),
}


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        rows = [{"status": "sem_linhas"}]

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    normalized_rows = [{key: row.get(key, "") for key in fieldnames} for row in rows]

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(normalized_rows)


def present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def secret_row(name: str, purpose: str, required_for: str) -> dict[str, str]:
    value = os.getenv(name, "").strip()
    return {
        "secret_ou_variavel": name,
        "presente": "sim" if value else "nao",
        "comprimento_detectado": str(len(value)) if value else "0",
        "valor_exposto": "nao",
        "finalidade": purpose,
        "necessario_para": required_for,
    }


def main() -> None:
    errors: list[str] = []
    alerts: list[str] = []

    github_oidc_url = present("ACTIONS_ID_TOKEN_REQUEST_URL")
    github_oidc_token = present("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    github_oidc_available = github_oidc_url and github_oidc_token

    wif_provider = present("GOOGLE_WORKLOAD_IDENTITY_PROVIDER")
    service_account = present("GOOGLE_SERVICE_ACCOUNT")
    project_id = present("GOOGLE_PROJECT_ID")
    drive_root = present("GOOGLE_DRIVE_ROOT_FOLDER_ID")
    drive_test = present("GOOGLE_DRIVE_TEST_FOLDER_ID")
    json_key = present("GDRIVE_SERVICE_ACCOUNT_JSON")

    wif_ready = wif_provider and service_account
    json_ready = json_key

    if wif_ready:
        auth_strategy = "workload_identity_federation_preferencial_detectada"
    elif json_ready:
        auth_strategy = "service_account_json_detectada_nao_preferencial"
        alerts.append("chave_json_detectada_credencial_longa")
    else:
        auth_strategy = "credencial_google_ausente"

    if not github_oidc_available:
        alerts.append("oidc_github_nao_detectado_no_step")
    if not drive_root:
        alerts.append("google_drive_root_folder_id_ausente")
    if not drive_test:
        alerts.append("google_drive_test_folder_id_ausente")
    if not project_id:
        alerts.append("google_project_id_ausente")

    ready_for_431 = (
        github_oidc_available
        and wif_ready
        and drive_root
        and drive_test
        and project_id
    )

    if ready_for_431:
        readiness = "pronto_para_4_31_teste_real_controlado"
    elif json_ready and drive_root and drive_test:
        readiness = "pronto_parcial_com_json_nao_preferencial"
    else:
        readiness = "nao_pronto_para_upload_download_real"

    secret_rows = [
        secret_row("GOOGLE_PROJECT_ID", "ID do projeto Google Cloud", "Workload Identity e Drive API"),
        secret_row("GOOGLE_WORKLOAD_IDENTITY_PROVIDER", "Provider OIDC do Google Cloud", "Workload Identity Federation"),
        secret_row("GOOGLE_SERVICE_ACCOUNT", "Service account a ser impersonada", "Token Google para Drive API"),
        secret_row("GOOGLE_DRIVE_ROOT_FOLDER_ID", "Pasta raiz no Drive", "Upload/download operacional"),
        secret_row("GOOGLE_DRIVE_TEST_FOLDER_ID", "Pasta de teste no Drive", "Teste real seguro da 4.31"),
        secret_row("GDRIVE_SERVICE_ACCOUNT_JSON", "Chave JSON alternativa", "Plano B não preferencial"),
        {
            "secret_ou_variavel": "ACTIONS_ID_TOKEN_REQUEST_URL",
            "presente": "sim" if github_oidc_url else "nao",
            "comprimento_detectado": "oculto",
            "valor_exposto": "nao",
            "finalidade": "URL interna para solicitar token OIDC do GitHub",
            "necessario_para": "teste seco de OIDC",
        },
        {
            "secret_ou_variavel": "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
            "presente": "sim" if github_oidc_token else "nao",
            "comprimento_detectado": "oculto",
            "valor_exposto": "nao",
            "finalidade": "token interno para solicitar OIDC",
            "necessario_para": "teste seco de OIDC",
        },
    ]

    estrategia = [
        {
            "prioridade": "1",
            "estrategia": "Workload Identity Federation",
            "status": "preferencial",
            "motivo": "evita chave longa no GitHub e usa credencial temporaria por workflow",
            "requisitos": "GOOGLE_PROJECT_ID; GOOGLE_WORKLOAD_IDENTITY_PROVIDER; GOOGLE_SERVICE_ACCOUNT; id-token: write",
            "usar_na_4_31": "sim_se_configurado",
        },
        {
            "prioridade": "2",
            "estrategia": "Service Account JSON",
            "status": "alternativa_controlada",
            "motivo": "funciona, mas cria segredo longo que precisa rotação e proteção",
            "requisitos": "GDRIVE_SERVICE_ACCOUNT_JSON; GOOGLE_DRIVE_TEST_FOLDER_ID",
            "usar_na_4_31": "somente_se_WIF_nao_for_possivel",
        },
        {
            "prioridade": "3",
            "estrategia": "arquivamento manual Drive",
            "status": "fallback_atual",
            "motivo": "ja funciona operacionalmente, mas nao automatiza pipeline",
            "requisitos": "disciplina de pastas e checklist",
            "usar_na_4_31": "nao_como_api",
        },
    ]

    checklist = [
        {
            "item": "GitHub Actions com id-token write",
            "status": "sim" if github_oidc_available else "nao",
            "acao": "manter permissions: id-token: write no workflow 4.30 e 4.31",
        },
        {
            "item": "GOOGLE_PROJECT_ID configurado",
            "status": "sim" if project_id else "nao",
            "acao": "criar secret ou variable no GitHub",
        },
        {
            "item": "GOOGLE_WORKLOAD_IDENTITY_PROVIDER configurado",
            "status": "sim" if wif_provider else "nao",
            "acao": "criar provider no Google Cloud e cadastrar no GitHub",
        },
        {
            "item": "GOOGLE_SERVICE_ACCOUNT configurado",
            "status": "sim" if service_account else "nao",
            "acao": "criar/cadastrar service account com escopo minimo",
        },
        {
            "item": "GOOGLE_DRIVE_ROOT_FOLDER_ID configurado",
            "status": "sim" if drive_root else "nao",
            "acao": "cadastrar ID da pasta Fito_Mais_Amazonia",
        },
        {
            "item": "GOOGLE_DRIVE_TEST_FOLDER_ID configurado",
            "status": "sim" if drive_test else "nao",
            "acao": "cadastrar ID de pasta temporaria de teste",
        },
    ]

    plano_431 = [
        {
            "etapa": "1",
            "acao": "autenticar_google",
            "descricao": "usar google-github-actions/auth com Workload Identity Federation",
            "criterio_sucesso": "token temporario gerado sem expor segredo",
        },
        {
            "etapa": "2",
            "acao": "criar_arquivo_teste",
            "descricao": "gerar arquivo TXT pequeno no runner",
            "criterio_sucesso": "arquivo local criado e hash registrado",
        },
        {
            "etapa": "3",
            "acao": "upload_drive_pasta_teste",
            "descricao": "enviar arquivo pequeno para GOOGLE_DRIVE_TEST_FOLDER_ID",
            "criterio_sucesso": "Drive API retorna file_id",
        },
        {
            "etapa": "4",
            "acao": "download_ou_metadata",
            "descricao": "consultar metadados do arquivo enviado",
            "criterio_sucesso": "nome, tamanho e id confirmados",
        },
        {
            "etapa": "5",
            "acao": "registrar_evidencia",
            "descricao": "gravar CSV/MD com file_id mascarado parcialmente",
            "criterio_sucesso": "evidencia sem segredo e sem token",
        },
    ]

    registry = [
        {
            "rodada": "4.30",
            "pacote": "api_drive_github_dryrun",
            "estrategia_autenticacao": auth_strategy,
            "github_oidc_disponivel": "sim" if github_oidc_available else "nao",
            "wif_ready": "sim" if wif_ready else "nao",
            "json_key_detectada": "sim" if json_ready else "nao",
            "drive_root_folder_id": "sim" if drive_root else "nao",
            "drive_test_folder_id": "sim" if drive_test else "nao",
            "readiness_4_31": readiness,
            "alertas": str(len(alerts)),
            "erros_estruturais": str(len(errors)),
            "status": "gerado",
        }
    ]

    status = [
        {
            "rodada": "4.30",
            "status": "sucesso",
            "erros_estruturais": str(len(errors)),
            "alertas": str(len(alerts)),
            "api_drive_github_ativa": "nao",
            "teste_seco_autenticacao": "executado",
            "upload_drive_real": "nao",
            "download_drive_real": "nao",
            "readiness_4_31": readiness,
            "score_aimm_final": "nao_liberado",
            "proxima_rodada": "4.31",
            "proxima_rodada_descricao": "teste real controlado de upload e consulta Drive API",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_DRIVE_GITHUB_DRYRUN_4_30",
            "tipo_evidencia": "teste_seco_autenticacao",
            "descricao": "Diagnostico de prontidao para autenticacao GitHub-Google Drive sem expor segredos.",
            "status": "gerado",
            "limitacao": "Nao executa upload/download real no Drive.",
        }
    ]

    diagnostico = [
        "# Diagnóstico API GitHub-Drive — Rodada 4.30",
        "",
        "## Resultado",
        "",
        "A rodada executou teste seco de autenticação e verificou a prontidão para conexão GitHub ↔ Google Drive.",
        "",
        "## Status central",
        "",
        f"- Estratégia detectada: `{auth_strategy}`",
        f"- OIDC GitHub disponível no job: `{'sim' if github_oidc_available else 'nao'}`",
        f"- Workload Identity Federation pronta: `{'sim' if wif_ready else 'nao'}`",
        f"- Service Account JSON detectada: `{'sim' if json_ready else 'nao'}`",
        f"- Pasta raiz Drive configurada: `{'sim' if drive_root else 'nao'}`",
        f"- Pasta teste Drive configurada: `{'sim' if drive_test else 'nao'}`",
        f"- Readiness para 4.31: `{readiness}`",
        "",
        "## Trava",
        "",
        "A 4.30 não acessa Drive, não envia arquivos, não baixa arquivos e não libera score AIMM final.",
    ]

    report = [
        "# Relatório da Rodada 4.30 — estratégia segura API GitHub-Drive",
        "",
        "## O que foi feito",
        "",
        "- Verificação de secrets/variáveis necessárias.",
        "- Verificação de disponibilidade OIDC no GitHub Actions.",
        "- Classificação da estratégia de autenticação.",
        "- Preparação do plano da 4.31.",
        "",
        "## O que ainda falta para funcionar de verdade",
        "",
        "- Configurar Workload Identity Federation ou chave JSON controlada.",
        "- Cadastrar ID da pasta raiz e pasta teste do Drive.",
        "- Rodar teste real de upload/consulta na 4.31.",
        "",
        "## Status",
        "",
        f"- Readiness: `{readiness}`",
        f"- Alertas: `{len(alerts)}`",
        f"- Erros estruturais: `{len(errors)}`",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.31 — teste real controlado Drive API.",
    ]

    log = [
        "TESTE AIMM_DRIVE_GITHUB_AUTH_DRYRUN_4_30 — Fito+ Amazônia",
        "=" * 86,
        f"Estrategia de autenticacao: {auth_strategy}",
        f"GitHub OIDC disponivel no job: {'sim' if github_oidc_available else 'nao'}",
        f"GOOGLE_PROJECT_ID presente: {'sim' if project_id else 'nao'}",
        f"GOOGLE_WORKLOAD_IDENTITY_PROVIDER presente: {'sim' if wif_provider else 'nao'}",
        f"GOOGLE_SERVICE_ACCOUNT presente: {'sim' if service_account else 'nao'}",
        f"GOOGLE_DRIVE_ROOT_FOLDER_ID presente: {'sim' if drive_root else 'nao'}",
        f"GOOGLE_DRIVE_TEST_FOLDER_ID presente: {'sim' if drive_test else 'nao'}",
        f"GDRIVE_SERVICE_ACCOUNT_JSON presente: {'sim' if json_ready else 'nao'}",
        "Valores de secrets expostos no log: nao",
        f"Readiness 4.31: {readiness}",
        f"Alertas: {len(alerts)}",
        f"Erros estruturais: {len(errors)}",
        "",
        "Resultado: SUCESSO.",
        "Teste seco de autenticacao e estrategia segura Drive-GitHub gerados.",
        "",
        "Trava: nao acessa Drive, nao faz upload/download e nao libera score AIMM final.",
    ]

    write_text(FILES["diagnostico"], diagnostico)
    write_csv(FILES["secrets"], secret_rows)
    write_csv(FILES["estrategia"], estrategia)
    write_csv(FILES["checklist"], checklist)
    write_csv(FILES["plano_431"], plano_431)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["status"], status)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log))


if __name__ == "__main__":
    main()
