from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Iterable, TypeVar


T = TypeVar("T")


DIMENSION_LABELS = {
    "gap": "Lacuna territorial",
    "intensidade": "Força do investimento",
    "mercado": "Viabilidade comercial",
    "risco": "Fatores de risco",
    "monitoramento": "Capacidade de acompanhamento",
}

DIMENSION_TOOLTIPS = {
    "gap": "Mostra a distância entre a situação atual e o potencial territorial que o projeto pode alcançar.",
    "intensidade": "Indica quanta transformação social e produtiva o investimento consegue viabilizar.",
    "mercado": "Resume a capacidade do projeto de gerar demanda, receita e conexão com compradores reais.",
    "risco": "Reúne os impedimentos operacionais, regulatórios e organizacionais que podem reduzir o resultado.",
    "monitoramento": "Mede se o projeto consegue acompanhar evidências, indicadores e prestação de contas.",
}


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only.lower()).strip("-")
    return slug or "projeto"


def unique_preserve_order(items: Iterable[T]) -> list[T]:
    seen: set[T] = set()
    ordered: list[T] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def dimension_label(key: str) -> str:
    return DIMENSION_LABELS.get(key, key.replace("_", " ").title())


def dimension_tooltip(key: str) -> str:
    return DIMENSION_TOOLTIPS.get(key, "Dimensão AIMM da calculadora Fito+.")


def qualitative_label(score: float) -> str:
    if score <= 20:
        return "Muito baixo"
    if score <= 40:
        return "Baixo"
    if score <= 60:
        return "Regular"
    if score <= 80:
        return "Bom"
    return "Excelente"


def status_badge(score: float, has_blocker: bool = False) -> str:
    if has_blocker:
        return "Impedimento crítico"
    if score < 40:
        return "Atenção prioritária"
    if score < 70:
        return "Potencial moderado"
    return "Elegível para análise formal"


def iso_now_utc() -> datetime:
    return datetime.now(timezone.utc)
