from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"
LOCALIDADES_BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
MAX_CONCURRENT_LOCALIDADES_REQUESTS = 4

from .territorios import (
    carregar_municipios_projeto,
    descrever_territorios_projeto,
    listar_codigos_municipios_projeto,
)


MUNICIPIOS_PROJETO = carregar_municipios_projeto()
CODIGOS_MUNICIPIOS_PROJETO = listar_codigos_municipios_projeto()
TERRITORIO_PROJETO = descrever_territorios_projeto()


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


def requisitar_json(url: str, timeout: int = 40) -> tuple[int, Any]:
    resposta = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "fito-aimm-amazonia/0.3 (+github-actions)",
            "Accept": "application/json",
        },
    )
    status = resposta.status_code
    resposta.raise_for_status()
    return status, resposta.json()


def salvar_csv(caminho: Path, linhas: list[dict[str, Any]], delimiter: str = ";") -> None:
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


def montar_url_sidra_populacao_estimada(
    codigos_municipios: list[str] | None = None,
    periodo: str = "last",
) -> str:
    codigos = codigos_municipios or CODIGOS_MUNICIPIOS_PROJETO
    municipios = ",".join(codigos)
    return f"{SIDRA_BASE_URL}/t/6579/n6/{municipios}/v/9324/p/{periodo}?formato=json"


def transformar_sidra_flat(dados_json: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not isinstance(dados_json, list) or len(dados_json) < 2:
        raise ValueError("Resposta SIDRA vazia ou em formato inesperado.")

    linhas = dados_json[1:]
    saida = []

    for item in linhas:
        codigo_municipio = str(item.get("D1C", "")).strip()
        municipio_api = str(item.get("D1N", "")).strip()
        valor = str(item.get("V", "")).strip()

        # A API pode retornar o período em diferentes colunas conforme a consulta.
        ano = (
            str(item.get("D2N", "")).strip()
            or str(item.get("D2C", "")).strip()
            or str(item.get("D3N", "")).strip()
            or str(item.get("D3C", "")).strip()
        )

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
            "observacao": "Coleta automatizada IBGE/SIDRA; dado territorial de referência.",
        })

    return saida


def coletar_populacao_estimada_municipios(
    arquivo_saida: Path = Path("data/raw/ibge/populacao_estimada_municipios.csv"),
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
    periodo: str = "last",
) -> list[dict[str, str]]:
    id_coleta = f"IBGE_SIDRA_6579_9324_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    url = montar_url_sidra_populacao_estimada(periodo=periodo)
    parametros = json.dumps({
        "tabela": "6579",
        "variavel": "9324",
        "periodo": periodo,
        "municipios": CODIGOS_MUNICIPIOS_PROJETO,
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
                territorio=TERRITORIO_PROJETO,
                status_http=status_http,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas),
                arquivo_saida=str(arquivo_saida),
                observacoes="Coleta automatizada IBGE/SIDRA de população estimada.",
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
                territorio=TERRITORIO_PROJETO,
                status_http="erro",
                status_coleta="falha",
                linhas_extraidas=0,
                arquivo_saida=str(arquivo_saida),
                mensagem_erro=str(erro),
                observacoes="Falha na coleta automatizada IBGE/SIDRA.",
            )
        )
        raise


def _get_nested(dicionario: dict[str, Any], caminho: list[str], default: str = "") -> str:
    atual: Any = dicionario
    for chave in caminho:
        if not isinstance(atual, dict):
            return default
        atual = atual.get(chave)
    if atual is None:
        return default
    return str(atual)


def montar_url_localidade_municipio(codigo_municipio: str) -> str:
    return f"{LOCALIDADES_BASE_URL}/municipios/{codigo_municipio}"


