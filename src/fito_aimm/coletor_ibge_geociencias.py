from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


AREA_XLS_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/areas_territoriais/2025/AR_BR_RG_UF_RGINT_RGI_MUN_2025.xls"
AREA_XLS_RAW = Path("data/raw/ibge/geociencias/AR_BR_RG_UF_RGINT_RGI_MUN_2025.xls")
SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"

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


def registrar_fetch_log(caminho: Path, resultado: ResultadoColeta) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "id_coleta", "data_hora_utc", "fonte", "endpoint", "parametros",
        "indicador_relacionado", "territorio", "status_http", "status_coleta",
        "linhas_extraidas", "arquivo_saida", "mensagem_erro", "observacoes",
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


def salvar_csv(caminho: Path, linhas: list[dict[str, Any]], delimiter: str = ";") -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not linhas:
        raise ValueError(f"Nenhuma linha para salvar em {caminho}")
    campos = list(linhas[0].keys())
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=delimiter)
        escritor.writeheader()
        escritor.writerows(linhas)


def baixar_arquivo(url: str, destino: Path, timeout: int = 120) -> int:
    destino.parent.mkdir(parents=True, exist_ok=True)
    resposta = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "fito-aimm-amazonia/0.4 (+github-actions)",
            "Accept": "application/vnd.ms-excel,application/octet-stream,*/*",
        },
    )
    status = resposta.status_code
    resposta.raise_for_status()
    destino.write_bytes(resposta.content)
    if destino.stat().st_size < 1024:
        raise ValueError("Arquivo baixado parece pequeno demais para ser a planilha de áreas territoriais.")
    return status


def normalizar_codigo(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    texto = str(valor).strip()
    texto = re.sub(r"\.0$", "", texto)
    return re.sub(r"\D", "", texto)


def parse_numero_brasileiro(valor: Any) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)) and not pd.isna(valor):
        return float(valor)

    texto = str(valor).strip().replace("\xa0", " ")
    if not texto or texto.lower() == "nan":
        return None

    texto = re.sub(r"[^0-9,.\-]", "", texto)
    if not texto:
        return None

    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def extrair_areas_municipios_de_xls(arquivo_xls: Path) -> list[dict[str, str]]:
    planilhas = pd.read_excel(arquivo_xls, sheet_name=None, header=None, engine="xlrd")
    resultados: dict[str, dict[str, str]] = {}

    for nome_planilha, df in planilhas.items():
        for _, row in df.iterrows():
            valores = list(row.values)
            codigos_na_linha = {normalizar_codigo(v) for v in valores}
            codigos_encontrados = [c for c in MUNICIPIOS_PROJETO if c in codigos_na_linha]

            if not codigos_encontrados:
                continue

            codigo = codigos_encontrados[0]
            esperado = MUNICIPIOS_PROJETO[codigo]

            numericos = []
            for v in valores:
                n = parse_numero_brasileiro(v)
                if n is None:
                    continue
                if abs(n - int(codigo)) < 0.001:
                    continue
                if 0.1 <= n <= 200000:
                    numericos.append(n)

            if not numericos:
                continue

            area_km2 = numericos[-1]
            nome_detectado = ""
            for v in valores:
                texto = str(v).strip()
                if esperado["municipio"].lower() in texto.lower():
                    nome_detectado = texto
                    break

            resultados[codigo] = {
                "codigo_municipio_ibge": codigo,
                "municipio": esperado["municipio"],
                "uf": esperado["uf"],
                "municipio_nome_detectado_na_planilha": nome_detectado,
                "area_territorial_km2": f"{area_km2:.6f}",
                "ano_area": "2025",
                "fonte_area": "SRC_IBGE_GEOCIENCIAS_AREAS",
                "produto_ibge": "Áreas Territoriais 2025",
                "url_download": AREA_XLS_URL,
                "planilha_origem": str(nome_planilha),
                "observacao_area": "Área territorial extraída da planilha oficial IBGE/Geociências 2025.",
            }

    faltantes = sorted(set(MUNICIPIOS_PROJETO) - set(resultados))
    if faltantes:
        raise ValueError(f"Não foi possível localizar área territorial para os códigos municipais: {faltantes}")

    return [resultados[codigo] for codigo in MUNICIPIOS_PROJETO]


def montar_url_sidra_populacao_estimada(periodo: str = "last") -> str:
    municipios = ",".join(MUNICIPIOS_PROJETO.keys())
    return f"{SIDRA_BASE_URL}/t/6579/n6/{municipios}/v/9324/p/{periodo}?formato=json"


def requisitar_json(url: str, timeout: int = 40) -> tuple[int, Any]:
    resposta = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "fito-aimm-amazonia/0.4 (+github-actions)", "Accept": "application/json"},
    )
    status = resposta.status_code
    resposta.raise_for_status()
    return status, resposta.json()


