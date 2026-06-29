
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/aimm_dashboard_rules.yaml")
CARDS_SEED = Path("data/reference/aimm_dashboard_cards_seed.csv")
NEXT_ACTIONS_SEED = Path("data/reference/aimm_next_actions_seed.csv")

ENGINE_OVERALL = Path("data/processed/aimm_overall_score.csv")
ENGINE_DIMENSIONS = Path("data/processed/aimm_dimension_scores.csv")
ENGINE_INDICATORS = Path("data/processed/aimm_indicator_scores.csv")
ENGINE_BLOCKERS = Path("data/processed/aimm_blockers_report.csv")
ENGINE_VALIDATION = Path("data/processed/aimm_engine_validation_report.csv")

OUT_EXEC_SUMMARY = Path("data/processed/aimm_executive_summary.csv")
OUT_CARDS = Path("data/processed/aimm_dashboard_cards.csv")
OUT_DIM_VIEW = Path("data/processed/aimm_dashboard_dimension_view.csv")
OUT_MANIFEST = Path("data/processed/aimm_output_manifest.csv")
OUT_NEXT_ACTIONS = Path("data/processed/aimm_next_actions.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_aimm_dashboard.csv")
OUT_MD = Path("outputs/reports/aimm_executive_summary.md")
OUT_JSON = Path("outputs/reports/aimm_dashboard_payload.json")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ensure_engine_outputs() -> None:
    """
    O GitHub Actions não preserva artefatos de workflows anteriores como arquivos versionados.
    Por isso, se os outputs do motor 4.16 não estiverem no repositório, esta etapa executa o motor
    a partir dos seeds já versionados da Rodada 4.16.
    """
    required = [ENGINE_OVERALL, ENGINE_DIMENSIONS, ENGINE_INDICATORS, ENGINE_BLOCKERS, ENGINE_VALIDATION]
    if all(p.exists() for p in required):
        return

    try:
        from fito_aimm.aimm_engine import execute_aimm_engine
    except Exception as exc:
        missing = ", ".join(str(p) for p in required if not p.exists())
        raise RuntimeError(f"Outputs do motor AIMM ausentes e não foi possível importar aimm_engine. Ausentes: {missing}. Erro: {exc}") from exc

    result = execute_aimm_engine()
    if result.get("errors"):
        raise RuntimeError(f"Falha ao executar motor AIMM como pré-etapa do dashboard: {result['errors']}")


def classify_readiness(overall: dict[str, str], blockers: list[dict[str, str]]) -> tuple[str, str]:
    final_allowed = overall.get("pode_ser_usado_como_score_final", "não")
    critical = sum(1 for b in blockers if b.get("criticidade") == "alta")
    if final_allowed == "não" or critical > 0:
        return "preliminar_com_bloqueios", "Score estrutural apenas para teste de arquitetura; há bloqueios críticos ativos."
    return "preliminar_sem_bloqueio_critico", "Resultado ainda preliminar, mas sem bloqueio crítico registrado."


def build_cards(cards_seed, overall, dimensions, indicators, blockers):
    cards = []
    counts = {
        "aimm_indicator_scores.csv": len(indicators),
        "aimm_dimension_scores.csv": len(dimensions),
        "aimm_blockers_report.csv": len(blockers),
    }

    for seed in cards_seed:
        source = seed["arquivo_origem"]
        field = seed["campo_origem"]
        if source == "aimm_overall_score.csv":
            value = overall.get(field, "")
        elif field == "count":
            value = counts.get(source, 0)
        else:
            value = ""
        cards.append({
            "id_card": seed["id_card"],
            "titulo": seed["titulo"],
            "tipo": seed["tipo"],
            "valor": value,
            "status": "preliminar",
            "interpretacao": seed["regra_exibicao"],
            "trava": "não usar como decisão final",
        })
    return cards


def build_dimension_view(dimensions):
    rows = []
    for d in dimensions:
        rows.append({
            "dimensao_aimm": d.get("dimensao_aimm", ""),
            "papel": d.get("papel", ""),
            "peso": d.get("peso", ""),
            "indicadores_considerados": d.get("indicadores_considerados", ""),
            "indicadores_bloqueados_ou_baixa_prontidao": d.get("indicadores_bloqueados_ou_baixa_prontidao", ""),
            "score_dimensao_preliminar": d.get("score_dimensao_preliminar", ""),
            "faixa_score_dimensao": d.get("faixa_score_dimensao", ""),
            "status_dimensao": d.get("status_dimensao", ""),
            "mensagem_executiva": f"{d.get('dimensao_aimm','')} = {d.get('score_dimensao_preliminar','')} ({d.get('status_dimensao','')})",
        })
    return rows


