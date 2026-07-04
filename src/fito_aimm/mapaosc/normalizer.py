from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

from ..territorios import carregar_municipios_projeto, listar_ufs_projeto
from .classifier import classificar_organizacao


MUNICIPIOS_PROJETO = carregar_municipios_projeto()
UFS_PROJETO = listar_ufs_projeto()


def remover_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto or ""))
        if not unicodedata.combining(c)
    )


def normalizar_texto(texto: Any) -> str:
    texto = remover_acentos(str(texto or "")).lower().strip()
    return re.sub(r"\s+", " ", texto)


def normalizar_coluna(nome: str) -> str:
    nome = normalizar_texto(nome)
    return re.sub(r"[^a-z0-9]+", "_", nome).strip("_")


def selecionar_coluna(colunas: list[str], preferencias: list[str]) -> str:
    norm = {col: normalizar_coluna(col) for col in colunas}
    for pref in preferencias:
        pref_norm = normalizar_coluna(pref)
        for col, col_norm in norm.items():
            if pref_norm == col_norm or pref_norm in col_norm:
                return col
    return ""


def localizar_colunas(df: pd.DataFrame) -> dict[str, str]:
    colunas = list(df.columns)
    return {
        "codigo_municipio": selecionar_coluna(colunas, [
            "cd_municipio", "codigo_municipio", "cod_municipio", "id_municipio",
            "municipio_codigo", "cod_mun", "edmu_cd_municipio"
        ]),
        "municipio": selecionar_coluna(colunas, [
            "tx_nome_municipio", "nome_municipio", "municipio", "nm_municipio",
            "cidade", "edmu_nm_municipio"
        ]),
        "uf": selecionar_coluna(colunas, [
            "sg_uf", "uf", "sigla_uf", "tx_uf", "eduf_sg_uf"
        ]),
        "cnpj": selecionar_coluna(colunas, [
            "cnpj", "nr_cnpj", "id_osc", "cd_identificador_osc", "tx_razao_social_osc"
        ]),
        "nome": selecionar_coluna(colunas, [
            "tx_nome_osc", "nome_osc", "razao_social", "tx_razao_social",
            "nome_fantasia", "nome"
        ]),
        "natureza": selecionar_coluna(colunas, [
            "natureza_juridica", "tx_nome_natureza_juridica", "classe_atividade_economica",
            "cnae", "juridica"
        ]),
        "situacao": selecionar_coluna(colunas, [
            "situacao_cadastral", "situacao", "status", "data_baixa", "dt_baixa", "baixa"
        ]),
        "email": selecionar_coluna(colunas, [
            "email", "correio_eletronico", "tx_email"
        ]),
        "telefone": selecionar_coluna(colunas, [
            "telefone", "tx_telefone", "ddd", "nr_telefone"
        ]),
        "endereco": selecionar_coluna(colunas, [
            "endereco", "logradouro", "bairro", "cep"
        ]),
        "area": selecionar_coluna(colunas, [
            "area_atuacao", "subarea_atuacao", "atividade", "cnae", "finalidade"
        ]),
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
            uf_match = df[col_uf].astype(str).str.upper().str.strip().isin(UFS_PROJETO)
            mask = mask | (mun_match & uf_match)
        else:
            mask = mask | mun_match

    return df.loc[mask].copy()


def valor(row: pd.Series, coluna: str) -> str:
    if not coluna or coluna not in row.index:
        return ""
    dado = row.get(coluna, "")
    return "" if pd.isna(dado) else str(dado).strip()


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

        triagem = classificar_organizacao(row, colmap, criterios, texto_linha(row), normalizar_texto)
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