def encontrar_chave_por_rotulo(cabecalho: dict[str, Any], termos: list[str], sufixo: str | None = None) -> str:
    termos_norm = [t.lower() for t in termos]
    for chave, rotulo in cabecalho.items():
        if sufixo and not str(chave).endswith(sufixo):
            continue
        texto = str(rotulo).lower()
        if all(t in texto for t in termos_norm):
            return str(chave)
    return ""


def transformar_sidra_populacao(dados_json: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not isinstance(dados_json, list) or len(dados_json) < 2:
        raise ValueError("Resposta SIDRA vazia ou em formato inesperado.")

    cabecalho = dados_json[0]
    linhas = dados_json[1:]

    chave_cod_mun = encontrar_chave_por_rotulo(cabecalho, ["município"], "C") or "D1C"
    chave_nome_mun = encontrar_chave_por_rotulo(cabecalho, ["município"], "N") or "D1N"
    chave_ano = (
        encontrar_chave_por_rotulo(cabecalho, ["ano"], "N")
        or encontrar_chave_por_rotulo(cabecalho, ["período"], "N")
        or "D3N"
    )

    saida = []
    for item in linhas:
        codigo = normalizar_codigo(item.get(chave_cod_mun, ""))
        municipio_api = str(item.get(chave_nome_mun, "")).strip()
        esperado = MUNICIPIOS_PROJETO.get(codigo, {})
        valor = str(item.get("V", "")).strip()
        ano = str(item.get(chave_ano, "")).strip()

        if "população" in ano.lower() or not re.search(r"\d{4}", ano):
            for chave, _rotulo in cabecalho.items():
                if str(chave).endswith("N"):
                    candidato = str(item.get(chave, "")).strip()
                    if re.fullmatch(r"\d{4}", candidato):
                        ano = candidato
                        break

        saida.append({
            "codigo_municipio_ibge": codigo,
            "municipio": esperado.get("municipio", municipio_api),
            "uf": esperado.get("uf", ""),
            "populacao_estimada": valor,
            "ano_populacao_estimada": ano,
            "fonte_populacao": "SRC_IBGE_API",
            "tabela_sidra_populacao": "6579",
            "variavel_sidra_populacao": "9324",
        })

    faltantes = sorted(set(MUNICIPIOS_PROJETO) - {linha["codigo_municipio_ibge"] for linha in saida})
    if faltantes:
        raise ValueError(f"Municípios ausentes na resposta SIDRA população: {faltantes}")

    return saida


def coletar_populacao_estimada(arquivo_saida: Path, arquivo_log: Path) -> list[dict[str, str]]:
    id_coleta = f"IBGE_SIDRA_POP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    url = montar_url_sidra_populacao_estimada()
    parametros = json.dumps({"tabela": "6579", "variavel": "9324", "periodo": "last"}, ensure_ascii=False)

    try:
        status, dados = requisitar_json(url)
        linhas = transformar_sidra_populacao(dados)
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
                status_http=status,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas),
                arquivo_saida=str(arquivo_saida),
                observacoes="População estimada municipal coletada via SIDRA para cálculo de densidade estimada.",
            ),
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
            ),
        )
        raise


def coletar_area_territorial_geociencias(
    arquivo_raw: Path = AREA_XLS_RAW,
    arquivo_saida: Path = Path("data/raw/ibge/geociencias/areas_territoriais_municipios_projeto.csv"),
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
) -> list[dict[str, str]]:
    id_coleta = f"IBGE_GEOCIENCIAS_AREA_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    try:
        status = baixar_arquivo(AREA_XLS_URL, arquivo_raw)
        linhas = extrair_areas_municipios_de_xls(arquivo_raw)
        salvar_csv(arquivo_saida, linhas)
        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_IBGE_GEOCIENCIAS_AREAS",
                endpoint=AREA_XLS_URL,
                parametros=json.dumps({"ano": "2025", "municipios": list(MUNICIPIOS_PROJETO.keys())}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_06; baseline_territorial",
                territorio="Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
                status_http=status,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas),
                arquivo_saida=str(arquivo_saida),
                observacoes="Áreas territoriais municipais coletadas da planilha oficial IBGE/Geociências 2025.",
            ),
        )
        return linhas
    except Exception as erro:
        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_IBGE_GEOCIENCIAS_AREAS",
                endpoint=AREA_XLS_URL,
                parametros=json.dumps({"ano": "2025", "municipios": list(MUNICIPIOS_PROJETO.keys())}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_06; baseline_territorial",
                territorio="Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
                status_http="erro",
                status_coleta="falha",
                linhas_extraidas=0,
                arquivo_saida=str(arquivo_saida),
                mensagem_erro=str(erro),
            ),
        )
        raise


