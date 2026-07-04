
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/aimm_engine_rules.yaml")
INPUTS = Path("data/reference/aimm_engine_indicator_inputs_seed.csv")
DIM_POLICY = Path("data/reference/aimm_engine_dimension_policy_seed.csv")
BLOCKERS = Path("data/reference/aimm_engine_blockers_seed.csv")
ALIGNMENT = Path("data/reference/aimm_indicator_alignment_seed.csv")
BLOCKED_READINESS_STATUSES = {"bloqueado", "bloqueado_sem_benchmark"}
BLOCKED_REVIEW_STATUS = "bloqueado_revisao_humana"

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


def to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def score_band(score: float, rules: dict[str, Any]) -> str:
    bands = rules.get("faixas_score", {})
    ordered_bands: list[tuple[float, float, str]] = []
    for label, raw_range in bands.items():
        if not isinstance(raw_range, list) or len(raw_range) != 2:
            continue
        min_val = to_float(raw_range[0], None)
        max_val = to_float(raw_range[1], None)
        if min_val is None or max_val is None:
            continue
        ordered_bands.append((min_val, max_val, str(label)))
    ordered_bands.sort(key=lambda r: r[0])

    for min_val, max_val, label in ordered_bands:
        if min_val <= score <= max_val:
            return label
    return "sem_faixa"


def validate_inputs(
    inputs: list[dict[str, str]],
    alignment: list[dict[str, str]],
    dim_policy: list[dict[str, str]],
    blockers: list[dict[str, str]],
    rules: dict[str, Any],
) -> list[str]:
    errors = []
    valid_dims = set(rules.get("dimensoes_canonicas", []))
    valid_subdims = set(rules.get("subdimensoes_permitidas", []))
    valid_axes = set(rules.get("eixos_analiticos_permitidos", []))
    valid_usage = set(rules.get("status_uso_permitidos", []))
    conf_map = rules.get("tratamento_confianca", {})
    readiness_map = rules.get("tratamento_prontidao_benchmark", {})
    policy_dims = {r["dimensao_aimm"] for r in dim_policy}
    alignment_by_id = {r.get("indicator_id", "").strip(): r for r in alignment}

    if policy_dims != valid_dims:
        errors.append(f"Dimensões da política não batem com regras. policy={sorted(policy_dims)} rules={sorted(valid_dims)}")

    weight_sum = 0.0
    for r in dim_policy:
        weight = to_float(r.get("peso"), None)
        if weight is None:
            errors.append(f"dim_policy: peso inválido para dimensão {r.get('dimensao_aimm','')}")
            continue
        weight_sum += weight
    if abs(weight_sum - 1.0) > 0.001:
        errors.append(f"Pesos das dimensões somam {weight_sum}, esperado 1.0")

    if not alignment:
        errors.append("alignment vazio; motor requer mapeamento canônico da Rodada 4.20")

    for i, row in enumerate(alignment, start=2):
        iid = row.get("indicator_id", "").strip()
        if not iid:
            errors.append(f"alignment linha {i}: indicator_id vazio")
            continue
        if row.get("dimensao_canonica", "") not in valid_dims:
            errors.append(f"alignment linha {i}: dimensao_canonica inválida: {row.get('dimensao_canonica')}")
        if row.get("subdimensao", "") not in valid_subdims:
            errors.append(f"alignment linha {i}: subdimensao inválida: {row.get('subdimensao')}")
        if row.get("eixo_analitico", "") not in valid_axes:
            errors.append(f"alignment linha {i}: eixo_analitico inválido: {row.get('eixo_analitico')}")
        if row.get("status_uso", "") not in valid_usage:
            errors.append(f"alignment linha {i}: status_uso inválido: {row.get('status_uso')}")

    seen = set()
    for i, row in enumerate(inputs, start=2):
        iid = row.get("id_indicador", "").strip()
        if not iid:
            errors.append(f"inputs linha {i}: id_indicador vazio")
        if iid in seen:
            errors.append(f"inputs linha {i}: id_indicador duplicado: {iid}")
        seen.add(iid)

        if iid not in alignment_by_id:
            errors.append(f"inputs linha {i}: indicador sem mapeamento canônico 4.20: {iid}")
            continue

        if row.get("nivel_confianca") not in conf_map:
            errors.append(f"inputs linha {i}: nível de confiança inválido: {row.get('nivel_confianca')}")
        if row.get("status_prontidao_benchmark") not in readiness_map:
            errors.append(f"inputs linha {i}: prontidão benchmark inválida: {row.get('status_prontidao_benchmark')}")

        usage_status = alignment_by_id[iid].get("status_uso", "")
        raw = row.get("score_bruto_preliminar", "")
        is_blocked_usage = usage_status.startswith("bloqueado")
        if row.get("status_prontidao_benchmark") in BLOCKED_READINESS_STATUSES or is_blocked_usage:
            # bloqueado pode ficar vazio
            pass
        else:
            val = to_float(raw, None)
            if val is None or val < 0 or val > 100:
                errors.append(f"inputs linha {i}: score fora de 0-100: {raw}")

    aligned_ids = {r.get("indicator_id", "").strip() for r in alignment}
    missing_from_inputs = sorted(i for i in aligned_ids if i and i not in seen)
    if missing_from_inputs:
        errors.append(f"inputs ausentes para indicadores canônicos: {', '.join(missing_from_inputs)}")

    if not blockers:
        errors.append("blockers vazio; motor deve registrar bloqueios/lacunas")

    return errors


