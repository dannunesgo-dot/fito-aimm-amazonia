
from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml


MAPAOSC_BASE_URL = "https://mapaosc.ipea.gov.br/download/20260522_MOSC_baseDivulgacao.csv"
MAPAOSC_DICIONARIO_URL = "https://mapaosc.ipea.gov.br/arquivos/subitems/4038-dicionario-de-dados-mapa-oscs.xlsx"

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
    campos = ["id_coleta","data_hora_utc","fonte","endpoint","parametros","indicador_relacionado","territorio","status_http","status_coleta","linhas_extraidas","arquivo_saida","mensagem_erro","observacoes"]
    existe = caminho.exists()
    with caminho.open("a", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        if not existe or caminho.stat().st_size == 0:
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


def remover_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto or "")) if not unicodedata.combining(c))


def normalizar_texto(texto: Any) -> str:
    texto = remover_acentos(str(texto or "")).lower().strip()
    return re.sub(r"\s+", " ", texto)


def normalizar_coluna(nome: str) -> str:
    nome = normalizar_texto(nome)
    return re.sub(r"[^a-z0-9]+", "_", nome).strip("_")


def detectar_delimitador(amostra: str) -> str:
    primeira_linha = amostra.splitlines()[0] if amostra.splitlines() else ""
    return max([";", ",", "\t", "|"], key=lambda sep: primeira_linha.count(sep))


def baixar_amostra(url: str, tamanho: int = 120000) -> tuple[str, int]:
    resposta = requests.get(url, stream=True, timeout=90, headers={"User-Agent": "fito-aimm-amazonia/0.5"})
    status = resposta.status_code
    resposta.raise_for_status()
    conteudo = b""
    for bloco in resposta.iter_content(chunk_size=8192):
        conteudo += bloco
        if len(conteudo) >= tamanho:
            break
    return conteudo.decode("utf-8", errors="replace"), status


def selecionar_coluna(colunas: list[str], preferencias: list[str]) -> str:
    norm = {col: normalizar_coluna(col) for col in colunas}
    for pref in preferencias:
        pref_norm = normalizar_coluna(pref)
        for col, col_norm in norm.items():
            if pref_norm == col_norm or pref_norm in col_norm:
                return col
    return ""


