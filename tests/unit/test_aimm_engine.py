from fito_aimm.aimm_engine import calculate_overall


def _dimension(dim, papel, peso, score):
    return {
        "dimensao_aimm": dim,
        "papel": papel,
        "peso": str(peso),
        "score_dimensao_preliminar": str(score),
    }


def _indicator(dim, confianca="alto", prontidao="benchmark_utilizavel", bloqueado="não"):
    return {
        "dimensao_aimm": dim,
        "nivel_confianca": confianca,
        "status_prontidao_benchmark": prontidao,
        "bloqueado_para_score_final": bloqueado,
    }


def test_overall_can_be_final_without_critical_blockers_and_with_method_validation():
    rules = {
        "criterios_score_final": {
            "niveis_confianca_aceitos": ["alto"],
            "status_prontidao_aceitos": ["benchmark_utilizavel"],
            "monitoring_factor_minimo": 0.8,
        }
    }
    dimension_scores = [
        _dimension("gap", "beneficio", 0.25, 80),
        _dimension("intensidade", "beneficio", 0.25, 70),
        _dimension("mercado", "beneficio", 0.20, 75),
        _dimension("risco", "penalizador", 0.20, 10),
        _dimension("monitoramento", "confianca", 0.10, 90),
    ]
    indicator_scores = [
        _indicator("gap"),
        _indicator("intensidade"),
        _indicator("mercado"),
        _indicator("risco"),
        _indicator("monitoramento"),
    ]

    overall = calculate_overall(dimension_scores, indicator_scores, [], rules)

    assert overall["pode_ser_usado_como_score_final"] == "sim"
    assert overall["validacao_metodologica_concluida"] == "sim"
    assert overall["sem_bloqueadores_criticos"] == "sim"


def test_overall_stays_blocked_with_critical_blockers():
    rules = {"criterios_score_final": {}}
    dimension_scores = [
        _dimension("gap", "beneficio", 0.25, 80),
        _dimension("intensidade", "beneficio", 0.25, 70),
        _dimension("mercado", "beneficio", 0.20, 75),
        _dimension("risco", "penalizador", 0.20, 10),
        _dimension("monitoramento", "confianca", 0.10, 90),
    ]
    indicator_scores = [_indicator("gap")]
    blockers = [{"criticidade": "alta"}]

    overall = calculate_overall(dimension_scores, indicator_scores, blockers, rules)

    assert overall["pode_ser_usado_como_score_final"] == "não"
    assert overall["sem_bloqueadores_criticos"] == "não"
