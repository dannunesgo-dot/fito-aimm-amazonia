"""
Motor de score AIMM — Fito+ Amazônia.

Implementa a mecânica OFICIAL do sistema AIMM (Anticipated Impact Measurement
and Monitoring) do IFC (International Finance Corporation), conforme a "AIMM
Guidance Note", março de 2026.

Referência da mecânica (Tabela 6 e seções da nota):
    https://www.ifc.org/content/dam/ifc/doc/latest/aimm-general-guidance-note.pdf

A mecânica é deliberadamente enxuta e determinística — não há média de
indicadores. O cálculo é:

    1. Cada eixo (Project Outcome e Market Outcome) recebe um RATING qualitativo:
       Marginal / Moderate / Strong / Very Strong.
    2. O rating converte em PONTOS fixos: 4 / 12 / 30 / 50.
    3. Aplica-se o ajuste de RISCO binário: Unqualified (fator 1,00) ou
       Qualified (fator 0,75).
    4. Cada eixo é arredondado ao múltiplo de 2 mais próximo.
    5. O score final é a SOMA dos dois eixos (+10 se elegível a clima/inclusão).
    6. A faixa é: Excellent 72-100 / Good 43-71 / Satisfactory 22-42 / Low 8-21.

Este módulo NÃO decide os ratings — ele os recebe prontos. A lógica que deriva
o rating a partir de indicadores e benchmarks é o sector framework Fito+
(Camada 2), separada e posterior.

Convenções do repositório: função pública ``execute_*``; sem dependências
externas (só biblioteca padrão); retorno estruturado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# --------------------------------------------------------------------------- #
# Valores oficiais (verbatim da Tabela 6 da nota IFC).
# --------------------------------------------------------------------------- #
class Rating(str, Enum):
    """Rating qualitativo de um eixo de outcome (escala oficial de 4 pontos)."""
    MARGINAL = "Marginal"
    MODERATE = "Moderate"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"


class Risco(str, Enum):
    """Avaliação de risco de dois níveis (oficial)."""
    UNQUALIFIED = "Unqualified"   # baixo risco, sem desconto
    QUALIFIED = "Qualified"       # alto risco, desconto de 0,25


# Conversão rating -> pontos (Tabela 6, valores oficiais).
PONTOS_POR_RATING: dict[Rating, int] = {
    Rating.VERY_STRONG: 50,
    Rating.STRONG: 30,
    Rating.MODERATE: 12,
    Rating.MARGINAL: 4,
}

# Fator de ajuste por risco (oficial: 1,00 ou 0,75).
FATOR_POR_RISCO: dict[Risco, float] = {
    Risco.UNQUALIFIED: 1.00,
    Risco.QUALIFIED: 0.75,
}

# Ajuste adicional por contribuição material a clima e/ou inclusão (oficial).
AJUSTE_CLIMA_INCLUSAO = 10


# --------------------------------------------------------------------------- #
# Estruturas de entrada e saída.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AvaliacaoEixo:
    """Avaliação de um eixo (Project Outcome ou Market Outcome)."""
    rating: Rating
    risco: Risco


@dataclass
class ResultadoAIMM:
    """Resultado completo e rastreável de um cálculo AIMM."""
    pontos_project_brutos: float
    pontos_project_ajustados: int
    pontos_market_brutos: float
    pontos_market_ajustados: int
    ajuste_clima_inclusao: int
    score_total: int
    faixa: str
    memoria_calculo: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Mecânica de cálculo.
# --------------------------------------------------------------------------- #
def arredondar_multiplo_2(valor: float) -> int:
    """Arredonda ao múltiplo de 2 mais próximo (regra oficial de cada eixo).

    Usa arredondamento padrão (round-half-to-even do Python) sobre valor/2.
    Ex.: 22,5 -> 22 (conforme exemplo da nota: Strong-Qualified = 22).
    """
    return int(round(valor / 2.0)) * 2


def faixa_aimm(score: int) -> str:
    """Faixa oficial do score (Tabela 6). Fronteiras confirmadas: 72/43/22/8."""
    if score >= 72:
        return "Excellent"
    if score >= 43:
        return "Good"
    if score >= 22:
        return "Satisfactory"
    return "Low"


def _pontos_ajustados_eixo(eixo: AvaliacaoEixo) -> tuple[float, int]:
    """Retorna (pontos_brutos_ajustados_por_risco, pontos_arredondados)."""
    base = PONTOS_POR_RATING[eixo.rating]
    fator = FATOR_POR_RISCO[eixo.risco]
    brutos = base * fator
    return brutos, arredondar_multiplo_2(brutos)


def execute_fitomais_aimm_engine(
    project: AvaliacaoEixo,
    market: AvaliacaoEixo,
    elegivel_clima_inclusao: bool = False,
) -> ResultadoAIMM:
    """Calcula o score AIMM oficial a partir dos ratings de projeto e mercado.

    Args:
        project: avaliação do eixo Project Outcome (rating + risco).
        market: avaliação do eixo Market Outcome (rating + risco).
        elegivel_clima_inclusao: se True, soma 10 pontos (critério oficial).

    Returns:
        ResultadoAIMM com pontos por eixo, score total, faixa e memória de cálculo.
    """
    p_brutos, p_aj = _pontos_ajustados_eixo(project)
    m_brutos, m_aj = _pontos_ajustados_eixo(market)
    ajuste = AJUSTE_CLIMA_INCLUSAO if elegivel_clima_inclusao else 0
    total = p_aj + m_aj + ajuste
    faixa = faixa_aimm(total)

    memoria = [
        f"Project: {project.rating.value}-{project.risco.value} = "
        f"{PONTOS_POR_RATING[project.rating]} x {FATOR_POR_RISCO[project.risco]:.2f} = "
        f"{p_brutos:.2f} -> {p_aj} (múltiplo de 2)",
        f"Market: {market.rating.value}-{market.risco.value} = "
        f"{PONTOS_POR_RATING[market.rating]} x {FATOR_POR_RISCO[market.risco]:.2f} = "
        f"{m_brutos:.2f} -> {m_aj} (múltiplo de 2)",
    ]
    if ajuste:
        memoria.append(f"Ajuste clima/inclusão: +{ajuste}")
    memoria.append(f"Score total = {p_aj} + {m_aj}" + (f" + {ajuste}" if ajuste else "") + f" = {total} ({faixa})")

    return ResultadoAIMM(
        pontos_project_brutos=p_brutos,
        pontos_project_ajustados=p_aj,
        pontos_market_brutos=m_brutos,
        pontos_market_ajustados=m_aj,
        ajuste_clima_inclusao=ajuste,
        score_total=total,
        faixa=faixa,
        memoria_calculo=memoria,
    )


# Conveniência: aceitar strings além dos enums (para uso via CSV/interface).
def calcular_por_texto(
    project_rating: str, project_risco: str,
    market_rating: str, market_risco: str,
    elegivel_clima_inclusao: bool = False,
) -> ResultadoAIMM:
    """Versão que aceita rótulos textuais (ex.: 'Strong', 'Unqualified')."""
    return execute_fitomais_aimm_engine(
        AvaliacaoEixo(Rating(project_rating), Risco(project_risco)),
        AvaliacaoEixo(Rating(market_rating), Risco(market_risco)),
        elegivel_clima_inclusao,
    )


if __name__ == "__main__":
    # Exemplo oficial da nota: Strong-UQ + Strong-Q = 52 (Good).
    r = calcular_por_texto("Strong", "Unqualified", "Strong", "Qualified")
    for linha in r.memoria_calculo:
        print(linha)