def carregar_criterios(caminho: Path = Path("config/criterios_triagem_mapaosc.yaml")) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    with caminho.open("r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo) or {}


def localizar_colunas(df: pd.DataFrame) -> dict[str, str]:
    colunas = list(df.columns)
    return {
        "codigo_municipio": selecionar_coluna(colunas, ["cd_municipio", "codigo_municipio", "cod_municipio", "id_municipio", "municipio_codigo", "cod_mun"]),
        "municipio": selecionar_coluna(colunas, ["tx_nome_municipio", "nome_municipio", "municipio", "nm_municipio", "cidade"]),
        "uf": selecionar_coluna(colunas, ["sg_uf", "uf", "sigla_uf", "tx_uf"]),
        "cnpj": selecionar_coluna(colunas, ["cnpj", "nr_cnpj", "id_osc", "cd_identificador_osc"]),
        "nome": selecionar_coluna(colunas, ["tx_nome_osc", "nome_osc", "razao_social", "tx_razao_social", "nome_fantasia", "nome"]),
        "natureza": selecionar_coluna(colunas, ["natureza_juridica", "tx_nome_natureza_juridica", "classe_atividade_economica", "cnae", "juridica"]),
        "situacao": selecionar_coluna(colunas, ["situacao_cadastral", "situacao", "status", "data_baixa", "dt_baixa", "baixa"]),
        "email": selecionar_coluna(colunas, ["email", "correio_eletronico", "tx_email"]),
        "telefone": selecionar_coluna(colunas, ["telefone", "tx_telefone", "ddd"]),
        "endereco": selecionar_coluna(colunas, ["endereco", "logradouro", "bairro", "cep"]),
        "area": selecionar_coluna(colunas, ["area_atuacao", "subarea_atuacao", "atividade", "cnae", "finalidade"]),
    }


def texto_linha(row: pd.Series) -> str:
    return " ".join(str(v) for v in row.values if not pd.isna(v))


def filtrar_chunk_por_municipio(df: pd.DataFrame, colmap: dict[str, str]) -> pd.DataFrame:
    alvo_codigos = set(MUNICIPIOS_PROJETO.keys())
    alvo_municipios = {normalizar_texto(v["municipio"]): v for v in MUNICIPIOS_PROJETO.values()}
    mask = pd.Series([False] * len(df), index=df.index)

    col_codigo = colmap.get("codigo_municipio")
    if col_codigo and col_codigo in df.columns:
        codigos = df[col_codigo].astype(str).str.replace(r"\D", "", regex=True)
        mask = mask | codigos.isin(alvo_codigos)

    col_mun = colmap.get("municipio")
    col_uf = colmap.get("uf")
    if col_mun and col_mun in df.columns:
        mun_norm = df[col_mun].astype(str).map(normalizar_texto)
        mun_match = mun_norm.isin(alvo_municipios.keys())
        if col_uf and col_uf in df.columns:
            uf_match = df[col_uf].astype(str).str.upper().str.strip().isin(["AM", "PA"])
            mask = mask | (mun_match & uf_match)
        else:
            mask = mask | mun_match

    return df.loc[mask].copy()


def contem_alguma(texto_norm: str, palavras: list[str]) -> bool:
    return any(normalizar_texto(p) in texto_norm for p in palavras)


def classificar_organizacao(row: pd.Series, colmap: dict[str, str], criterios: dict[str, Any]) -> dict[str, Any]:
    palavras = criterios.get("palavras_chave", {})
    pontos = criterios.get("pontuacao", {})
    texto = normalizar_texto(texto_linha(row))
    score = int(pontos.get("base_municipio_alvo", 20))
    flags = []

    situacao = normalizar_texto(row.get(colmap.get("situacao", ""), "")) if colmap.get("situacao") else ""
    if any(x in situacao for x in ["baixada", "inativa", "encerrada"]):
        score += int(pontos.get("penalidade_baixada_inativa", -40))
        flags.append("possivelmente_baixada_ou_inativa")
    else:
        score += int(pontos.get("ativa_ou_sem_baixa", 15))
        flags.append("ativa_ou_sem_baixa_identificada")

    for chave, ponto_nome, flag in [
        ("associacao", "tipo_associacao", "associacao"),
        ("cooperativa", "tipo_cooperativa", "cooperativa"),
        ("fundacao", "tipo_fundacao", "fundacao"),
        ("saude", "area_saude", "saude"),
        ("agricultura_extrativismo_bioeconomia", "area_agricultura_extrativismo_bioeconomia", "agricultura_extrativismo_bioeconomia"),
        ("meio_ambiente_sustentabilidade", "area_meio_ambiente_sustentabilidade", "meio_ambiente_sustentabilidade"),
        ("pesquisa_educacao_capacitacao", "area_pesquisa_educacao_capacitacao", "pesquisa_educacao_capacitacao"),
    ]:
        if contem_alguma(texto, palavras.get(chave, [])):
            score += int(pontos.get(ponto_nome, 0))
            flags.append(flag)

    def get_col(chave):
        col = colmap.get(chave, "")
        return str(row.get(col, "") or "").strip() if col else ""

    if get_col("email") or get_col("telefone"):
        score += int(pontos.get("possui_email_ou_telefone", 10))
        flags.append("contato_minimo")
    if get_col("endereco"):
        score += int(pontos.get("possui_endereco", 5))
        flags.append("endereco")
    if not (get_col("email") or get_col("telefone") or get_col("endereco")):
        score += int(pontos.get("penalidade_dado_minimo_insuficiente", -10))
        flags.append("dados_contato_insuficientes")

    classe = "alta_prioridade" if score >= 70 else ("media_prioridade" if score >= 40 else "baixa_prioridade")
    return {"score_triagem": score, "classificacao_triagem": classe, "marcadores_triagem": "|".join(flags)}


def valor(row: pd.Series, coluna: str) -> str:
    if not coluna or coluna not in row.index:
        return ""
    v = row.get(coluna, "")
    return "" if pd.isna(v) else str(v).strip()


def padronizar_linhas(df: pd.DataFrame, colmap: dict[str, str], criterios: dict[str, Any]) -> list[dict[str, str]]:
    saida = []
    for _, row in df.iterrows():
        municipio_raw = valor(row, colmap.get("municipio", ""))
        uf_raw = valor(row, colmap.get("uf", "")).upper()
        codigo_raw = re.sub(r"\D", "", valor(row, colmap.get("codigo_municipio", "")))

        if codigo_raw in MUNICIPIOS_PROJETO:
            info = MUNICIPIOS_PROJETO[codigo_raw]
            municipio, uf, codigo_ibge = info["municipio"], info["uf"], codigo_raw
        else:
            municipio_norm = normalizar_texto(municipio_raw)
            codigo_ibge, municipio, uf = "", municipio_raw, uf_raw
            for codigo, info in MUNICIPIOS_PROJETO.items():
                if normalizar_texto(info["municipio"]) == municipio_norm and info["uf"] == uf_raw:
                    codigo_ibge, municipio, uf = codigo, info["municipio"], info["uf"]
                    break

        triagem = classificar_organizacao(row, colmap, criterios)
        saida.append({
            "cnpj_ou_id": valor(row, colmap.get("cnpj", "")),
            "nome_organizacao": valor(row, colmap.get("nome", "")),
            "municipio": municipio,
            "uf": uf,
            "codigo_municipio_ibge": codigo_ibge,
            "natureza_juridica_ou_classe": valor(row, colmap.get("natureza", "")),
            "situacao_cadastral_ou_status": valor(row, colmap.get("situacao", "")),
            "area_atuacao_ou_atividade": valor(row, colmap.get("area", "")),
            "email": valor(row, colmap.get("email", "")),
            "telefone": valor(row, colmap.get("telefone", "")),
            "endereco": valor(row, colmap.get("endereco", "")),
            "score_triagem": str(triagem["score_triagem"]),
            "classificacao_triagem": triagem["classificacao_triagem"],
            "marcadores_triagem": triagem["marcadores_triagem"],
            "fonte": "SRC_MAPA_OSC",
            "limitacao": "Triagem remota automatizada. Requer verificação documental, regularidade jurídica, contato ativo e visita/entrevista antes de seleção.",
        })
    return saida


def salvar_csv(caminho: Path, linhas: list[dict[str, Any]], campos: list[str] | None = None) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if campos is None:
        campos = list(linhas[0].keys()) if linhas else ["cnpj_ou_id","nome_organizacao","municipio","uf","codigo_municipio_ibge","score_triagem","classificacao_triagem","fonte","limitacao"]
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)