def to_float(valor: str) -> float:
    texto = str(valor).strip().replace(".", "").replace(",", ".")
    return float(texto)


def montar_area_densidade(
    populacao: list[dict[str, str]],
    areas: list[dict[str, str]],
    arquivo_saida: Path = Path("data/processed/territorios_ibge_area_densidade.csv"),
) -> list[dict[str, str]]:
    pop_por_codigo = {linha["codigo_municipio_ibge"]: linha for linha in populacao}
    area_por_codigo = {linha["codigo_municipio_ibge"]: linha for linha in areas}

    saida = []
    for codigo, esperado in MUNICIPIOS_PROJETO.items():
        pop = pop_por_codigo[codigo]
        area = area_por_codigo[codigo]
        pop_val = to_float(pop["populacao_estimada"])
        area_val = float(area["area_territorial_km2"])
        densidade = pop_val / area_val

        saida.append({
            "codigo_municipio_ibge": codigo,
            "municipio": esperado["municipio"],
            "uf": esperado["uf"],
            "populacao_estimada": str(int(pop_val)),
            "ano_populacao_estimada": pop.get("ano_populacao_estimada", ""),
            "area_territorial_km2": f"{area_val:.6f}",
            "ano_area_territorial": area.get("ano_area", "2025"),
            "densidade_estimada_hab_km2": f"{densidade:.6f}",
            "formula_densidade": "populacao_estimada / area_territorial_km2",
            "fonte_populacao": "SRC_IBGE_API",
            "fonte_area": "SRC_IBGE_GEOCIENCIAS_AREAS",
            "status_baseline": "coletado",
            "limitacao": "Densidade estimada calculada pela calculadora com população estimada anual e área territorial IBGE/Geociências; não substitui densidade demográfica censitária oficial.",
        })

    salvar_csv(arquivo_saida, saida)
    return saida


def gerar_evidencias_area_densidade(
    linhas: list[dict[str, str]],
    arquivo_saida: Path = Path("data/evidence/evidence_ibge_area_densidade.csv"),
) -> list[dict[str, str]]:
    data_coleta = agora_utc_iso()
    evidencias = []
    for linha in linhas:
        evidencias.append({
            "id_evidencia": f"EVD_IBGE_AREA_DENS_{linha['codigo_municipio_ibge']}",
            "id_fonte": "SRC_IBGE_GEOCIENCIAS_AREAS; SRC_IBGE_API",
            "id_indicador": "GAP_TERR_06",
            "tipo_evidencia": "dado_api_e_download_oficial",
            "pergunta_ou_lacuna": "Qual é a área territorial oficial do município e a densidade estimada para baseline territorial?",
            "url_ou_arquivo": "data/processed/territorios_ibge_area_densidade.csv",
            "titulo_documento": "Área territorial IBGE/Geociências 2025 e população estimada SIDRA",
            "pagina_tabela_secao": "Áreas Territoriais 2025; SIDRA tabela 6579 variável 9324",
            "trecho_original_ou_descricao": f"{linha['municipio']}/{linha['uf']}: área {linha['area_territorial_km2']} km²; população estimada {linha['populacao_estimada']}; densidade estimada {linha['densidade_estimada_hab_km2']} hab/km².",
            "resumo_ptbr": "Evidência automatizada para área territorial e densidade estimada municipal.",
            "valor_extraido": linha["area_territorial_km2"],
            "unidade": "km²",
            "periodo_referencia": linha["ano_area_territorial"],
            "territorio": f"{linha['municipio']}/{linha['uf']}",
            "metodo_extracao": "download XLS IBGE/Geociências + API SIDRA + cálculo automatizado",
            "nivel_confianca": "alto",
            "data_coleta": data_coleta,
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "conferido",
            "limitacoes": linha["limitacao"],
            "uso_na_calculadora": "Linha de base territorial; cálculo de densidade; normalização de indicadores por área.",
            "status_evidencia": "validada",
        })
    salvar_csv(arquivo_saida, evidencias)
    return evidencias


def executar_pipeline_area_densidade_ibge(
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
) -> dict[str, Any]:
    populacao = coletar_populacao_estimada(
        arquivo_saida=Path("data/raw/ibge/populacao_estimada_municipios.csv"),
        arquivo_log=arquivo_log,
    )
    areas = coletar_area_territorial_geociencias(arquivo_log=arquivo_log)
    area_densidade = montar_area_densidade(populacao, areas)
    evidencias = gerar_evidencias_area_densidade(area_densidade)

    return {
        "populacao": populacao,
        "areas": areas,
        "area_densidade": area_densidade,
        "evidencias": evidencias,
    }
