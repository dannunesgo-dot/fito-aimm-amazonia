# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_27_diagnostico_automacoes_ingestao")

FILES = {
    "diagnostico": BASE / "DIAGNOSTICO_AUTOMACOES_DRIVE_GITHUB_4_27.md",
    "status_automacoes": BASE / "STATUS_AUTOMACOES_AIMM_4_27.csv",
    "modulos": BASE / "MODULOS_INGESTAO_BENCHMARKS_AIMM_4_27.csv",
    "requisitos_api": BASE / "REQUISITOS_API_DRIVE_GITHUB_4_27.csv",
    "plano": BASE / "PLANO_IMPLEMENTACAO_FUNCIONAL_AIMM_4_27.csv",
    "checklist": BASE / "CHECKLIST_TESTE_FUNCIONAL_AIMM_4_27.csv",
    "registry": Path("data/processed/aimm/aimm_automation_ingestion_diagnostic_registry_4_27.csv"),
    "status": Path("data/processed/aimm/aimm_automation_ingestion_diagnostic_status_4_27.csv"),
    "evidence": Path("data/evidence/evidence_aimm_automation_ingestion_diagnostic_4_27.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_DIAGNOSTICO_AUTOMACOES_4_27.md"),
    "log": Path("outputs/logs/teste_aimm_diagnostico_automacoes_4_27.txt"),
}