def baixar_arquivo(url: str, destino: Path, timeout: int = 120) -> int:
    destino.parent.mkdir(parents=True, exist_ok=True)
    resposta = requests.get(url, timeout=timeout, headers={"User-Agent": "fito-aimm-amazonia/0.5"})
    status = resposta.status_code
    resposta.raise_for_status()
    destino.write_bytes(resposta.content)
    return status


def gerar_resumo_por_municipio(linhas: list[dict[str, str]]) -> list[dict[str, str]]:
    resumo = {f"{i['municipio']}/{i['uf']}": {"total":0,"alta":0,"media":0,"baixa":0,"coop":0,"assoc":0} for i in MUNICIPIOS_PROJETO.values()}
    for l in linhas:
        chave = f"{l['municipio']}/{l['uf']}"
        if chave not in resumo:
            continue
        resumo[chave]["total"] += 1
        if l["classificacao_triagem"] == "alta_prioridade":
            resumo[chave]["alta"] += 1
        elif l["classificacao_triagem"] == "media_prioridade":
            resumo[chave]["media"] += 1
        else:
            resumo[chave]["baixa"] += 1
        if "cooperativa" in l.get("marcadores_triagem",""):
            resumo[chave]["coop"] += 1
        if "associacao" in l.get("marcadores_triagem",""):
            resumo[chave]["assoc"] += 1
    saida = []
    for chave, v in resumo.items():
        municipio, uf = chave.split("/")
        saida.append({"municipio": municipio, "uf": uf, "total_organizacoes_filtradas": str(v["total"]), "alta_prioridade": str(v["alta"]), "media_prioridade": str(v["media"]), "baixa_prioridade": str(v["baixa"]), "com_marcador_cooperativa": str(v["coop"]), "com_marcador_associacao": str(v["assoc"]), "fonte": "SRC_MAPA_OSC"})
    return saida