def enrich_inputs_with_alignment(inputs: list[dict[str, str]], alignment: list[dict[str, str]]) -> list[dict[str, str]]:
    alignment_by_id = {r.get("indicator_id", "").strip(): r for r in alignment}
    rows: list[dict[str, str]] = []
    for row in inputs:
        iid = row.get("id_indicador", "").strip()
        aligned = alignment_by_id.get(iid, {})
        merged = dict(row)
        merged["dimensao_aimm"] = aligned.get("dimensao_canonica", "")
        merged["subdimensao"] = aligned.get("subdimensao", "")
        merged["eixo_analitico"] = aligned.get("eixo_analitico", "")
        merged["status_uso"] = aligned.get("status_uso", "")
        merged["benchmark_status"] = aligned.get("benchmark_status", "")
        merged["nome_indicador"] = aligned.get("nome_indicador", "")
        rows.append(merged)
    return rows


def calculate_indicator_scores(inputs: list[dict[str, str]], rules: dict[str, Any]) -> list[dict[str, Any]]:
    conf_map = rules["tratamento_confianca"]
    readiness_map = rules["tratamento_prontidao_benchmark"]

    rows = []
    for row in inputs:
        raw_value = to_float(row.get("score_bruto_preliminar"), None)
        parse_issue = raw_value is None
        raw = raw_value if raw_value is not None else 0.0
        confidence_factor = float(conf_map[row["nivel_confianca"]])
        readiness_factor = float(readiness_map[row["status_prontidao_benchmark"]])
        adjusted = raw * confidence_factor * readiness_factor

        blocked_usage = row.get("status_uso", "").startswith("bloqueado")
        blocked_readiness = row["status_prontidao_benchmark"] in BLOCKED_READINESS_STATUSES
        blocked_confidence = row["nivel_confianca"] == "bloqueado"
        bloqueado = blocked_usage or blocked_readiness or blocked_confidence
        invalid_or_missing = parse_issue and not bloqueado
        if invalid_or_missing:
            bloqueado = True
        if bloqueado:
            adjusted = 0.0

        limitation_parts = [str(row.get("limitacao", "")).strip()]
        if invalid_or_missing:
            limitation_parts.append("score_bruto_invalido_ou_ausente")
        limitation = " | ".join(p for p in limitation_parts if p)

        rows.append({
            "id_indicador": row["id_indicador"],
            "nome_indicador": row.get("nome_indicador", ""),
            "dimensao_aimm": row["dimensao_aimm"],
            "subdimensao": row.get("subdimensao", ""),
            "eixo_analitico": row.get("eixo_analitico", ""),
            "status_uso": row.get("status_uso", ""),
            "benchmark_status": row.get("benchmark_status", ""),
            "id_benchmark": row["id_benchmark"],
            "score_bruto_preliminar": f"{raw:.2f}",
            "nivel_confianca": row["nivel_confianca"],
            "fator_confianca": f"{confidence_factor:.2f}",
            "status_prontidao_benchmark": row["status_prontidao_benchmark"],
            "fator_prontidao": f"{readiness_factor:.2f}",
            "score_ajustado_preliminar": f"{adjusted:.2f}",
            "faixa_score_ajustado": score_band(adjusted, rules),
            "bloqueado_para_score_final": "sim" if bloqueado or readiness_factor < 0.75 else "não",
            "dados_invalidos_ou_ausentes": "sim" if invalid_or_missing else "não",
            "limitacao": limitation,
        })
    return rows


