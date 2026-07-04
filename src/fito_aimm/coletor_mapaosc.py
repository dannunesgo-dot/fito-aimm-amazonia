from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .mapaosc.classifier import gerar_evidencias_mapaosc, gerar_resumo_por_municipio
from .mapaosc.fetcher import (
    MAPAOSC_BASE_URL,
    MAPAOSC_DICIONARIO_URL,
    ResultadoColeta,
    baixar_arquivo_com_retry,
    carregar_criterios,
    detectar_delimitador,
    detectar_encoding,
    obter_arquivo_base_mapaosc,
    registrar_fetch_log,
)
from .mapaosc.normalizer import filtrar_chunk_por_municipio, localizar_colunas, normalizar_coluna, padronizar_linhas
from .territorios import carregar_municipios_projeto, descrever_territorios_projeto


MUNICIPIOS_PROJETO = carregar_municipios_projeto()
TERRITORIO_PROJETO = descrever_territorios_projeto()


def salvar_csv(caminho: Path, linhas: list[dict[str, Any]], campos: list[str] | None = None) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if campos is None:
        campos = list(linhas[0].keys()) if linhas else [
            "cnpj_ou_id", "nome_organizacao", "municipio", "uf", "codigo_municipio_ibge",
            "score_triagem", "classificacao_triagem", "fonte", "limitacao",
        ]
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)


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
    caminho_base = None
    metodo_obtencao = ""
    status_http: int | str = "local"

    try:
        caminho_base, metodo_obtencao, status_http = obter_arquivo_base_mapaosc()
        amostra_bytes = caminho_base.read_bytes()[:200000]
        encoding = detectar_encoding(amostra_bytes)
        amostra_texto = amostra_bytes.decode(encoding, errors="replace")
        delimitador = detectar_delimitador(amostra_texto)

        baixar_arquivo_com_retry(MAPAOSC_DICIONARIO_URL, arquivo_dicionario)

        linhas_processadas = []
        colmap_final: dict[str, str] = {}
        total_linhas_lidas = 0

        try:
            reader = pd.read_csv(
                caminho_base,
                sep=delimitador,
                dtype=str,
                chunksize=50000,
                encoding=encoding,
                encoding_errors="replace",
                low_memory=False,
                on_bad_lines="skip",
            )
        except TypeError:
            reader = pd.read_csv(
                caminho_base,
                sep=delimitador,
                dtype=str,
                chunksize=50000,
                encoding=encoding,
                low_memory=False,
                on_bad_lines="skip",
            )

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

        campos = [
            "cnpj_ou_id", "nome_organizacao", "municipio", "uf", "codigo_municipio_ibge",
            "natureza_juridica_ou_classe", "situacao_cadastral_ou_status",
            "area_atuacao_ou_atividade", "email", "telefone", "endereco",
            "score_triagem", "classificacao_triagem", "marcadores_triagem", "fonte", "limitacao",
        ]
        salvar_csv(arquivo_saida_raw, linhas_processadas, campos=campos)
        salvar_csv(
            arquivo_saida_processado,
            sorted(linhas_processadas, key=lambda item: int(item.get("score_triagem") or 0), reverse=True),
            campos=campos,
        )

        resumo = gerar_resumo_por_municipio(linhas_processadas)
        salvar_csv(arquivo_resumo, resumo)
        evidencias = gerar_evidencias_mapaosc(resumo, salvar_csv, normalizar_coluna)

        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_MAPA_OSC",
                endpoint=str(caminho_base) if metodo_obtencao == "arquivo_local_preexistente" else MAPAOSC_BASE_URL,
                parametros=json.dumps({
                    "municipios": MUNICIPIOS_PROJETO,
                    "delimitador_detectado": delimitador,
                    "encoding_detectado": encoding,
                    "metodo_obtencao_base": metodo_obtencao,
                    "arquivo_base": str(caminho_base),
                    "max_linhas_saida": max_linhas_saida,
                    "colunas_detectadas": colmap_final,
                    "chunksize": 50000,
                }, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_05; INT_BEN_05; RISK_OSC_01; MON_02",
                territorio=TERRITORIO_PROJETO,
                status_http=status_http,
                status_coleta="sucesso",
                linhas_extraidas=len(linhas_processadas),
                arquivo_saida=str(arquivo_saida_processado),
                observacoes=(
                    f"Triagem Mapa OSCs concluída. Método: {metodo_obtencao}. Encoding: {encoding}. "
                    f"Linhas lidas: {total_linhas_lidas}. Linhas filtradas: {len(linhas_processadas)}. Chunksize: 50000."
                ),
            ),
        )

        return {
            "linhas": linhas_processadas,
            "resumo": resumo,
            "evidencias": evidencias,
            "colunas_detectadas": colmap_final,
            "total_linhas_lidas": total_linhas_lidas,
            "delimitador": delimitador,
            "encoding": encoding,
            "metodo_obtencao_base": metodo_obtencao,
            "arquivo_base": str(caminho_base),
            "chunksize": 50000,
        }

    except Exception as erro:
        registrar_fetch_log(
            arquivo_log,
            ResultadoColeta(
                id_coleta=id_coleta,
                fonte="SRC_MAPA_OSC",
                endpoint=MAPAOSC_BASE_URL,
                parametros=json.dumps({"municipios": MUNICIPIOS_PROJETO}, ensure_ascii=False),
                indicador_relacionado="GAP_TERR_05; INT_BEN_05; RISK_OSC_01; MON_02",
                territorio=TERRITORIO_PROJETO,
                status_http="erro",
                status_coleta="falha",
                linhas_extraidas=0,
                arquivo_saida=str(arquivo_saida_processado),
                mensagem_erro=str(erro),
                observacoes="Falha na triagem automatizada Mapa das OSCs/Ipea.",
            ),
        )
        raise
