
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/aimm_engine_rules.yaml")
INPUTS = Path("data/reference/aimm_engine_indicator_inputs_seed.csv")
DIM_POLICY = Path("data/reference/aimm_engine_dimension_policy_seed.csv")
BLOCKERS = Path("data/reference/aimm_engine_blockers_seed.csv")

OUT_INDICATOR = Path("data/processed/aimm_indicator_scores.csv")
OUT_DIMENSION = Path("data/processed/aimm_dimension_scores.csv")
OUT_OVERALL = Path("data/processed/aimm_overall_score.csv")
OUT_BLOCKERS = Path("data/processed/aimm_blockers_report.csv")
OUT_VALIDATION = Path("data/processed/aimm_engine_validation_report.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_aimm_engine.csv")


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


def to_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def score_band(score: float) -> str:
    if score <= 20:
        return "muito_baixo"
    if score <= 40:
        return "baixo"
    if score <= 60:
        return "medio"
    if score <= 80:
        return "alto"
    return "muito_alto"


def validate_inputs(inputs: list[dict[str, str]], dim_policy: list[dict[str, str]], blockers: list[dict[str, str]], rules: dict[str, Any]) -> list[str]:
    errors = []
    valid_dims = set(rules.get("dimensoes", []))
    conf_map = rules.get("tratamento_confianca", {})
    readiness_map = rules.get("tratamento_prontidao_benchmark", {})
    policy_dims = {r["dimensao_aimm"] for r in dim_policy}

    if policy_dims != valid_dims:
        errors.append(f"Dimensões da política não batem com regras. policy={sorted(policy_dims)} rules={sorted(valid_dims)}")

    weight_sum = sum(to_float(r.get("peso"), 0.0) or 0.0 for r in dim_policy)
    if abs(weight_sum - 1.0) > 0.001:
        errors.append(f"Pesos das dimensões somam {weight_sum}, esperado 1.0")

    seen = set()
    for i, row in enumerate(inputs, start=2):
        iid = row.get("id_indicador", "").strip()
        if not iid:
            errors.append(f"inputs linha {i}: id_indicador vazio")
        if iid in seen:
            errors.append(f"inputs linha {i}: id_indicador duplicado: {iid}")
        seen.add(iid)

        dim = row.get("dimensao_aimm", "")
        if dim not in valid_dims:
            errors.append(f"inputs linha {i}: dimensão inválida: {dim}")
        if row.get("nivel_confianca") not in conf_map:
            errors.append(f"inputs linha {i}: nível de confiança inválido: {row.get('nivel_confianca')}")
        if row.get("status_prontidao_benchmark") not in readiness_map:
            errors.append(f"inputs linha {i}: prontidão benchmark inválida: {row.get('status_prontidao_benchmark')}")
        raw = row.get("score_bruto_preliminar", "")
        if row.get("status_prontidao_benchmark") == "bloqueado":
            # bloqueado pode ficar vazio
            pass
        else:
            val = to_float(raw, None)
            if val is None or val < 0 or val > 100:
                errors.append(f"inputs linha {i}: score fora de 0-100: {raw}")

    if not blockers:
        errors.append("blockers vazio; motor deve registrar bloqueios/lacunas")

    return errors


def calculate_indicator_scores(inputs: list[dict[str, str]], rules: dict[str, Any]) -> list[dict[str, Any]]:
    conf_map = rules["tratamento_confianca"]
    readiness_map = rules["tratamento_prontidao_benchmark"]

    rows = []
    for row in inputs:
        raw = to_float(row.get("score_bruto_preliminar"), 0.0) or 0.0
        confidence_factor = float(conf_map[row["nivel_confianca"]])
        readiness_factor = float(readiness_map[row["status_prontidao_benchmark"]])
        adjusted = raw * confidence_factor * readiness_factor

        bloqueado = row["status_prontidao_benchmark"] == "bloqueado" or row["nivel_confianca"] == "bloqueado"
        if bloqueado:
            adjusted = 0.0

        rows.append({
            "id_indicador": row["id_indicador"],
            "dimensao_aimm": row["dimensao_aimm"],
            "id_benchmark": row["id_benchmark"],
            "score_bruto_preliminar": f"{raw:.2f}",
            "nivel_confianca": row["nivel_confianca"],
            "fator_confianca": f"{confidence_factor:.2f}",
            "status_prontidao_benchmark": row["status_prontidao_benchmark"],
            "fator_prontidao": f"{readiness_factor:.2f}",
            "score_ajustado_preliminar": f"{adjusted:.2f}",
            "faixa_score_ajustado": score_band(adjusted),
            "bloqueado_para_score_final": "sim" if bloqueado or readiness_factor < 0.75 else "não",
            "limitacao": row.get("limitacao", ""),
        })
    return rows


