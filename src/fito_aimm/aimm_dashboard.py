"""
Dashboard AIMM — Fito+ Amazônia.

Consome o motor oficial (``fitomais_aimm_engine``) e apresenta o resultado na
estrutura da metodologia do IFC:

    - Eixo 1: Project Outcome (rating, risco, pontos)
    - Eixo 2: Market Outcome (rating, risco, pontos)
    - Score final (soma dos eixos) e faixa (Excellent/Good/Satisfactory/Low)
    - Memória de cálculo (rastreabilidade)

**Substitui** o dashboard anterior, que consumia o motor descontinuado
(``aimm_engine``, preservado em ``docs/deprecated/``). O modelo antigo mostrava
scores por dimensão e por indicador — conceitos que não existem na metodologia
oficial do AIMM.

ENTRADA DE RATINGS (importante):
Os ratings (Marginal/Moderate/Strong/Very Strong) e os riscos
(Unqualified/Qualified) NÃO são derivados por este módulo. Eles vêm de
``data/reference/aimm_ratings_input_seed.csv``, que hoje contém valores
PROVISÓRIOS de exemplo. A derivação real dos ratings — a partir de indicadores,
benchmarks e avaliação de gap/intensidade — é responsabilidade do **sector
framework Fito+** (Camada 2), ainda a construir.

Enquanto os ratings estiverem marcados como ``PROVISORIO_EXEMPLO``, todas as
saídas trazem o alerta ``status_resultado = provisorio_nao_validado``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fito_aimm.fitomais_aimm_engine import (
    AvaliacaoEixo, Rating, Risco, execute_fitomais_aimm_engine,
)

RATINGS_INPUT = Path("data/reference/aimm_ratings_input_seed.csv")

OUT_EXEC_SUMMARY = Path("data/processed/aimm_executive_summary.csv")
OUT_CARDS = Path("data/processed/aimm_dashboard_cards.csv")
OUT_AXES = Path("data/processed/aimm_dashboard_axes_view.csv")
OUT_NEXT_ACTIONS = Path("data/processed/aimm_next_actions.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_aimm_dashboard.csv")
OUT_MD = Path("outputs/reports/aimm_executive_summary.md")
OUT_JSON = Path("outputs/reports/aimm_dashboard_payload.json")

MARCADOR_PROVISORIO = "PROVISORIO_EXEMPLO"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = fields or list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def carregar_ratings() -> tuple[dict[str, str], bool]:
    """Lê os ratings de entrada. Retorna (valores, é_provisorio)."""
    if not RATINGS_INPUT.exists():
        raise FileNotFoundError(
            f"Entrada de ratings ausente: {RATINGS_INPUT}. "
            "Este arquivo é preenchido pelo sector framework Fito+ (Camada 2)."
        )
    linhas = read_csv(RATINGS_INPUT)
    valores = {r["campo"]: r["valor"] for r in linhas}
    provisorio = any(r.get("origem") == MARCADOR_PROVISORIO for r in linhas)
    return valores, provisorio


def execute_aimm_dashboard() -> dict[str, Any]:
    errors: list[str] = []

    valores, provisorio = carregar_ratings()

    try:
        project = AvaliacaoEixo(
            Rating(valores["project_outcome_rating"]),
            Risco(valores["project_outcome_risco"]),
        )
        market = AvaliacaoEixo(
            Rating(valores["market_outcome_rating"]),
            Risco(valores["market_outcome_risco"]),
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Ratings de entrada inválidos em {RATINGS_INPUT}: {exc}") from exc

    clima = str(valores.get("elegivel_clima_inclusao", "nao")).strip().lower() in {"sim", "true", "1"}

    r = execute_fitomais_aimm_engine(project, market, clima)

    status = "provisorio_nao_validado" if provisorio else "validado"
    alerta = (
        "ATENCAO: ratings PROVISORIOS de exemplo. O score NAO representa avaliacao real. "
        "Os ratings reais virao do sector framework Fito+ (Camada 2)."
        if provisorio else
        "Ratings validados pelo sector framework."
    )

    axes = [
        {
            "eixo": "Project Outcome",
            "descricao": "Efeitos sobre stakeholders, economia e meio ambiente/social",
            "rating": project.rating.value,
            "risco": project.risco.value,
            "pontos_brutos": f"{r.pontos_project_brutos:.2f}",
            "pontos_ajustados": str(r.pontos_project_ajustados),
            "status": status,
        },
        {
            "eixo": "Market Outcome",
            "descricao": "Mudancas sistemicas no mercado (competitividade, resiliencia, sustentabilidade)",
            "rating": market.rating.value,
            "risco": market.risco.value,
            "pontos_brutos": f"{r.pontos_market_brutos:.2f}",
            "pontos_ajustados": str(r.pontos_market_ajustados),
            "status": status,
        },
    ]
    write_csv(OUT_AXES, axes)

    cards = [
        {"cartao": "Score AIMM", "valor": str(r.score_total), "detalhe": f"Faixa: {r.faixa}", "status": status},
        {"cartao": "Project Outcome", "valor": str(r.pontos_project_ajustados),
         "detalhe": f"{project.rating.value} / {project.risco.value}", "status": status},
        {"cartao": "Market Outcome", "valor": str(r.pontos_market_ajustados),
         "detalhe": f"{market.rating.value} / {market.risco.value}", "status": status},
        {"cartao": "Ajuste clima/inclusao", "valor": str(r.ajuste_clima_inclusao),
         "detalhe": "Elegivel" if clima else "Nao elegivel", "status": status},
    ]
    write_csv(OUT_CARDS, cards)

    resumo = [{
        "id_resultado": "AIMM_FITOMAIS",
        "score_total": str(r.score_total),
        "faixa": r.faixa,
        "project_outcome_rating": project.rating.value,
        "project_outcome_risco": project.risco.value,
        "project_outcome_pontos": str(r.pontos_project_ajustados),
        "market_outcome_rating": market.rating.value,
        "market_outcome_risco": market.risco.value,
        "market_outcome_pontos": str(r.pontos_market_ajustados),
        "ajuste_clima_inclusao": str(r.ajuste_clima_inclusao),
        "status_resultado": status,
        "alerta": alerta,
        "metodologia": "IFC AIMM Guidance Note (marco 2026) - conversao oficial de ratings.",
    }]
    write_csv(OUT_EXEC_SUMMARY, resumo)

    acoes = []
    if provisorio:
        acoes.append({
            "prioridade": "1",
            "acao": "Construir o sector framework Fito+ (Camada 2) para derivar os ratings reais",
            "motivo": "Os ratings atuais sao provisorios de exemplo; o score nao representa avaliacao real.",
            "responsavel": "equipe Fito+ / MDIC",
        })
    acoes.append({
        "prioridade": "2",
        "acao": "Definir indicadores e benchmarks por eixo de escopo Fito+",
        "motivo": "A metodologia AIMM exige benchmarks para avaliar gap e intensidade.",
        "responsavel": "equipe Fito+ / MDIC",
    })
    write_csv(OUT_NEXT_ACTIONS, acoes)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Resumo Executivo AIMM - Fito+ Amazonia",
        "",
        f"> **{alerta}**" if provisorio else f"> {alerta}",
        "",
        f"## Score AIMM: {r.score_total} ({r.faixa})",
        "",
        "| Eixo | Rating | Risco | Pontos |",
        "|---|---|---|---|",
        f"| Project Outcome | {project.rating.value} | {project.risco.value} | {r.pontos_project_ajustados} |",
        f"| Market Outcome | {market.rating.value} | {market.risco.value} | {r.pontos_market_ajustados} |",
    ]
    if r.ajuste_clima_inclusao:
        md.append(f"| Ajuste clima/inclusao | - | - | +{r.ajuste_clima_inclusao} |")
    md += ["", "## Memoria de calculo", ""]
    md += [f"- {linha}" for linha in r.memoria_calculo]
    md += [
        "",
        "## Metodologia",
        "",
        "Conforme a *AIMM Guidance Note* (IFC, marco de 2026): ratings qualitativos",
        "convertidos em pontos fixos (Marginal 4 / Moderate 12 / Strong 30 / Very Strong 50),",
        "ajustados por risco (Unqualified 1,00 / Qualified 0,75), arredondados ao multiplo de 2",
        "e somados. Faixas: Excellent 72-100 / Good 43-71 / Satisfactory 22-42 / Low 8-21.",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "score_total": r.score_total,
        "faixa": r.faixa,
        "eixos": axes,
        "ajuste_clima_inclusao": r.ajuste_clima_inclusao,
        "memoria_calculo": r.memoria_calculo,
        "status_resultado": status,
        "alerta": alerta,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    write_csv(OUT_EVIDENCE, [{
        "id_evidencia": "EVD_AIMM_DASHBOARD",
        "id_fonte": "FITOMAIS_AIMM_ENGINE",
        "tipo_evidencia": "resultado_calculo_aimm",
        "trecho_original_ou_descricao": " | ".join(r.memoria_calculo),
        "valor_extraido": str(r.score_total),
        "unidade": "pontos AIMM",
        "metodo_extracao": "conversao oficial IFC de ratings qualitativos",
        "status_evidencia": status,
        "limitacoes": alerta,
    }])

    return {
        "errors": errors,
        "score_total": r.score_total,
        "faixa": r.faixa,
        "project": {"rating": project.rating.value, "risco": project.risco.value,
                    "pontos": r.pontos_project_ajustados},
        "market": {"rating": market.rating.value, "risco": market.risco.value,
                   "pontos": r.pontos_market_ajustados},
        "ajuste_clima_inclusao": r.ajuste_clima_inclusao,
        "provisorio": provisorio,
        "status": status,
        "memoria_calculo": r.memoria_calculo,
        "outputs": {
            "exec_summary": str(OUT_EXEC_SUMMARY),
            "cards": str(OUT_CARDS),
            "axes": str(OUT_AXES),
            "next_actions": str(OUT_NEXT_ACTIONS),
            "markdown": str(OUT_MD),
            "json": str(OUT_JSON),
            "evidence": str(OUT_EVIDENCE),
        },
    }


if __name__ == "__main__":
    res = execute_aimm_dashboard()
    print(f"Score AIMM: {res['score_total']} ({res['faixa']})")
    print(f"  Project Outcome: {res['project']['rating']}/{res['project']['risco']} = {res['project']['pontos']}")
    print(f"  Market Outcome:  {res['market']['rating']}/{res['market']['risco']} = {res['market']['pontos']}")
    if res["provisorio"]:
        print("  ATENCAO: ratings provisorios de exemplo - score nao e avaliacao real.")
