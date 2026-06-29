from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"

# Códigos municipais IBGE usados no projeto Fito+ Amazônia.
# Manaus/AM: 1302603
# Benjamin Constant/AM: 1300607
# Belém/PA: 1501402
# Santarém/PA: 1506807
MUNICIPIOS_PROJETO = {
    "1302603": {"municipio": "Manaus", "uf": "AM"},
    "1300607": {"municipio": "Benjamin Constant", "uf": "AM"},
    "1501402": {"municipio": "Belém", "uf": "PA"},
    "1506807": {"municipio": "Santarém", "uf": "PA"},
}


@dataclass
class ResultadoColeta:
    id_coleta: str
    fonte: str
    endpoint: str
    parametros: str
    indicador_relacionado: str
    territorio: str
    status_http: int | str
    status_coleta: str
    linhas_extraidas: int
    arquivo_saida: str
    mensagem_erro: str = ""
    observacoes: str = ""


def agora_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def montar_url_sidra_populacao_estimada(
    codigos_municipios: list[str] | None = None,
    periodo: str = "last",
) -> str:
    """Monta URL da tabela SIDRA 6579, variável 9324: população residente estimada.

    Padrão SIDRA usado:
    https://apisidra.ibge.gov.br/values/t/6579/n6/<municipios>/v/9324/p/<periodo>?formato=json
    """
    codigos = codigos_municipios or list(MUNICIPIOS_PROJETO.keys())
    municipios = ",".join(codigos)
    return f"{SIDRA_BASE_URL}/t/6579/n6/{municipios}/v/9324/p/{periodo}?formato=json"


def requisitar_json(url: str, timeout: int = 40) -> tuple[int, Any]:
    resposta = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "fito-aimm-amazonia/0.1 (+github-actions)",
            "Accept": "application/json",
        },
    )
    status = resposta.status_code
    resposta.raise_for_status()
    return status, resposta.json()


def transformar_sidra_flat(dados_json: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Transforma resposta JSON do SIDRA em linhas tabulares.

    A API SIDRA normalmente retorna a primeira linha como cabeçalho.
    O coletor preserva metadados essenciais e padroniza município/UF.
    """
    if not isinstance(dados_json, list) or len(dados_json) < 2:
        raise ValueError("Resposta SIDRA vazia ou em formato inesperado.")

    cabecalho = dados_json[0]
    linhas = dados_json[1:]

    saida = []
    for item in linhas:
        codigo_municipio = str(item.get("D1C", "")).strip()
        municipio_api = str(item.get("D1N", "")).strip()
        valor = str(item.get("V", "")).strip()
        ano = str(item.get("D2N", item.get("D2C", ""))).strip()

        territorio_padrao = MUNICIPIOS_PROJETO.get(codigo_municipio, {})
        municipio = territorio_padrao.get("municipio", municipio_api)
        uf = territorio_padrao.get("uf", "")

        saida.append({
            "id_indicador": "GAP_TERR_01",
            "fonte": "SRC_IBGE_API",
            "tabela_sidra": "6579",
            "variavel_sidra": "9324",
            "nome_variavel": "População residente estimada",
            "codigo_municipio_ibge": codigo_municipio,
            "municipio": municipio,
            "uf": uf,
            "ano": ano,
            "valor": valor,
            "unidade": "pessoas",
            "observacao": "Coleta automatizada inicial usada como teste de conectividade IBGE/SIDRA; indicador territorial de referência, não substitui recorte específico de agricultores familiares.",
        })

    return saida


def salvar_csv(caminho: Path, linhas: list[dict[str, str]], delimiter: str = ";") -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if not linhas:
        raise ValueError(f"Nenhuma linha para salvar em {caminho}")

    campos = list(linhas[0].keys())
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=delimiter)
        escritor.writeheader()
        escritor.writerows(linhas)


def registrar_fetch_log(caminho: Path, resultado: ResultadoColeta) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)

    campos = [
        "id_coleta",
        "data_hora_utc",
        "fonte",
        "endpoint",
        "parametros",
        "indicador_relacionado",
        "territorio",
        "status_http",
        "status_coleta",
        "linhas_extraidas",
        "arquivo_saida",
        "mensagem_erro",
        "observacoes",
    ]

    arquivo_existe = caminho.exists()
    with caminho.open("a", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        if not arquivo_existe or caminho.stat().st_size == 0:
            escritor.writeheader()

        escritor.writerow({
            "id_coleta": resultado.id_coleta,
            "data_hora_utc": agora_utc_iso(),
            "fonte": resultado.fonte,
            "endpoint": resultado.endpoint,
            "parametros": resultado.parametros,
            "indicador_relacionado": resultado.indicador_relacionado,
            "territorio": resultado.territorio,
            "status_http": resultado.status_http,
            "status_coleta": resultado.status_coleta,
            "linhas_extraidas": resultado.linhas_extraidas,
            "arquivo_saida": resultado.arquivo_saida,
            "mensagem_erro": resultado.mensagem_erro,
            "observacoes": resultado.observacoes,
        })


def coletar_populacao_estimada_municipios(
    arquivo_saida: Path = Path("data/raw/ibge/populacao_estimada_municipios.csv"),
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
    periodo: str = "last",
) -> list[dict[str, str]]:
    """Executa a primeira coleta real IBGE/SIDRA do projeto.

    Objetivo: testar conectividade, parsing, normalização territorial e registro de log.
    Produto: CSV com população estimada dos quatro municípios do Fito+ Amazônia.
    """
    id_coleta = f"IBGE_SIDRA_6579_9324_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    url = montar_url_sidra_populacao_estimada(periodo=periodo)
    parametros = json.dumps({
        "tabela": "6579",
        "variavel": "9324",
        "periodo": periodo,
        "municipios": list(MUNICIPIOS_PROJETO.keys()),
    }, ensure_ascii=False)

    try:
        status_http, dados_json = requisitar_json(url)
        linhas = transformar_sidra_flat(dados_json)

        codigos_obtidos = {linha["codigo_municipio_ibge"] for linha in linhas}
        codigos_esperados = set(MUNICIPIOS_PROJETO.keys())
        faltantes = sorted(codigos_esperados - codigos_obtidos)
        if faltantes:
            raise ValueError(f"Municípios ausentes na resposta SIDRA: {faltantes}")

        salvar_csv(arquivo_saida, linhas)

        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_IBGE_API",
                endpoint=url,
                parametros=parametros,
                indicador_relacionado="GAP_TERR_01",
                territorio="Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
                status_http=status_http,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas),
                arquivo_saida=str(arquivo_saida),
                observacoes="Primeira coleta real automatizada IBGE/SIDRA da calculadora.",
            )
        )

        return linhas

    except Exception as erro:
        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_IBGE_API",
                endpoint=url,
                parametros=parametros,
                indicador_relacionado="GAP_TERR_01",
                territorio="Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
                status_http="erro",
                status_coleta="falha",
                linhas_extraidas=0,
                arquivo_saida=str(arquivo_saida),
                mensagem_erro=str(erro),
                observacoes="Falha na coleta automatizada IBGE/SIDRA.",
            )
        )
        raise