def calculate_dimension_scores(indicator_scores: list[dict[str, Any]], dim_policy: list[dict[str, str]]) -> list[dict[str, Any]]:
    policy_by_dim = {r["dimensao_aimm"]: r for r in dim_policy}
    rows = []

    for dim, policy in policy_by_dim.items():
        members = [r for r in indicator_scores if r["dimensao_aimm"] == dim]
        if not members:
            avg = 0.0
            blocked = 0
        else:
            avg = sum(float(r["score_ajustado_preliminar"]) for r in members) / len(members)
            blocked = sum(1 for r in members if r["bloqueado_para_score_final"] == "sim")

        rows.append({
            "dimensao_aimm": dim,
            "papel": policy["papel"],
            "peso": f"{float(policy['peso']):.2f}",
            "indicadores_considerados": str(len(members)),
            "indicadores_bloqueados_ou_baixa_prontidao": str(blocked),
            "score_dimensao_preliminar": f"{avg:.2f}",
            "faixa_score_dimensao": score_band(avg),
            "status_dimensao": "preliminar_com_bloqueios" if blocked else "preliminar",
            "limitacao": policy.get("descricao", ""),
        })
    return rows


def calculate_overall(dimension_scores: list[dict[str, Any]]) -> dict[str, Any]:
    # Benefícios: gap, intensidade, mercado.
    benefit_dims = [r for r in dimension_scores if r["papel"] == "beneficio"]
    risk_dims = [r for r in dimension_scores if r["papel"] == "penalizador"]
    monitor_dims = [r for r in dimension_scores if r["papel"] == "confianca"]

    weighted_benefit_num = sum(float(r["score_dimensao_preliminar"]) * float(r["peso"]) for r in benefit_dims)
    weighted_benefit_den = sum(float(r["peso"]) for r in benefit_dims) or 1.0
    score_bruto = weighted_benefit_num / weighted_benefit_den

    risk_penalty = sum(float(r["score_dimensao_preliminar"]) for r in risk_dims) / (len(risk_dims) or 1)
    monitor_factor_raw = sum(float(r["score_dimensao_preliminar"]) for r in monitor_dims) / (len(monitor_dims) or 1)
    monitor_factor = monitor_factor_raw / 100

    score_risk_adjusted = score_bruto * (1 - risk_penalty / 100)
    score_confidence_adjusted = score_risk_adjusted * monitor_factor

    return {
        "id_resultado": "AIMM_ENGINE_PRELIMINAR_4_16",
        "score_bruto_beneficio_preliminar": f"{score_bruto:.2f}",
        "risk_penalty_preliminar": f"{risk_penalty:.2f}",
        "monitoring_factor_preliminar": f"{monitor_factor:.2f}",
        "score_ajustado_risco_preliminar": f"{score_risk_adjusted:.2f}",
        "score_estrutural_preliminar": f"{score_confidence_adjusted:.2f}",
        "faixa_score_estrutural": score_band(score_confidence_adjusted),
        "status_resultado": "preliminar_com_bloqueios",
        "pode_ser_usado_como_score_final": "não",
        "interpretacao": "Score estrutural inicial para testar o motor. Não representa AIMM final validado.",
    }


def generate_validation(errors: list[str], indicator_scores, dimension_scores, overall, blockers) -> list[dict[str, str]]:
    rows = []
    rows.append({
        "checagem": "erros_validacao",
        "status": "ok" if not errors else "erro",
        "valor": str(len(errors)),
        "mensagem": "Sem erros estruturais." if not errors else "Há erros estruturais."
    })
    rows.append({
        "checagem": "indicadores_processados",
        "status": "ok" if indicator_scores else "erro",
        "valor": str(len(indicator_scores)),
        "mensagem": "Indicadores processados pelo motor."
    })
    rows.append({
        "checagem": "dimensoes_processadas",
        "status": "ok" if len(dimension_scores) == 5 else "erro",
        "valor": str(len(dimension_scores)),
        "mensagem": "Dimensões AIMM processadas."
    })
    rows.append({
        "checagem": "resultado_final_bloqueado",
        "status": "trava",
        "valor": overall.get("pode_ser_usado_como_score_final", "não"),
        "mensagem": "Resultado não pode ser usado como score final validado."
    })
    rows.append({
        "checagem": "bloqueios_registrados",
        "status": "ok" if blockers else "erro",
        "valor": str(len(blockers)),
        "mensagem": "Bloqueios/lacunas ativos registrados."
    })
    for err in errors:
        rows.append({"checagem": "erro", "status": "erro", "valor": "", "mensagem": err})
    return rows