def calculate_dimension_scores(indicator_scores: list[dict[str, Any]], dim_policy: list[dict[str, str]], rules: dict[str, Any]) -> list[dict[str, Any]]:
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
            "faixa_score_dimensao": score_band(avg, rules),
            "status_dimensao": "preliminar_com_bloqueios" if blocked else "preliminar",
            "limitacao": policy.get("descricao", ""),
        })
    return rows


def calculate_overall(
    dimension_scores: list[dict[str, Any]],
    indicator_scores: list[dict[str, Any]],
    rules: dict[str, Any],
) -> dict[str, Any]:
    weights = {r["dimensao_aimm"]: float(r["peso"]) for r in dimension_scores}
    dim_score = {r["dimensao_aimm"]: float(r["score_dimensao_preliminar"]) for r in dimension_scores}
    project_score = dim_score.get("project_outcomes", 0.0)
    market_score = dim_score.get("market_outcomes", 0.0)
    score_bruto = (project_score * weights.get("project_outcomes", 0.0)) + (market_score * weights.get("market_outcomes", 0.0))

    risk_indicators = [r for r in indicator_scores if r.get("eixo_analitico") == "risk_assessment"]
    monitoring_indicators = [r for r in indicator_scores if r.get("eixo_analitico") == "monitoring"]
    if risk_indicators:
        risk_penalty = sum(float(r["score_ajustado_preliminar"]) for r in risk_indicators) / len(risk_indicators)
    else:
        risk_penalty = 0.0
    if monitoring_indicators:
        monitor_factor_raw = sum(float(r["score_ajustado_preliminar"]) for r in monitoring_indicators) / len(monitoring_indicators)
    else:
        monitor_factor_raw = 100.0
    monitor_factor = monitor_factor_raw / 100

    score_risk_adjusted = score_bruto * (1 - risk_penalty / 100)
    score_confidence_adjusted = score_risk_adjusted * monitor_factor

    return {
        "id_resultado": "AIMM_ENGINE_PRELIMINAR_4_16",
        "score_project_outcomes_preliminar": f"{project_score:.2f}",
        "score_market_outcomes_preliminar": f"{market_score:.2f}",
        "score_bruto_beneficio_preliminar": f"{score_bruto:.2f}",
        "risk_penalty_preliminar": f"{risk_penalty:.2f}",
        "monitoring_factor_preliminar": f"{monitor_factor:.2f}",
        "score_ajustado_risco_preliminar": f"{score_risk_adjusted:.2f}",
        "score_estrutural_preliminar": f"{score_confidence_adjusted:.2f}",
        "faixa_score_estrutural": score_band(score_confidence_adjusted, rules),
        "status_resultado": "preliminar",
        "pode_ser_usado_como_score_final": "não",
        "gate_liberacao_final": "",
        "interpretacao": "Score estrutural canônico preliminar baseado em project_outcomes e market_outcomes; não representa AIMM final validado.",
    }


def evaluate_release_gate(
    errors: list[str],
    indicator_scores: list[dict[str, Any]],
    dimension_scores: list[dict[str, Any]],
    blockers: list[dict[str, str]],
    rules: dict[str, Any],
) -> tuple[str, list[str]]:
    gate = rules.get("regras_liberacao_final", {})
    reasons: list[str] = []
    valid_dims = set(rules.get("dimensoes_canonicas", []))

    if gate.get("exige_sem_erros_validacao", True) and errors:
        reasons.append("erros_estruturais")
    if gate.get("exige_dimensoes_canonicas_completas", True):
        dims = {d.get("dimensao_aimm", "") for d in dimension_scores}
        if dims != valid_dims:
            reasons.append("dimensoes_canonicas_incompletas")
    if gate.get("exige_sem_indicador_bloqueado", True):
        if any(r.get("bloqueado_para_score_final") == "sim" for r in indicator_scores):
            reasons.append("indicadores_bloqueados")
    if gate.get("exige_sem_bloqueios_criticos", True):
        if any((b.get("criticidade") or "").strip().lower() == "alta" for b in blockers):
            reasons.append("bloqueios_criticos")
    if gate.get("exige_sem_bloqueio_revisao_humana", True):
        if any((r.get("status_uso") or "").strip() == BLOCKED_REVIEW_STATUS for r in indicator_scores):
            reasons.append("revisao_humana_pendente")

    explicit_permission = bool(gate.get("permitir_score_final", False))
    if not explicit_permission:
        reasons.append("gate_desabilitado_por_config")

    return ("sim" if explicit_permission and not reasons else "não"), reasons