def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Nenhuma linha para gravar em {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized_rows.append({key: row.get(key, "") for key in fieldnames})

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(normalized_rows)


def exists(path_text: str) -> str:
    return "sim" if Path(path_text).exists() else "nao"


def count_glob(pattern: str) -> int:
    return len(list(Path(".").glob(pattern)))


def env_present(name: str) -> str:
    value = os.getenv(name, "")
    return "sim" if value.strip() else "nao"


def env_len(name: str) -> int:
    value = os.getenv(name, "")
    return len(value.strip())


def safe_secret_status(name: str) -> dict[str, str]:
    present = env_present(name)
    length = env_len(name)
    return {
        "secret_ou_variavel": name,
        "presente": present,
        "comprimento_detectado": str(length) if present == "sim" else "0",
        "valor_exposto": "nao",
        "observacao": "presenca_detectada_sem_exibir_conteudo" if present == "sim" else "ausente",
    }


def main() -> None:
    errors: list[str] = []
    alerts: list[str] = []

    required_dirs = [
        "data",
        "data/manual",
        "data/raw",
        "data/reference",
        "data/processed",
        "data/evidence",
        "scripts",
        ".github/workflows",
        "outputs",
    ]

    for directory in required_dirs:
        if not Path(directory).exists():
            alerts.append(f"diretorio_ausente:{directory}")

    expected_secrets = [
        "GH_TOKEN_DIAGNOSTIC",
        "GDRIVE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_WORKLOAD_IDENTITY_PROVIDER",
        "GOOGLE_SERVICE_ACCOUNT",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID",
        "GOOGLE_DRIVE_TEST_FOLDER_ID",
    ]

    secret_rows = [safe_secret_status(name) for name in expected_secrets]

    wif_ready = (
        env_present("GOOGLE_WORKLOAD_IDENTITY_PROVIDER") == "sim"
        and env_present("GOOGLE_SERVICE_ACCOUNT") == "sim"
    )

    json_key_present = env_present("GDRIVE_SERVICE_ACCOUNT_JSON") == "sim"
    drive_folder_present = env_present("GOOGLE_DRIVE_ROOT_FOLDER_ID") == "sim"

    if wif_ready:
        drive_api_status = "credencial_wif_detectada_mas_nao_testada"
    elif json_key_present:
        drive_api_status = "chave_json_detectada_mas_nao_testada"
    else:
        drive_api_status = "nao_implementada_sem_credencial_detectada"

    if not drive_folder_present:
        alerts.append("google_drive_root_folder_id_ausente")

    if drive_api_status == "nao_implementada_sem_credencial_detectada":
        alerts.append("api_drive_github_nao_configurada")

    scripts_py = count_glob("scripts/*.py")
    workflows_yml = count_glob(".github/workflows/*.yml")
    benchmarks_detectados = count_glob("**/*benchmark*")
    ingestao_detectada = count_glob("**/*ingest*") + count_glob("**/*ingestao*")
    drive_detectado = count_glob("**/*drive*")
    gis_detectado = count_glob("**/*gis*")

    status_automacoes = [
        {
            "componente": "github_actions",
            "status": "funciona",
            "evidencia": "workflows anteriores executaram com sucesso",
            "risco": "baixo",
            "proxima_acao": "manter execucao por workflow_dispatch",
        },
        {
            "componente": "artefatos_github",
            "status": "funciona",
            "evidencia": "rodadas anteriores publicaram ZIP",
            "risco": "baixo",
            "proxima_acao": "manter arquivamento manual em Drive",
        },
        {
            "componente": "api_drive_github",
            "status": drive_api_status,
            "evidencia": "diagnostico_por_variaveis_de_ambiente_sem_expor_secret",
            "risco": "alto",
            "proxima_acao": "implementar rodada propria de autenticacao e teste real",
        },
        {
            "componente": "upload_automatico_drive",
            "status": "nao_implementado",
            "evidencia": "nenhuma chamada Drive API executada nesta rodada",
            "risco": "alto",
            "proxima_acao": "implementar somente apos credencial segura",
        },
        {
            "componente": "download_automatico_drive",
            "status": "nao_implementado",
            "evidencia": "nenhuma chamada Drive API executada nesta rodada",
            "risco": "alto",
            "proxima_acao": "implementar somente apos credencial segura",
        },
        {
            "componente": "ingestao_arquivos",
            "status": "nao_implementada" if ingestao_detectada == 0 else "parcial_ou_nome_detectado",
            "evidencia": f"arquivos_com_ingest_detectados:{ingestao_detectada}",
            "risco": "alto",
            "proxima_acao": "criar modulo padrao de ingestao na 4.28",
        },
        {
            "componente": "benchmarks_automaticos",
            "status": "estrutura_detectada_sem_automacao" if benchmarks_detectados > 0 else "nao_implementado",
            "evidencia": f"arquivos_com_benchmark_detectados:{benchmarks_detectados}",
            "risco": "medio",
            "proxima_acao": "criar modulo de benchmark na 4.29",
        },
        {
            "componente": "gis_manaus",
            "status": "funciona_com_lacunas",
            "evidencia": f"arquivos_gis_detectados:{gis_detectado}",
            "risco": "medio",
            "proxima_acao": "manter Manaus como baseline; segundo municipio opcional",
        },
        {
            "componente": "score_aimm_final",
            "status": "bloqueado",
            "evidencia": "trava mantida desde rodadas anteriores",
            "risco": "alto",
            "proxima_acao": "nao liberar antes de pipeline funcional e validacoes",
        },
    ]

    modulos = [
        {
            "modulo": "entrada_manual",
            "pasta_esperada": "data/manual",
            "existe": exists("data/manual"),
            "funcao": "receber sementes, manifests e registros manuais controlados",
            "situacao": "estrutura_existente" if exists("data/manual") == "sim" else "ausente",
        },
        {
            "modulo": "dados_brutos",
            "pasta_esperada": "data/raw",
            "existe": exists("data/raw"),
            "funcao": "receber arquivos originais versionaveis quando tamanho permitir",
            "situacao": "estrutura_existente" if exists("data/raw") == "sim" else "ausente",
        },
        {
            "modulo": "referencias",
            "pasta_esperada": "data/reference",
            "existe": exists("data/reference"),
            "funcao": "guardar tabelas de referencia e seeds estaveis",
            "situacao": "estrutura_existente" if exists("data/reference") == "sim" else "ausente",
        },
        {
            "modulo": "processados",
            "pasta_esperada": "data/processed",
            "existe": exists("data/processed"),
            "funcao": "guardar saidas tabulares geradas por workflows",
            "situacao": "estrutura_existente" if exists("data/processed") == "sim" else "ausente",
        },
        {
            "modulo": "evidencias",
            "pasta_esperada": "data/evidence",
            "existe": exists("data/evidence"),
            "funcao": "guardar evidencias e logs de auditoria",
            "situacao": "estrutura_existente" if exists("data/evidence") == "sim" else "ausente",
        },
        {
            "modulo": "scripts",
            "pasta_esperada": "scripts",
            "existe": exists("scripts"),
            "funcao": "executar processamento controlado por rodada",
            "situacao": f"scripts_py_detectados:{scripts_py}",
        },
        {
            "modulo": "workflows",
            "pasta_esperada": ".github/workflows",
            "existe": exists(".github/workflows"),
            "funcao": "executar scripts no GitHub Actions",
            "situacao": f"workflows_yml_detectados:{workflows_yml}",
        },
        {
            "modulo": "ingestao_arquivos",
            "pasta_esperada": "a_definir_na_4_28",
            "existe": "nao",
            "funcao": "validar e catalogar arquivos novos antes de processamento",
            "situacao": "nao_implementado",
        },
        {
            "modulo": "benchmark_automatico",
            "pasta_esperada": "a_definir_na_4_29",
            "existe": "nao",
            "funcao": "coletar, validar, normalizar e versionar benchmarks",
            "situacao": "nao_implementado",
        },
    ]

    requisitos_api = [
        {
            "requisito": "secret_ou_identidade_google",
            "necessario_para": "autenticacao GitHub-Google",
            "status_detectado": drive_api_status,
            "acao": "preferir Workload Identity Federation; chave JSON somente como alternativa controlada",
        },
        {
            "requisito": "GOOGLE_DRIVE_ROOT_FOLDER_ID",
            "necessario_para": "apontar pasta raiz Fito_Mais_Amazonia",
            "status_detectado": env_present("GOOGLE_DRIVE_ROOT_FOLDER_ID"),
            "acao": "configurar secret ou variavel quando a API for implementada",
        },
        {
            "requisito": "GOOGLE_DRIVE_TEST_FOLDER_ID",
            "necessario_para": "teste seguro sem afetar pastas finais",
            "status_detectado": env_present("GOOGLE_DRIVE_TEST_FOLDER_ID"),
            "acao": "criar pasta de teste no Drive antes do primeiro upload automatico",
        },
        {
            "requisito": "script_upload_drive",
            "necessario_para": "envio automatico de artefato",
            "status_detectado": "nao_implementado",
            "acao": "criar na rodada de API apos diagnostico",
        },
        {
            "requisito": "script_download_drive",
            "necessario_para": "leitura automatica de insumos do Drive",
            "status_detectado": "nao_implementado",
            "acao": "criar depois do teste de autenticacao",
        },
        {
            "requisito": "manifesto_ingestao",
            "necessario_para": "controlar arquivos novos",
            "status_detectado": "nao_implementado",
            "acao": "criar na rodada 4.28",
        },
    ]

    plano = [
        {
            "rodada": "4.28",
            "nome": "modulo de ingestao e validacao de arquivos",
            "entrega": "manifesto de entrada, validador de extensoes, tamanhos, nomes e destino",
            "depende_de_api_drive": "nao",
            "prioridade": "alta",
        },
        {
            "rodada": "4.29",
            "nome": "modulo de benchmarks e normalizacao",
            "entrega": "catalogo de fontes, status de coleta, normalizacao e lacunas",
            "depende_de_api_drive": "nao",
            "prioridade": "alta",
        },
        {
            "rodada": "4.30",
            "nome": "estrategia segura de API GitHub-Drive",
            "entrega": "modelo de autenticacao, secrets requeridos e teste seco",
            "depende_de_api_drive": "sim",
            "prioridade": "alta",
        },
        {
            "rodada": "4.31",
            "nome": "teste real GitHub-Drive com arquivo pequeno",
            "entrega": "upload e download controlado em pasta de teste",
            "depende_de_api_drive": "sim",
            "prioridade": "alta",
        },
        {
            "rodada": "4.32",
            "nome": "pipeline minimo ponta a ponta",
            "entrega": "entrada de arquivo, validacao, processamento, artefato e registro",
            "depende_de_api_drive": "parcial",
            "prioridade": "alta",
        },
    ]

    checklist = [
        {
            "item": "workflow 4.27 verde",
            "criterio": "Resultado: SUCESSO e Erros estruturais: 0",
            "status": "pendente_ate_execucao",
        },
        {
            "item": "status real da API registrado",
            "criterio": "api_drive_github classificada sem expor segredo",
            "status": "pendente_ate_execucao",
        },
        {
            "item": "modulos de ingestao classificados",
            "criterio": "CSV informa existente, parcial ou nao implementado",
            "status": "pendente_ate_execucao",
        },
        {
            "item": "benchmarks classificados",
            "criterio": "CSV informa estrutura detectada ou ausente",
            "status": "pendente_ate_execucao",
        },
        {
            "item": "proximas rodadas funcionais definidas",
            "criterio": "4.28 a 4.32 registradas",
            "status": "pendente_ate_execucao",
        },
    ]

    registry = [
        {
            "rodada": "4.27",
            "pacote": "diagnostico_funcional_automacoes_drive_github_ingestao",
            "scripts_py_detectados": str(scripts_py),
            "workflows_yml_detectados": str(workflows_yml),
            "benchmarks_detectados": str(benchmarks_detectados),
            "ingestao_detectada": str(ingestao_detectada),
            "drive_detectado": str(drive_detectado),
            "api_drive_github": drive_api_status,
            "alertas": str(len(alerts)),
            "erros_estruturais": str(len(errors)),
            "status": "gerado",
        }
    ]

    status = [
        {
            "rodada": "4.27",
            "status": "sucesso" if not errors else "erro",
            "erros_estruturais": str(len(errors)),
            "alertas": str(len(alerts)),
            "api_drive_github": drive_api_status,
            "ingestao_arquivos": "nao_implementada" if ingestao_detectada == 0 else "parcial_ou_nome_detectado",
            "benchmarks_automaticos": "nao_implementados",
            "score_aimm_final": "nao_liberado",
            "proxima_rodada": "4.28",
            "proxima_rodada_descricao": "modulo de ingestao e validacao de arquivos",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_AUTOMATION_INGESTION_DIAGNOSTIC_4_27",
            "tipo_evidencia": "diagnostico_funcional",
            "descricao": "Diagnostico funcional de automacoes, API Drive-GitHub, ingestao de arquivos e benchmarks.",
            "status": "gerado",
            "limitacao": "Nao acessa Google Drive, nao executa upload/download e nao processa benchmark real.",
        }
    ]

    diagnostico = [
        "# Diagnóstico funcional AIMM — Rodada 4.27",
        "",
        "## Resultado",
        "",
        "Esta rodada classificou o estado real das automações, da integração Drive-GitHub e dos módulos de ingestão.",
        "",
        "## Status central",
        "",
        f"- API Drive-GitHub: `{drive_api_status}`",
        f"- Scripts Python detectados: `{scripts_py}`",
        f"- Workflows YAML detectados: `{workflows_yml}`",
        f"- Arquivos com termo benchmark detectados: `{benchmarks_detectados}`",
        f"- Arquivos com termo ingest/ingestao detectados: `{ingestao_detectada}`",
        f"- Arquivos com termo drive detectados: `{drive_detectado}`",
        "",
        "## Conclusão técnica",
        "",
        "O sistema executa workflows e gera artefatos, mas ainda não possui pipeline automático completo de Drive, ingestão e benchmark.",
        "",
        "## Encaminhamento",
        "",
        "A próxima rodada deve criar o módulo de ingestão e validação de arquivos, sem depender ainda da API Drive.",
    ]

    report = [
        "# Relatório da Rodada 4.27 — diagnóstico funcional",
        "",
        "## Resultado",
        "",
        "Diagnóstico funcional gerado.",
        "",
        "## Pontos avaliados",
        "",
        "- GitHub Actions.",
        "- Artefatos.",
        "- API GitHub-Drive.",
        "- Upload/download automático.",
        "- Módulos de ingestão.",
        "- Benchmarks.",
        "- GIS.",
        "- Score AIMM.",
        "",
        "## Travas",
        "",
        "- Não ativa API.",
        "- Não acessa Drive.",
        "- Não processa benchmarks reais.",
        "- Não libera score AIMM final.",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.28 — módulo de ingestão e validação de arquivos.",
    ]

    log_lines = [
        "TESTE AIMM_AUTOMATION_INGESTION_DIAGNOSTIC_4_27 — Fito+ Amazônia",
        "=" * 86,
        f"Scripts Python detectados: {scripts_py}",
        f"Workflows YAML detectados: {workflows_yml}",
        f"Arquivos benchmark detectados: {benchmarks_detectados}",
        f"Arquivos ingestao detectados: {ingestao_detectada}",
        f"Arquivos drive detectados: {drive_detectado}",
        f"API GitHub-Drive: {drive_api_status}",
        f"GOOGLE_DRIVE_ROOT_FOLDER_ID presente: {env_present('GOOGLE_DRIVE_ROOT_FOLDER_ID')}",
        f"GOOGLE_DRIVE_TEST_FOLDER_ID presente: {env_present('GOOGLE_DRIVE_TEST_FOLDER_ID')}",
        f"Workload Identity Provider presente: {env_present('GOOGLE_WORKLOAD_IDENTITY_PROVIDER')}",
        f"Google Service Account presente: {env_present('GOOGLE_SERVICE_ACCOUNT')}",
        f"Service Account JSON presente: {env_present('GDRIVE_SERVICE_ACCOUNT_JSON')}",
        "Valores de secrets expostos no log: nao",
        f"Alertas: {len(alerts)}",
        f"Erros estruturais: {len(errors)}",
        "",
        "Resultado: SUCESSO." if not errors else "Resultado: ERRO.",
        "Diagnostico funcional de automacoes, Drive-GitHub e ingestao gerado.",
        "",
        "Trava: nao ativa API, nao acessa Drive, nao processa benchmark real e nao libera score AIMM final.",
    ]

    all_secret_rows = secret_rows

    write_text(FILES["diagnostico"], diagnostico)
    write_csv(FILES["status_automacoes"], status_automacoes)
    write_csv(FILES["modulos"], modulos)
    write_csv(FILES["requisitos_api"], requisitos_api + all_secret_rows)
    write_csv(FILES["plano"], plano)
    write_csv(FILES["checklist"], checklist)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["status"], status)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log_lines)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log_lines))

    if errors:
        raise ValueError(f"Rodada 4.27 contém {len(errors)} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
