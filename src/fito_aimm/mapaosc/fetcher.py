from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml


MAPAOSC_BASE_URL = "https://mapaosc.ipea.gov.br/download/20260522_MOSC_baseDivulgacao.csv"
MAPAOSC_DICIONARIO_URL = "https://mapaosc.ipea.gov.br/arquivos/subitems/4038-dicionario-de-dados-mapa-oscs.xlsx"

LOCAL_BASE_CANDIDATES = [
    Path("data/raw/mapaosc/20260522_MOSC_baseDivulgacao.csv"),
    Path("data/raw/mapaosc/MOSC_baseDivulgacao.csv"),
    Path("data/raw/mapaosc/mapaosc_base_principal.csv"),
]


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


def detectar_delimitador(amostra: str) -> str:
    linhas = [linha for linha in amostra.splitlines() if linha.strip()]
    primeira_linha = linhas[0] if linhas else ""
    return max([";", ",", "\t", "|"], key=lambda sep: primeira_linha.count(sep))


def detectar_encoding(amostra_bytes: bytes) -> str:
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin1", "iso-8859-1"]:
        try:
            amostra_bytes.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin1"


def primeiro_arquivo_local_existente() -> Path | None:
    for caminho in LOCAL_BASE_CANDIDATES:
        if caminho.exists() and caminho.stat().st_size > 1024:
            return caminho
    return None


def baixar_com_retry(
    url: str,
    destino: Path,
    tentativas: int = 5,
    connect_timeout: int = 60,
    read_timeout: int = 600,
    espera_inicial: int = 20,
) -> tuple[int, Path]:
    destino.parent.mkdir(parents=True, exist_ok=True)
    ultimo_erro = None
    session = requests.Session()
    headers = {
        "User-Agent": "fito-aimm-amazonia/0.6 (+github-actions)",
        "Accept": "text/csv,application/octet-stream,*/*",
        "Connection": "close",
    }

    for tentativa in range(1, tentativas + 1):
        try:
            with session.get(
                url,
                stream=True,
                timeout=(connect_timeout, read_timeout),
                headers=headers,
            ) as resposta:
                status = resposta.status_code
                resposta.raise_for_status()
                tmp = destino.with_suffix(destino.suffix + ".tmp")
                with tmp.open("wb") as arquivo:
                    for bloco in resposta.iter_content(chunk_size=1024 * 1024):
                        if bloco:
                            arquivo.write(bloco)
                if tmp.stat().st_size < 1024:
                    raise ValueError("Arquivo baixado é pequeno demais para ser a base principal do Mapa das OSCs.")
                tmp.replace(destino)
                return status, destino
        except Exception as erro:
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(espera_inicial * tentativa)

    raise RuntimeError(f"Falha após {tentativas} tentativas de download do Mapa das OSCs: {ultimo_erro}")


def obter_arquivo_base_mapaosc() -> tuple[Path, str, int | str]:
    local = primeiro_arquivo_local_existente()
    if local:
        return local, "arquivo_local_preexistente", "local"

    destino = LOCAL_BASE_CANDIDATES[0]
    status, caminho = baixar_com_retry(MAPAOSC_BASE_URL, destino)
    return caminho, "download_requests_retry", status


def carregar_criterios(caminho: Path = Path("config/criterios_triagem_mapaosc.yaml")) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    with caminho.open("r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo) or {}


def baixar_arquivo_com_retry(url: str, destino: Path, tentativas: int = 3) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(
                url,
                timeout=(60, 300),
                headers={"User-Agent": "fito-aimm-amazonia/0.6"},
            )
            resposta.raise_for_status()
            destino.write_bytes(resposta.content)
            return
        except Exception as erro:
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(10 * tentativa)
    print(f"Aviso: dicionário Mapa OSCs não baixado: {ultimo_erro}")