def generate_evidence(indicator_scores, dimension_scores, overall, blockers):
    # CORRIGIDO em refactor/phase1: Strings truncadas expandidas
    score_estrutural = overall.get("score_estrutural_preliminar", "N/A")
    num_indicators = len(indicator_scores)
    num_dimensions = len(dimension_scores)
    num_blockers = len(blockers)
    
    descricao = (
        f"Indicadores processados: {num_indicators}; "
        f"dimensões: {num_dimensions}; "
        f"bloqueios: {num_blockers}; "
        f"score estrutural preliminar: {score_estrutural}"
    )
    
    return [{
        "id_evidencia": "EVD_AIMM_ENGINE_4_16",
        "id_fonte": "AIMM_ENGINE_INITIAL",
        "id_indicador": "GAP; INTENSIDADE; MERCADO; RISCO; MONITORAMENTO",
        "tipo_evidencia": "motor_calculo_preliminar",
        "pergunta_ou_lacuna": "O motor inicial consegue integrar indicadores, benchmarks/proxies, risco, monitoramento e bloqueios em um score estrutural preliminar?",
        "url_ou_arquivo": "data/processed/aimm_indicator_scores.csv; data/processed/aimm_dimension_scores.csv; data/processed/aimm_overall_score.csv",
        "titulo_documento": "Motor de cálculo inicial da calculadora AIMM — Rodada 4.16",
        "pagina_tabela_secao": "indicator_scores; dimension_scores; overall_score; blockers",
        "trecho_original_ou_descricao": descricao,
        "resumo_ptbr": "Evidência de funcionamento estrutural do motor inicial da calculadora; não representa score AIMM final.",
        "valor_extraido": overall.get("score_estrutural_preliminar", ""),
        "unidade": "score 0-100",
        "periodo_referencia": "Rodada 4.16",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "cálculo automatizado com indicadores seed, fatores de confiança, prontidão de benchmark, penalização de risco e fator de monitoramento",
        "nivel_confianca": "baixo_para_decisao; médio_para_teste_estrutural",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_validacao_metodologica_substantiva",
        "limitacoes": "Score preliminar usa proxies e lacunas; não deve ser usado como resultado final ou decisão de investimento.",
        "uso_na_calculadora": "Teste inicial do motor de cálculo AIMM adaptado.",
        "status_evidencia": "pendente",
    }]


def execute_aimm_engine() -> dict[str, Any]:
    rules = load_yaml(RULES)
    inputs = read_csv(INPUTS)
    dim_policy = read_csv(DIM_POLICY)
    blockers = read_csv(BLOCKERS)

    errors = validate_inputs(inputs, dim_policy, blockers, rules)
    if errors:
        validation = generate_validation(errors, [], [], {"pode_ser_usado_como_score_final": "não"}, blockers)
        write_csv(OUT_VALIDATION, validation)
        return {"errors": errors}

    indicator_scores = calculate_indicator_scores(inputs, rules)
    dimension_scores = calculate_dimension_scores(indicator_scores, dim_policy)
    overall = calculate_overall(dimension_scores)
    validation = generate_validation([], indicator_scores, dimension_scores, overall, blockers)
    evidence = generate_evidence(indicator_scores, dimension_scores, overall, blockers)

    write_csv(OUT_INDICATOR, indicator_scores)
    write_csv(OUT_DIMENSION, dimension_scores)
    write_csv(OUT_OVERALL, [overall])
    write_csv(OUT_BLOCKERS, blockers)
    write_csv(OUT_VALIDATION, validation)
    write_csv(OUT_EVIDENCE, evidence)

    return {
        "errors": [],
        "total_indicators": len(indicator_scores),
        "total_dimensions": len(dimension_scores),
        "total_blockers": len(blockers),
        "score": overall["score_estrutural_preliminar"],
        "risk_penalty": overall["risk_penalty_preliminar"],
        "monitoring_factor": overall["monitoring_factor_preliminar"],
        "outputs": {
            "aimm_indicator_scores": str(OUT_INDICATOR),
            "aimm_dimension_scores": str(OUT_DIMENSION),
            "aimm_overall_score": str(OUT_OVERALL),
            "aimm_blockers_report": str(OUT_BLOCKERS),
            "aimm_engine_validation_report": str(OUT_VALIDATION),
            "evidence": str(OUT_EVIDENCE),
        }
    }