def transformar_localidade_municipio(dados: dict[str, Any]) -> dict[str, str]:
    codigo = str(dados.get("id", "")).strip()
    nome = str(dados.get("nome", "")).strip()
    microrregiao = dados.get("microrregiao") or {}
    mesorregiao = microrregiao.get("mesorregiao") or {}
    uf = mesorregiao.get("UF") or {}
    regiao = uf.get("regiao") or {}
    regiao_imediata = dados.get("regiao-imediata") or {}
    regiao_intermediaria = regiao_imediata.get("regiao-intermediaria") or {}

    esperado = MUNICIPIOS_PROJETO.get(codigo, {})

    return {
        "codigo_municipio_ibge": codigo,
        "municipio": esperado.get("municipio", nome),
        "municipio_nome_api": nome,
        "uf_sigla": str(uf.get("sigla", esperado.get("uf", ""))).strip(),
        "uf_nome": str(uf.get("nome", "")).strip(),
        "regiao_id": str(regiao.get("id", "")).strip(),
        "regiao_sigla": str(regiao.get("sigla", "")).strip(),
        "regiao_nome": str(regiao.get("nome", "")).strip(),
        "microrregiao_id": str(microrregiao.get("id", "")).strip(),
        "microrregiao_nome": str(microrregiao.get("nome", "")).strip(),
        "mesorregiao_id": str(mesorregiao.get("id", "")).strip(),
        "mesorregiao_nome": str(mesorregiao.get("nome", "")).strip(),
        "regiao_imediata_id": str(regiao_imediata.get("id", "")).strip(),
        "regiao_imediata_nome": str(regiao_imediata.get("nome", "")).strip(),
        "regiao_intermediaria_id": str(regiao_intermediaria.get("id", "")).strip(),
        "regiao_intermediaria_nome": str(regiao_intermediaria.get("nome", "")).strip(),
        "fonte": "SRC_IBGE_API",
        "observacao": "API IBGE Localidades; hierarquia político-administrativa e regional.",
    }


def coletar_localidades_municipios(
    arquivo_saida: Path = Path("data/raw/ibge/localidades_municipios.csv"),
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
) -> list[dict[str, str]]:
    id_coleta = f"IBGE_LOCALIDADES_MUNICIPIOS_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    codigos = CODIGOS_MUNICIPIOS_PROJETO
    urls = {codigo: montar_url_localidade_municipio(codigo) for codigo in codigos}
    linhas_por_codigo: dict[str, dict[str, str]] = {}

    def coletar_localidade(codigo: str, url: str) -> tuple[str, dict[str, str]]:
        try:
            _, dados_json = requisitar_json(url)
        except Exception as erro:
            raise RuntimeError(f"Falha ao consultar município {codigo} em {url}") from erro
        return codigo, transformar_localidade_municipio(dados_json)

    try:
        max_workers = max(1, min(MAX_CONCURRENT_LOCALIDADES_REQUESTS, len(codigos)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futuros = [
                executor.submit(coletar_localidade, codigo, urls[codigo])
                for codigo in codigos
            ]
            for futuro in futuros:
                codigo, linha = futuro.result()
                linhas_por_codigo[codigo] = linha

        linhas = [linhas_por_codigo[codigo] for codigo in codigos]
        codigos_obtidos = set(linhas_por_codigo)
        codigos_esperados = set(codigos)
        faltantes = sorted(codigos_esperados - codigos_obtidos)
        if faltantes:
            raise ValueError(f"Municípios ausentes na resposta Localidades: {faltantes}")

        salvar_csv(arquivo_saida, linhas)

        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_IBGE_API",
                endpoint=" | ".join(urls.values()),
                parametros=json.dumps({"municipios": CODIGOS_MUNICIPIOS_PROJETO}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_01; GAP_TERR_04; GAP_TERR_06",
                territorio=TERRITORIO_PROJETO,
                status_http=200,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas),
                arquivo_saida=str(arquivo_saida),
                observacoes=f"Coleta automatizada IBGE Localidades em paralelo ({max_workers} workers).",
            )
        )

        return linhas

    except Exception as erro:
        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_IBGE_API",
                endpoint=" | ".join(urls.values()) if urls else "API Localidades",
                parametros=json.dumps({"municipios": CODIGOS_MUNICIPIOS_PROJETO}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_01; GAP_TERR_04; GAP_TERR_06",
                territorio=TERRITORIO_PROJETO,
                status_http="erro",
                status_coleta="falha",
                linhas_extraidas=0,
                arquivo_saida=str(arquivo_saida),
                mensagem_erro=str(erro),
                observacoes="Falha na coleta automatizada IBGE Localidades.",
            )
        )
        raise


