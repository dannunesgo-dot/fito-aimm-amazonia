# -*- coding: utf-8 -*-
"""Unit tests for the AIMM 4.20 scoring engine."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fito_aimm.aimm_engine import (
    BLOCKED_READINESS_STATUSES,
    BLOCKED_REVIEW_STATUS,
    BLOCKED_USAGE_STATUSES,
    MONITORING_ONLY_STATUS,
    calculate_dimension_scores,
    calculate_indicator_scores,
    calculate_overall,
    enrich_inputs_with_alignment,
    evaluate_release_gate,
    is_blocked_usage,
    score_band,
    to_float,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RULES: dict = {
    "dimensoes_canonicas": ["project_outcomes", "market_outcomes"],
    "faixas_score": {
        "low": [0, 34],
        "good": [35, 49],
        "strong": [50, 59],
        "excellent": [60, 100],
    },
    "tratamento_confianca": {
        "alto": 1.00,
        "medio": 0.75,
        "baixo": 0.50,
        "bloqueado": 0.00,
    },
    "tratamento_prontidao_benchmark": {
        "benchmark_utilizavel": 1.00,
        "proxy_utilizavel_com_validacao": 0.75,
        "proxy_baixa_confianca": 0.50,
        "bloqueado": 0.00,
        "bloqueado_sem_benchmark": 0.00,
        "revisar": 0.25,
    },
    "status_uso_permitidos": [
        "calculavel_preliminar",
        "proxy_baixa_confianca",
        "bloqueado_sem_benchmark",
        "bloqueado_revisao_humana",
        "apenas_monitoramento",
    ],
    "regras_liberacao_final": {
        "permitir_score_final": False,
        "exige_sem_erros_validacao": True,
        "exige_dimensoes_canonicas_completas": True,
        "exige_sem_indicador_bloqueado": True,
        "exige_sem_bloqueios_criticos": True,
        "exige_sem_bloqueio_revisao_humana": True,
    },
    "eixo_risco": "risk_assessment",
    "eixo_monitoramento": "monitoring",
    "id_resultado_preliminar": "AIMM_ENGINE_TEST",
}

SAMPLE_DIM_POLICY = [
    {"dimensao_aimm": "project_outcomes", "peso": "0.60", "papel": "beneficio", "descricao": "proj"},
    {"dimensao_aimm": "market_outcomes", "peso": "0.40", "papel": "beneficio", "descricao": "mkt"},
]


def _make_indicator(
    iid: str,
    dim: str,
    score: str,
    confianca: str,
    prontidao: str,
    eixo: str = "intensity",
    status_uso: str = "calculavel_preliminar",
    limitacao: str = "",
) -> dict:
    return {
        "id_indicador": iid,
        "nome_indicador": f"Indicador {iid}",
        "dimensao_aimm": dim,
        "subdimensao": "stakeholder_effects",
        "eixo_analitico": eixo,
        "status_uso": status_uso,
        "benchmark_status": "proxy_documentado",
        "id_benchmark": f"BMK_{iid}",
        "score_bruto_preliminar": score,
        "nivel_confianca": confianca,
        "status_prontidao_benchmark": prontidao,
        "limitacao": limitacao,
    }


# ---------------------------------------------------------------------------
# Tests: helpers
# ---------------------------------------------------------------------------


def test_to_float_valid():
    assert to_float("52") == 52.0
    assert to_float("48,5") == 48.5
    assert to_float("0") == 0.0


def test_to_float_empty():
    assert to_float("") == 0.0
    assert to_float(None) == 0.0


def test_to_float_invalid_returns_default():
    assert to_float("abc", default=None) is None
    assert to_float("abc", default=0.0) == 0.0


def test_score_band():
    assert score_band(0, SAMPLE_RULES) == "low"
    assert score_band(34, SAMPLE_RULES) == "low"
    assert score_band(35, SAMPLE_RULES) == "good"
    assert score_band(50, SAMPLE_RULES) == "strong"
    assert score_band(60, SAMPLE_RULES) == "excellent"
    assert score_band(100, SAMPLE_RULES) == "excellent"
    assert score_band(101, SAMPLE_RULES) == "sem_faixa"


def test_is_blocked_usage():
    assert is_blocked_usage("bloqueado_sem_benchmark") is True
    assert is_blocked_usage("bloqueado_revisao_humana") is True
    assert is_blocked_usage("calculavel_preliminar") is False
    assert is_blocked_usage("apenas_monitoramento") is False
    assert is_blocked_usage("") is False
    assert is_blocked_usage(None) is False


def test_constants_consistency():
    assert BLOCKED_REVIEW_STATUS in BLOCKED_USAGE_STATUSES
    assert "bloqueado_sem_benchmark" in BLOCKED_READINESS_STATUSES
    assert MONITORING_ONLY_STATUS == "apenas_monitoramento"


# ---------------------------------------------------------------------------
# Tests: calculate_indicator_scores
# ---------------------------------------------------------------------------


def test_calculate_indicator_scores_basic():
    inputs = [
        _make_indicator("IND_001", "project_outcomes", "60", "alto", "benchmark_utilizavel"),
    ]
    rows = calculate_indicator_scores(inputs, SAMPLE_RULES)
    assert len(rows) == 1
    r = rows[0]
    assert r["score_bruto_preliminar"] == "60.00"
    assert r["fator_confianca"] == "1.00"
    assert r["fator_prontidao"] == "1.00"
    assert float(r["score_ajustado_preliminar"]) == 60.0
    assert r["bloqueado_para_score_final"] == "não"
    assert r["apenas_monitoramento"] == "não"


def test_calculate_indicator_scores_blocked_usage():
    inputs = [
        _make_indicator(
            "IND_BLK", "project_outcomes", "50",
            "medio", "benchmark_utilizavel",
            status_uso="bloqueado_revisao_humana",
        ),
    ]
    rows = calculate_indicator_scores(inputs, SAMPLE_RULES)
    r = rows[0]
    assert float(r["score_ajustado_preliminar"]) == 0.0
    assert r["bloqueado_para_score_final"] == "sim"
    assert r["apenas_monitoramento"] == "não"


def test_calculate_indicator_scores_blocked_readiness():
    inputs = [
        _make_indicator(
            "IND_BLKR", "market_outcomes", "40",
            "medio", "bloqueado_sem_benchmark",
        ),
    ]
    rows = calculate_indicator_scores(inputs, SAMPLE_RULES)
    r = rows[0]
    assert float(r["score_ajustado_preliminar"]) == 0.0
    assert r["bloqueado_para_score_final"] == "sim"


def test_calculate_indicator_scores_monitoring_only():
    inputs = [
        _make_indicator(
            "IND_MON", "project_outcomes", "55",
            "medio", "proxy_utilizavel_com_validacao",
            eixo="monitoring",
            status_uso="apenas_monitoramento",
        ),
    ]
    rows = calculate_indicator_scores(inputs, SAMPLE_RULES)
    r = rows[0]
    # Score is still computed normally
    assert float(r["score_ajustado_preliminar"]) > 0.0
    # But flagged as monitoring-only — excluded from score aggregation
    assert r["apenas_monitoramento"] == "sim"
    assert r["bloqueado_para_score_final"] == "sim"


def test_calculate_indicator_scores_invalid_score():
    inputs = [
        _make_indicator("IND_INV", "project_outcomes", "N/A", "medio", "benchmark_utilizavel"),
    ]
    rows = calculate_indicator_scores(inputs, SAMPLE_RULES)
    r = rows[0]
    assert float(r["score_ajustado_preliminar"]) == 0.0
    assert r["bloqueado_para_score_final"] == "sim"
    assert "score_bruto_invalido_ou_ausente" in r["limitacao"]


# ---------------------------------------------------------------------------
# Tests: calculate_dimension_scores
# ---------------------------------------------------------------------------


def test_calculate_dimension_scores_excludes_monitoring_only():
    """Monitoring-only indicators must not contribute to dimension score average."""
    indicator_scores = [
        {
            "id_indicador": "IND_A",
            "dimensao_aimm": "project_outcomes",
            "eixo_analitico": "intensity",
            "score_ajustado_preliminar": "60.00",
            "bloqueado_para_score_final": "não",
            "apenas_monitoramento": "não",
        },
        {
            "id_indicador": "IND_MON",
            "dimensao_aimm": "project_outcomes",
            "eixo_analitico": "monitoring",
            "score_ajustado_preliminar": "10.00",
            "bloqueado_para_score_final": "sim",
            "apenas_monitoramento": "sim",
        },
    ]
    rows = calculate_dimension_scores(indicator_scores, SAMPLE_DIM_POLICY, SAMPLE_RULES)
    proj_row = next(r for r in rows if r["dimensao_aimm"] == "project_outcomes")
    # Only IND_A contributes; IND_MON must be excluded → score == 60.0
    assert float(proj_row["score_dimensao_preliminar"]) == 60.0


def test_calculate_dimension_scores_empty_dimension():
    indicator_scores: list = []
    rows = calculate_dimension_scores(indicator_scores, SAMPLE_DIM_POLICY, SAMPLE_RULES)
    for row in rows:
        assert float(row["score_dimensao_preliminar"]) == 0.0


# ---------------------------------------------------------------------------
# Tests: calculate_overall — monitoring factor must NOT deflate score
# ---------------------------------------------------------------------------


def test_calculate_overall_no_monitoring_deflation():
    """Monitoring indicators must not reduce the overall score via multiplication."""
    indicator_scores = [
        {
            "id_indicador": "IND_A",
            "dimensao_aimm": "project_outcomes",
            "eixo_analitico": "intensity",
            "score_ajustado_preliminar": "60.00",
            "apenas_monitoramento": "não",
        },
        {
            "id_indicador": "IND_MON",
            "dimensao_aimm": "project_outcomes",
            "eixo_analitico": "monitoring",
            "score_ajustado_preliminar": "20.00",  # low monitoring score
            "apenas_monitoramento": "sim",
        },
    ]
    dimension_scores = [
        {"dimensao_aimm": "project_outcomes", "peso": "0.60", "score_dimensao_preliminar": "60.00"},
        {"dimensao_aimm": "market_outcomes", "peso": "0.40", "score_dimensao_preliminar": "0.00"},
    ]
    overall = calculate_overall(dimension_scores, indicator_scores, SAMPLE_RULES)
    # Expected: score_bruto = 60*0.6 + 0*0.4 = 36.0
    # risk_penalty = 0 (no risk_assessment indicators)
    # score_estrutural = 36.0 * (1 - 0/100) = 36.0
    # monitoring factor must NOT reduce this
    assert float(overall["score_estrutural_preliminar"]) == pytest.approx(36.0)


def test_calculate_overall_risk_penalty_applied():
    """Risk axis indicators must penalize the overall score."""
    indicator_scores = [
        {
            "id_indicador": "IND_RISK",
            "dimensao_aimm": "market_outcomes",
            "eixo_analitico": "risk_assessment",
            "score_ajustado_preliminar": "40.00",
            "apenas_monitoramento": "não",
        },
    ]
    dimension_scores = [
        {"dimensao_aimm": "project_outcomes", "peso": "0.60", "score_dimensao_preliminar": "50.00"},
        {"dimensao_aimm": "market_outcomes", "peso": "0.40", "score_dimensao_preliminar": "50.00"},
    ]
    overall = calculate_overall(dimension_scores, indicator_scores, SAMPLE_RULES)
    # score_bruto = 50*0.6 + 50*0.4 = 50.0
    # risk_penalty = 40.0 (average of risk_assessment indicators)
    # score_estrutural = 50 * (1 - 40/100) = 30.0
    assert float(overall["score_estrutural_preliminar"]) == pytest.approx(30.0)
    assert float(overall["risk_penalty_preliminar"]) == pytest.approx(40.0)


def test_calculate_overall_monitoring_factor_tracked():
    """monitoring_factor_preliminar must still be reported even if not applied to score."""
    indicator_scores = [
        {
            "id_indicador": "IND_MON",
            "dimensao_aimm": "project_outcomes",
            "eixo_analitico": "monitoring",
            "score_ajustado_preliminar": "50.00",
            "apenas_monitoramento": "sim",
        },
    ]
    dimension_scores = [
        {"dimensao_aimm": "project_outcomes", "peso": "0.60", "score_dimensao_preliminar": "40.00"},
        {"dimensao_aimm": "market_outcomes", "peso": "0.40", "score_dimensao_preliminar": "30.00"},
    ]
    overall = calculate_overall(dimension_scores, indicator_scores, SAMPLE_RULES)
    assert "monitoring_factor_preliminar" in overall
    assert float(overall["monitoring_factor_preliminar"]) == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# Tests: evaluate_release_gate
# ---------------------------------------------------------------------------


def test_evaluate_release_gate_blocked_by_config():
    _, reasons = evaluate_release_gate([], [], [], [], SAMPLE_RULES)
    assert "gate_desabilitado_por_config" in reasons


def test_evaluate_release_gate_blocked_by_errors():
    _, reasons = evaluate_release_gate(["erro_x"], [], [], [], SAMPLE_RULES)
    assert "erros_estruturais" in reasons


def test_evaluate_release_gate_blocked_by_human_review():
    ind = [{"status_uso": "bloqueado_revisao_humana", "bloqueado_para_score_final": "sim"}]
    _, reasons = evaluate_release_gate([], ind, [], [], SAMPLE_RULES)
    assert "revisao_humana_pendente" in reasons


# ---------------------------------------------------------------------------
# Tests: integration — full engine run with seed data
# ---------------------------------------------------------------------------


def test_engine_runs_with_seed_data():
    """Smoke test: engine must run with real seed CSV files without errors."""
    import os

    os.chdir(Path(__file__).resolve().parents[1])
    from fito_aimm.aimm_engine import execute_aimm_engine

    result = execute_aimm_engine()
    assert result["errors"] == []
    assert result["total_indicators"] > 0
    assert result["total_dimensions"] == 2
    assert float(result["score"]) > 0.0


def test_engine_seed_score_not_deflated_by_monitoring():
    """After the fix, score must be considerably higher than 3.0 (old deflated value)."""
    import os

    os.chdir(Path(__file__).resolve().parents[1])
    from fito_aimm.aimm_engine import execute_aimm_engine

    result = execute_aimm_engine()
    # Old bugged score was ~2.65 due to monitoring multiplication
    # Correct score based on weighted dimensions and risk penalty only must be > 10
    assert float(result["score"]) > 10.0


def test_engine_output_files_exist():
    """All declared output files must be created by the engine."""
    import os

    os.chdir(Path(__file__).resolve().parents[1])
    from fito_aimm.aimm_engine import execute_aimm_engine

    result = execute_aimm_engine()
    for key, path in result["outputs"].items():
        assert Path(path).exists(), f"Output ausente: {key} -> {path}"


def test_engine_gate_blocks_final_score():
    """Preliminary score must always be blocked from final use (gate config)."""
    import os

    os.chdir(Path(__file__).resolve().parents[1])
    from fito_aimm.aimm_engine import execute_aimm_engine, read_csv

    result = execute_aimm_engine()
    overall = read_csv(Path(result["outputs"]["aimm_overall_score"]))[0]
    assert overall["pode_ser_usado_como_score_final"] == "não"