def build_executive_summary(overall, dimensions, indicators, blockers, rules):
    readiness, interpretation = classify_readiness(overall, blockers)
    high_blockers = [b for b in blockers if b.get("criticidade") == "alta"]
    return [{
        "projeto": (rules.get("projeto") or {}).get("nome", "Fito+ Amazônia"),
        "rodada_base": "4.16",
        "rodada_output": "4.17",
        "score_estrutural_preliminar": overall.get("score_estrutural_preliminar", ""),
        "faixa_score_estrutural": overall.get("faixa_score_estrutural", ""),
        "penalidade_risco_preliminar": overall.get("risk_penalty_preliminar", ""),
        "fator_monitoramento_preliminar": overall.get("monitoring_factor_preliminar", ""),
        "indicadores_processados": str(len(indicators)),
        "dimensoes_processadas": str(len(dimensions)),
        "bloqueios_ativos": str(len(blockers)),
        "bloqueios_criticos": str(len(high_blockers)),
        "status_prontidao": readiness,
        "interpretacao_executiva": interpretation,
        "pode_ser_usado_como_score_final": overall.get("pode_ser_usado_como_score_final", "não"),
        "trava": "não aprova orçamento, OSC, espécie, produto, rota regulatória ou score AIMM final",
    }]


def build_manifest(outputs: dict[str, Path]):
    rows = []
    for key, path in outputs.items():
        rows.append({
            "id_output": key,
            "arquivo": str(path),
            "existe": "sim" if path.exists() else "não",
            "tipo": path.suffix.replace(".", "") or "arquivo",
            "uso": "arquivo gerado pela Rodada 4.17",
            "status": "ativo",
        })
    return rows


def build_evidence(summary, cards, dimensions, blockers):
    s = summary[0]
    return [{
        "id_evidencia": "EVD_AIMM_DASHBOARD_4_17",
        "id_fonte": "AIMM_DASHBOARD_OUTPUTS",
        "id_indicador": "GAP; INTENSIDADE; MERCADO; RISCO; MONITORAMENTO",
        "tipo_evidencia": "painel_resumo_executivo",
        "pergunta_ou_lacuna": "O sistema gerou uma camada de outputs executivos auditáveis para leitura do motor AIMM?",
        "url_ou_arquivo": "data/processed/aimm_executive_summary.csv; outputs/reports/aimm_executive_summary.md",
        "titulo_documento": "Painel e resumo executivo da calculadora AIMM — Rodada 4.17",
        "pagina_tabela_secao": "executive_summary; dashboard_cards; dimension_view; output_manifest",
        "trecho_original_ou_descricao": f"Score estrutural preliminar: {s.get('score_estrutural_preliminar')}; cards: {len(cards)}; dimensões: {len(dimensions)}; bloqueios ativos: {len(blockers)}.",
        "resumo_ptbr": "Evidência de geração de outputs executivos da calculadora; não representa score AIMM final.",
        "valor_extraido": s.get("score_estrutural_preliminar", ""),
        "unidade": "score 0-100",
        "periodo_referencia": "Rodada 4.17",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "consolidação automatizada dos outputs estruturais da Rodada 4.16",
        "nivel_confianca": "médio_para_comunicação; baixo_para_decisão_final",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_validação_substantiva",
        "limitacoes": "Painel usa score preliminar estrutural; mantém bloqueios e lacunas.",
        "uso_na_calculadora": "Saída executiva, trilha de auditoria e base para painel visual futuro.",
        "status_evidencia": "pendente",
    }]