def montar_baseline_territorial_ibge(
    arquivo_populacao: Path = Path("data/raw/ibge/populacao_estimada_municipios.csv"),
    arquivo_localidades: Path = Path("data/raw/ibge/localidades_municipios.csv"),
    arquivo_saida: Path = Path("data/processed/territorios_ibge_baseline.csv"),
) -> list[dict[str, str]]:
    def ler_csv_dict(caminho: Path) -> list[dict[str, str]]:
        with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
            return list(csv.DictReader(arquivo, delimiter=";"))

    populacao = ler_csv_dict(arquivo_populacao)
    localidades = ler_csv_dict(arquivo_localidades)

    pop_por_codigo = {linha["codigo_municipio_ibge"]: linha for linha in populacao}
    loc_por_codigo = {linha["codigo_municipio_ibge"]: linha for linha in localidades}

    saida = []
    for codigo, esperado in MUNICIPIOS_PROJETO.items():
        pop = pop_por_codigo.get(codigo, {})
        loc = loc_por_codigo.get(codigo, {})

        saida.append({
            "codigo_municipio_ibge": codigo,
            "municipio": esperado["municipio"],
            "uf": esperado["uf"],
            "regiao_nome": loc.get("regiao_nome", ""),
            "regiao_sigla": loc.get("regiao_sigla", ""),
            "uf_nome": loc.get("uf_nome", ""),
            "regiao_imediata_nome": loc.get("regiao_imediata_nome", ""),
            "regiao_intermediaria_nome": loc.get("regiao_intermediaria_nome", ""),
            "microrregiao_nome": loc.get("microrregiao_nome", ""),
            "mesorregiao_nome": loc.get("mesorregiao_nome", ""),
            "populacao_estimada": pop.get("valor", ""),
            "ano_populacao_estimada": pop.get("ano", ""),
            "unidade_populacao": pop.get("unidade", "pessoas"),
            "fonte_populacao": "SRC_IBGE_API",
            "fonte_localidade": "SRC_IBGE_API",
            "status_baseline": "coletado",
            "observacao": "Baseline territorial IBGE/SIDRA + Localidades. Área territorial, densidade e ruralidade serão incorporadas em rodada posterior com tabelas/arquivos específicos confirmados.",
        })

    salvar_csv(arquivo_saida, saida)
    return saida


def gerar_evidencias_ibge_territorios(
    baseline: list[dict[str, str]],
    arquivo_saida: Path = Path("data/evidence/evidence_ibge_territorios.csv"),
) -> list[dict[str, str]]:
    evidencias = []
    data_coleta = agora_utc_iso()

    for linha in baseline:
        evidencias.append({
            "id_evidencia": f"EVD_IBGE_TERR_{linha['codigo_municipio_ibge']}",
            "id_fonte": "SRC_IBGE_API",
            "id_indicador": "GAP_TERR_01",
            "tipo_evidencia": "dado_api",
            "pergunta_ou_lacuna": "Qual é a população estimada e a hierarquia territorial do município?",
            "url_ou_arquivo": "data/processed/territorios_ibge_baseline.csv",
            "titulo_documento": "Baseline territorial IBGE/SIDRA e Localidades",
            "pagina_tabela_secao": "SIDRA tabela 6579 variável 9324; API Localidades município por identificador",
            "trecho_original_ou_descricao": f"{linha['municipio']}/{linha['uf']}: população estimada {linha['populacao_estimada']} pessoas; região {linha['regiao_nome']}; região imediata {linha['regiao_imediata_nome']}.",
            "resumo_ptbr": "Dado coletado automaticamente para linha de base territorial do projeto Fito+ Amazônia.",
            "valor_extraido": linha["populacao_estimada"],
            "unidade": "pessoas",
            "periodo_referencia": linha["ano_populacao_estimada"],
            "territorio": f"{linha['municipio']}/{linha['uf']}",
            "metodo_extracao": "API IBGE/SIDRA + API IBGE Localidades",
            "nivel_confianca": "alto",
            "data_coleta": data_coleta,
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "conferido",
            "limitacoes": "População municipal é proxy territorial geral; não mede agricultores familiares, ruralidade ou renda.",
            "uso_na_calculadora": "Linha de base territorial e teste ampliado de coleta automatizada.",
            "status_evidencia": "validada",
        })

    salvar_csv(arquivo_saida, evidencias)
    return evidencias


def executar_pipeline_baseline_ibge(
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
) -> dict[str, Any]:
    populacao = coletar_populacao_estimada_municipios(arquivo_log=arquivo_log)
    localidades = coletar_localidades_municipios(arquivo_log=arquivo_log)
    baseline = montar_baseline_territorial_ibge()
    evidencias = gerar_evidencias_ibge_territorios(baseline)

    return {
        "populacao": populacao,
        "localidades": localidades,
        "baseline": baseline,
        "evidencias": evidencias,
    }