def gerar_evidencias_mapaosc(resumo: list[dict[str, str]], arquivo_saida: Path = Path("data/evidence/evidence_mapaosc_triagem.csv")) -> list[dict[str, str]]:
    data = agora_utc_iso()
    evidencias = []
    for l in resumo:
        evidencias.append({
            "id_evidencia": f"EVD_MAPAOSC_TRIAGEM_{normalizar_coluna(l['municipio'])}_{l['uf']}",
            "id_fonte": "SRC_MAPA_OSC",
            "id_indicador": "GAP_TERR_05; INT_BEN_05; RISK_OSC_01; MON_02",
            "tipo_evidencia": "base_publica_filtrada",
            "pergunta_ou_lacuna": "Quais OSCs, associações, cooperativas e organizações candidatas existem no município?",
            "url_ou_arquivo": "data/processed/organizacoes_candidatas_mapaosc.csv",
            "titulo_documento": "Triagem automatizada de OSCs — Mapa das OSCs/Ipea",
            "pagina_tabela_secao": "Base principal do Mapa das OSCs; coleta maio/2026; filtro municipal",
            "trecho_original_ou_descricao": f"{l['municipio']}/{l['uf']}: {l['total_organizacoes_filtradas']} organizações filtradas; {l['alta_prioridade']} alta prioridade; {l['media_prioridade']} média prioridade.",
            "resumo_ptbr": "Evidência de triagem remota inicial para seleção de organizações executoras/parceiras.",
            "valor_extraido": l["total_organizacoes_filtradas"],
            "unidade": "organizações",
            "periodo_referencia": "maio/2026",
            "territorio": f"{l['municipio']}/{l['uf']}",
            "metodo_extracao": "download da base principal do Mapa das OSCs e filtragem automatizada por município",
            "nivel_confianca": "médio",
            "data_coleta": data,
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "pendente_verificacao_humana",
            "limitacoes": "Triagem remota; requer validação documental, contato, regularidade jurídica e avaliação de campo.",
            "uso_na_calculadora": "Linha de base de organizações candidatas e risco de capacidade executora.",
            "status_evidencia": "pendente",
        })
    salvar_csv(arquivo_saida, evidencias)
    return evidencias