def generate_validation(errors: list[str], indicator_scores, dimension_scores, overall, blockers, rules, gate_reasons: list[str]) -> list[dict[str, str]]:
    rows = []
    expected_dims = len(rules.get("dimensoes_canonicas", []))
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
        "status": "ok" if len(dimension_scores) == expected_dims else "erro",
        "valor": str(len(dimension_scores)),
        "mensagem": "Dimensões AIMM processadas."
    })
    rows.append({
        "checagem": "resultado_final_bloqueado",
        "status": "ok" if overall.get("pode_ser_usado_como_score_final", "não") == "sim" else "trava",
        "valor": overall.get("pode_ser_usado_como_score_final", "não"),
        "mensagem": "Resultado bloqueado por gate configurável." if gate_reasons else "Gate de liberação atendido."
    })
    rows.append({
        "checagem": "gate_liberacao_final",
        "status": "trava" if gate_reasons else "ok",
        "valor": "|".join(gate_reasons),
        "mensagem": "Critérios formais de liberação final avaliados."
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
    return [{
        "id_evidencia": "EVD_AIMM_ENGINE_4_16",
        "id_fonte": "AIMM_ENGINE_INITIAL",
        "id_indicador": "PROJECT_OUTCOMES; MARKET_OUTCOMES",
        "tipo_evidencia": "motor_calculo_preliminar",
        "pergunta_ou_lacuna": "O motor canônico consegue integrar project_outcomes e market_outcomes, com eixos de risco/monitoramento e bloqueios, em score estrutural preliminar?",
        "url_ou_arquivo": "data/processed/aimm_indicator_scores.csv; data/processed/aimm_dimension_scores.csv; data/processed/aimm_overall_score.csv",
        "titulo_documento": "Motor de cálculo inicial da calculadora AIMM — Rodada 4.16",
        "pagina_tabela_secao": "indicator_scores; dimension_scores; overall_score; blockers",
        "trecho_original_ou_descricao": f"Indicadores processados: {len(indicator_scores)}; dimensões: {len(dimension_scores)}; bloqueios: {len(blockers)}; score estrutural preliminar: {overall.get('score_estrutural_preliminar')}.",
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
    alignment = read_csv(ALIGNMENT)
    dim_policy = read_csv(DIM_POLICY)
    blockers = read_csv(BLOCKERS)

    errors = validate_inputs(inputs, alignment, dim_policy, blockers, rules)
    if errors:
        gate = evaluate_release_gate(errors, [], [], blockers, rules)
        validation = generate_validation(errors, [], [], {"pode_ser_usado_como_score_final": "não"}, blockers, rules, gate[1])
        write_csv(OUT_VALIDATION, validation)
        return {"errors": errors}

    canonical_inputs = enrich_inputs_with_alignment(inputs, alignment)
    indicator_scores = calculate_indicator_scores(canonical_inputs, rules)
    dimension_scores = calculate_dimension_scores(indicator_scores, dim_policy, rules)
    overall = calculate_overall(dimension_scores, indicator_scores, rules)
    final_allowed, gate_reasons = evaluate_release_gate([], indicator_scores, dimension_scores, blockers, rules)
    overall["pode_ser_usado_como_score_final"] = final_allowed
    overall["gate_liberacao_final"] = "|".join(gate_reasons)
    overall["status_resultado"] = "preliminar_sem_bloqueios" if final_allowed == "sim" else "preliminar_com_bloqueios"
    validation = generate_validation([], indicator_scores, dimension_scores, overall, blockers, rules, gate_reasons)
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
