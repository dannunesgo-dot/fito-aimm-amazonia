from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


TERRITORIOS_PATH = Path("config/territorios.yaml")


@lru_cache(maxsize=1)
def carregar_municipios_projeto(caminho: Path = TERRITORIOS_PATH) -> dict[str, dict[str, str]]:
    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = yaml.safe_load(arquivo) or {}

    municipios = dados.get("municipios_projeto") or {}
    if not isinstance(municipios, dict) or not municipios:
        raise ValueError(f"{caminho}: municipios_projeto ausente ou vazio")

    normalizados: dict[str, dict[str, str]] = {}
    for codigo, info in municipios.items():
        codigo_normalizado = "".join(ch for ch in str(codigo).strip() if ch.isdigit())
        if not codigo_normalizado:
            raise ValueError(f"{caminho}: código municipal inválido: {codigo!r}")
        if not isinstance(info, dict):
            raise ValueError(f"{caminho}: configuração inválida para {codigo_normalizado}")

        municipio = str(info.get("municipio", "")).strip()
        uf = str(info.get("uf", "")).strip().upper()
        if not municipio or not uf:
            raise ValueError(f"{caminho}: município/UF obrigatórios para {codigo_normalizado}")

        normalizados[codigo_normalizado] = {"municipio": municipio, "uf": uf}

    return normalizados


def listar_codigos_municipios_projeto() -> list[str]:
    return list(carregar_municipios_projeto().keys())


def descrever_territorios_projeto() -> str:
    return "; ".join(
        f"{info['municipio']}/{info['uf']}"
        for info in carregar_municipios_projeto().values()
    )


def listar_ufs_projeto() -> set[str]:
    return {info["uf"] for info in carregar_municipios_projeto().values()}