def coletar_mapaosc_municipios(
    arquivo_saida_raw: Path = Path("data/raw/mapaosc/mapaosc_base_principal_filtrada_municipios.csv"),
    arquivo_saida_processado: Path = Path("data/processed/organizacoes_candidatas_mapaosc.csv"),
    arquivo_resumo: Path = Path("data/processed/resumo_organizacoes_mapaosc_municipios.csv"),
    arquivo_log: Path = Path("data/reference/fetch_log.csv"),
    arquivo_dicionario: Path = Path("data/raw/mapaosc/dicionario_de_dados_mapa_oscs.xlsx"),
    criterios_path: Path = Path("config/criterios_triagem_mapaosc.yaml"),
    max_linhas_saida: int = 5000,
) -> dict[str, Any]:
    id_coleta = f"MAPAOSC_TRIAGEM_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    criterios = carregar_criterios(criterios_path)

    try:
        amostra, status = baixar_amostra(MAPAOSC_BASE_URL)
        delimitador = detectar_delimitador(amostra)

        try:
            baixar_arquivo(MAPAOSC_DICIONARIO_URL, arquivo_dicionario)
        except Exception:
            arquivo_dicionario.parent.mkdir(parents=True, exist_ok=True)
            arquivo_dicionario.with_suffix(".txt").write_text("Dicionário não baixado automaticamente nesta execução.", encoding="utf-8")

        linhas_processadas = []
        colmap_final = {}
        total_linhas_lidas = 0

        reader = pd.read_csv(MAPAOSC_BASE_URL, sep=delimitador, dtype=str, chunksize=100000, encoding="utf-8", low_memory=False, on_bad_lines="skip")
        for chunk in reader:
            total_linhas_lidas += len(chunk)
            if not colmap_final:
                colmap_final = localizar_colunas(chunk)
            filtrado = filtrar_chunk_por_municipio(chunk, colmap_final)
            if filtrado.empty:
                continue
            linhas_processadas.extend(padronizar_linhas(filtrado, colmap_final, criterios))
            if len(linhas_processadas) >= max_linhas_saida:
                linhas_processadas = linhas_processadas[:max_linhas_saida]
                break

        campos = ["cnpj_ou_id","nome_organizacao","municipio","uf","codigo_municipio_ibge","natureza_juridica_ou_classe","situacao_cadastral_ou_status","area_atuacao_ou_atividade","email","telefone","endereco","score_triagem","classificacao_triagem","marcadores_triagem","fonte","limitacao"]
        salvar_csv(arquivo_saida_raw, linhas_processadas, campos=campos)
        salvar_csv(arquivo_saida_processado, sorted(linhas_processadas, key=lambda x: int(x.get("score_triagem") or 0), reverse=True), campos=campos)

        resumo = gerar_resumo_por_municipio(linhas_processadas)
        salvar_csv(arquivo_resumo, resumo)
        evidencias = gerar_evidencias_mapaosc(resumo)

        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_MAPA_OSC",
                endpoint=MAPAOSC_BASE_URL,
                parametros=json.dumps({"municipios": MUNICIPIOS_PROJETO, "delimitador_detectado": delimitador, "max_linhas_saida": max_linhas_saida, "colunas_detectadas": colmap_final}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_05; INT_BEN_05; RISK_OSC_01; MON_02",
                territorio="Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
                status_http=status,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas_processadas),
                arquivo_saida=str(arquivo_saida_processado),
                observacoes=f"Triagem Mapa OSCs concluída. Linhas lidas: {total_linhas_lidas}. Linhas filtradas: {len(linhas_processadas)}.",
            ),
        )

        return {"linhas": linhas_processadas, "resumo": resumo, "evidencias": evidencias, "colunas_detectadas": colmap_final, "total_linhas_lidas": total_linhas_lidas, "delimitador": delimitador}

    except Exception as erro:
        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_MAPA_OSC",
                endpoint=MAPAOSC_BASE_URL,
                parametros=json.dumps({"municipios": MUNICIPIOS_PROJETO}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_05; INT_BEN_05; RISK_OSC_01; MON_02",
                territorio="Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
                status_http="erro",
                status_coleta="falha",
                linhas_extraidas=0,
                arquivo_saida=str(arquivo_saida_processado),
                mensagem_erro=str(erro),
                observacoes="Falha na triagem automatizada Mapa das OSCs/Ipea.",
            ),
        )
        raise