def write_markdown(summary, cards, dimensions, blockers, next_actions):
    s = summary[0]
    lines = []
    lines.append("# Fito+ Amazônia — Resumo Executivo AIMM")
    lines.append("")
    lines.append("## Resultado estrutural preliminar")
    lines.append("")
    lines.append(f"- Score estrutural preliminar: **{s.get('score_estrutural_preliminar')}**")
    lines.append(f"- Faixa: **{s.get('faixa_score_estrutural')}**")
    lines.append(f"- Penalidade de risco preliminar: **{s.get('penalidade_risco_preliminar')}**")
    lines.append(f"- Fator de monitoramento preliminar: **{s.get('fator_monitoramento_preliminar')}**")
    lines.append(f"- Status de prontidão: **{s.get('status_prontidao')}**")
    lines.append("")
    lines.append("> Trava: este resultado é estrutural e preliminar. Não é score AIMM final validado.")
    lines.append("")
    lines.append("## Cards principais")
    lines.append("")
    for c in cards:
        lines.append(f"- **{c['titulo']}**: {c['valor']} — {c['trava']}")
    lines.append("")
    lines.append("## Dimensões AIMM")
    lines.append("")
    lines.append("| Dimensão | Papel | Score preliminar | Status |")
    lines.append("|---|---:|---:|---|")
    for d in dimensions:
        lines.append(f"| {d['dimensao_aimm']} | {d['papel']} | {d['score_dimensao_preliminar']} | {d['status_dimensao']} |")
    lines.append("")
    lines.append("## Bloqueios e lacunas ativos")
    lines.append("")
    for b in blockers:
        lines.append(f"- **{b.get('criticidade','')}** — {b.get('bloqueio','')}: {b.get('efeito_no_score','')}")
    lines.append("")
    lines.append("## Próximas ações")
    lines.append("")
    for a in next_actions:
        lines.append(f"- **{a.get('prioridade','')}** — {a.get('acao','')}: {a.get('justificativa','')}")
    lines.append("")
    lines.append("## Interpretação")
    lines.append("")
    lines.append(s.get("interpretacao_executiva", ""))
    lines.append("")
    lines.append("O score baixo nesta etapa deve ser lido como baixa maturidade de evidências e presença de bloqueios, não como avaliação substantiva definitiva do mérito do projeto.")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def execute_aimm_dashboard() -> dict[str, Any]:
    rules = load_yaml(RULES)
    ensure_engine_outputs()

    cards_seed = read_csv(CARDS_SEED)
    next_actions = read_csv(NEXT_ACTIONS_SEED)

    overall_rows = read_csv(ENGINE_OVERALL)
    dimensions = read_csv(ENGINE_DIMENSIONS)
    indicators = read_csv(ENGINE_INDICATORS)
    blockers = read_csv(ENGINE_BLOCKERS)
    validation = read_csv(ENGINE_VALIDATION)

    if not overall_rows:
        return {"errors": ["aimm_overall_score.csv vazio"]}
    overall = overall_rows[0]

    summary = build_executive_summary(overall, dimensions, indicators, blockers, rules)
    cards = build_cards(cards_seed, overall, dimensions, indicators, blockers)
    dim_view = build_dimension_view(dimensions)

    outputs = {
        "executive_summary_csv": OUT_EXEC_SUMMARY,
        "dashboard_cards_csv": OUT_CARDS,
        "dimension_view_csv": OUT_DIM_VIEW,
        "next_actions_csv": OUT_NEXT_ACTIONS,
        "evidence_csv": OUT_EVIDENCE,
        "executive_summary_md": OUT_MD,
        "dashboard_payload_json": OUT_JSON,
    }

    write_csv(OUT_EXEC_SUMMARY, summary)
    write_csv(OUT_CARDS, cards)
    write_csv(OUT_DIM_VIEW, dim_view)
    write_csv(OUT_NEXT_ACTIONS, next_actions)
    evidence = build_evidence(summary, cards, dim_view, blockers)
    write_csv(OUT_EVIDENCE, evidence)

    payload = {
        "summary": summary[0],
        "cards": cards,
        "dimensions": dim_view,
        "blockers": blockers,
        "next_actions": next_actions,
        "validation": validation,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    write_markdown(summary, cards, dim_view, blockers, next_actions)
    manifest = build_manifest(outputs)
    write_csv(OUT_MANIFEST, manifest)

    return {
        "errors": [],
        "score": summary[0]["score_estrutural_preliminar"],
        "status": summary[0]["status_prontidao"],
        "cards": len(cards),
        "dimensions": len(dim_view),
        "blockers": len(blockers),
        "next_actions": len(next_actions),
        "outputs": {**{k: str(v) for k, v in outputs.items()}, "output_manifest": str(OUT_MANIFEST)},
    }
