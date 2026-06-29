
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/budget_components_rules.yaml")
COMPONENTS = Path("data/reference/budget_components_seed.csv")
ASSUMPTIONS = Path("data/reference/cost_assumption_registry_seed.csv")
PHASES = Path("data/reference/budget_phase_schedule_seed.csv")
AIMM_LINKS = Path("data/reference/budget_aimm_linkage_seed.csv")

OUT_COMPONENTS = Path("data/processed/budget_components.csv")
OUT_ASSUMPTIONS = Path("data/processed/cost_assumption_registry.csv")
OUT_PHASES = Path("data/processed/budget_phase_schedule.csv")
OUT_AIMM = Path("data/processed/budget_aimm_linkage.csv")
OUT_SUMMARY = Path("data/processed/budget_summary.csv")
OUT_VALIDATION = Path("data/processed/budget_validation_report.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_budget_components.csv")


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
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def check_unique(rows: list[dict[str, str]], field: str, label: str) -> list[str]:
    seen = set()
    errors = []
    for i, row in enumerate(rows, start=2):
        key = row.get(field, "").strip()
        if not key:
            errors.append(f"{label}: linha {i} sem {field}")
        elif key in seen:
            errors.append(f"{label}: {field} duplicado: {key}")
        seen.add(key)
    return errors


def validate_inputs(components, assumptions, phases, aimm_links, rules) -> list[str]:
    errors = []
    errors.extend(check_unique(components, "id_componente", "budget_components"))
    errors.extend(check_unique(assumptions, "id_pressuposto", "cost_assumption_registry"))

    total_expected = to_float((rules.get("projeto") or {}).get("investimento_total_brl"))
    total_components = sum(to_float(r.get("valor_brl")) for r in components)
    if round(total_components, 2) != round(total_expected, 2):
        errors.append(f"Total dos componentes = {total_components}, esperado = {total_expected}")

    valid_classes = set(rules.get("classes_gasto", []))
    for i, row in enumerate(components, start=2):
        if row.get("classe_gasto") not in valid_classes:
            errors.append(f"budget_components linha {i}: classe_gasto inválida: {row.get('classe_gasto')}")
        if to_float(row.get("valor_brl")) <= 0:
            errors.append(f"budget_components linha {i}: valor_brl deve ser positivo")

    component_ids = {r["id_componente"] for r in components}
    for i, row in enumerate(phases, start=2):
        cid = row.get("id_componente")
        if cid not in component_ids:
            errors.append(f"budget_phase_schedule linha {i}: id_componente desconhecido: {cid}")
        pct_sum = sum(to_float(row.get(k)) for k in ["ano_1_pct", "ano_2_pct", "ano_3_pct", "avaliacao_anos_4_5_pct", "impacto_anos_6_10_pct"])
        if round(pct_sum, 6) != 100:
            errors.append(f"budget_phase_schedule linha {i}: percentuais somam {pct_sum}, esperado 100")

    valid_dims = set(rules.get("dimensoes_aimm_relacionadas", []))
    for i, row in enumerate(aimm_links, start=2):
        if row.get("dimensao_aimm") not in valid_dims:
            errors.append(f"budget_aimm_linkage linha {i}: dimensão AIMM inválida: {row.get('dimensao_aimm')}")

    return errors


def enrich_components(components: list[dict[str, str]], total: float) -> list[dict[str, Any]]:
    out = []
    for row in components:
        value = to_float(row.get("valor_brl"))
        percent = (value / total * 100) if total else 0
        r = dict(row)
        r["valor_brl_formatado"] = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        r["percentual_total"] = f"{percent:.2f}"
        r["status_orcamento"] = "preliminar_para_calculadora"
        r["exige_memoria_calculo"] = "sim"
        r["exige_pesquisa_precos"] = "sim"
        r["trava_execucao"] = "não_autoriza_execucao"
        out.append(r)
    return out


def build_phase_schedule_values(components: list[dict[str, str]], phases: list[dict[str, str]]) -> list[dict[str, Any]]:
    value_by_id = {r["id_componente"]: to_float(r["valor_brl"]) for r in components}
    out = []
    for row in phases:
        cid = row["id_componente"]
        total = value_by_id[cid]
        r = dict(row)
        for pct_col, val_col in [
            ("ano_1_pct", "ano_1_brl"),
            ("ano_2_pct", "ano_2_brl"),
            ("ano_3_pct", "ano_3_brl"),
            ("avaliacao_anos_4_5_pct", "avaliacao_anos_4_5_brl"),
            ("impacto_anos_6_10_pct", "impacto_anos_6_10_brl"),
        ]:
            r[val_col] = f"{total * to_float(row.get(pct_col)) / 100:.2f}"
        r["valor_total_brl"] = f"{total:.2f}"
        out.append(r)
    return out


def build_summary(components: list[dict[str, str]], phase_values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(to_float(r["valor_brl"]) for r in components)
    by_class: dict[str, float] = {}
    for r in components:
        by_class[r["classe_gasto"]] = by_class.get(r["classe_gasto"], 0.0) + to_float(r["valor_brl"])

    summary = [
        {"indicador": "investimento_total_brl", "valor": f"{total:.2f}", "unidade": "BRL", "observacao": "Total preliminar informado pelo projeto."},
        {"indicador": "numero_componentes", "valor": str(len(components)), "unidade": "componentes", "observacao": "Componentes orçamentários de arquitetura."},
    ]
    for cls, value in sorted(by_class.items()):
        summary.append({
            "indicador": f"valor_{cls.lower()}",
            "valor": f"{value:.2f}",
            "unidade": "BRL",
            "observacao": f"Total preliminar classificado como {cls}.",
        })
        summary.append({
            "indicador": f"percentual_{cls.lower()}",
            "valor": f"{(value / total * 100) if total else 0:.2f}",
            "unidade": "%",
            "observacao": f"Participação de {cls} no orçamento total.",
        })

    # phase totals
    for col in ["ano_1_brl", "ano_2_brl", "ano_3_brl", "avaliacao_anos_4_5_brl", "impacto_anos_6_10_brl"]:
        value = sum(to_float(r[col]) for r in phase_values)
        summary.append({
            "indicador": f"total_{col}",
            "valor": f"{value:.2f}",
            "unidade": "BRL",
            "observacao": "Distribuição temporal preliminar.",
        })
    return summary


def build_validation_report(errors: list[str], components, total_expected: float, phase_values) -> list[dict[str, str]]:
    rows = []
    total_components = sum(to_float(r.get("valor_brl")) for r in components)
    rows.append({
        "checagem": "total_orcamento",
        "status": "ok" if round(total_components, 2) == round(total_expected, 2) else "erro",
        "valor_observado": f"{total_components:.2f}",
        "valor_esperado": f"{total_expected:.2f}",
        "mensagem": "Total dos componentes fecha o investimento informado."
    })
    phase_total = sum(to_float(r["valor_total_brl"]) for r in phase_values)
    rows.append({
        "checagem": "total_fases",
        "status": "ok" if round(phase_total, 2) == round(total_expected, 2) else "erro",
        "valor_observado": f"{phase_total:.2f}",
        "valor_esperado": f"{total_expected:.2f}",
        "mensagem": "Total das fases corresponde ao investimento informado."
    })
    rows.append({
        "checagem": "status_execucao",
        "status": "trava",
        "valor_observado": "preliminar",
        "valor_esperado": "não_autoriza_execucao",
        "mensagem": "Orçamento preliminar não autoriza contratação, compra ou execução."
    })
    for err in errors:
        rows.append({
            "checagem": "erro_validacao",
            "status": "erro",
            "valor_observado": "",
            "valor_esperado": "",
            "mensagem": err,
        })
    return rows


def generate_evidence(components, assumptions, phase_values, summary):
    total = sum(to_float(r.get("valor_brl")) for r in components)
    top = sorted(components, key=lambda r: to_float(r.get("valor_brl")), reverse=True)[0]
    return [{
        "id_evidencia": "EVD_BUDGET_COMPONENTS_4_14",
        "id_fonte": "BUDGET_COMPONENTS_ARCHITECTURE",
        "id_indicador": "INTENSIDADE; RISCO; MONITORAMENTO; MERCADO; GAP",
        "tipo_evidencia": "orcamento_componentes_pressupostos",
        "pergunta_ou_lacuna": "Como o investimento de R$ 80 milhões está estruturado preliminarmente por componente para alimentar a calculadora AIMM?",
        "url_ou_arquivo": "data/processed/budget_components.csv; data/processed/cost_assumption_registry.csv; data/processed/budget_phase_schedule.csv",
        "titulo_documento": "Orçamento por componente e pressupostos de custo — Rodada 4.14",
        "pagina_tabela_secao": "budget_components; cost_assumption_registry; budget_phase_schedule",
        "trecho_original_ou_descricao": f"Componentes orçamentários: {len(components)}; total: R$ {total:,.2f}; maior componente: {top.get('nome_componente')} (R$ {to_float(top.get('valor_brl')):,.2f}); pressupostos: {len(assumptions)}.",
        "resumo_ptbr": "Evidência de arquitetura orçamentária preliminar para uso na calculadora AIMM; não é orçamento executivo.",
        "valor_extraido": f"{total:.2f}",
        "unidade": "BRL",
        "periodo_referencia": "Rodada 4.14",
        "territorio": "Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
        "metodo_extracao": "estruturação preliminar do investimento informado pelo usuário em componentes, fases e pressupostos",
        "nivel_confianca": "baixo_para_execucao; médio_para_arquitetura_da_calculadora",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_pesquisa_precos_memoria_calculo",
        "limitacoes": "Valores são preliminares; exigem pesquisa de preços, memória de cálculo, fontes, TR/projeto básico e validação técnica.",
        "uso_na_calculadora": "Entrada para intensidade, custo por beneficiário, risco, monitoramento e cenários.",
        "status_evidencia": "pendente",
    }]


def execute_budget_components() -> dict[str, Any]:
    rules = load_yaml(RULES)
    components = read_csv(COMPONENTS)
    assumptions = read_csv(ASSUMPTIONS)
    phases = read_csv(PHASES)
    aimm_links = read_csv(AIMM_LINKS)
    total_expected = to_float((rules.get("projeto") or {}).get("investimento_total_brl"))

    errors = validate_inputs(components, assumptions, phases, aimm_links, rules)
    # Validation report is written even if no errors.
    enriched = enrich_components(components, total_expected)
    phase_values = build_phase_schedule_values(components, phases)
    summary = build_summary(components, phase_values)
    validation = build_validation_report(errors, components, total_expected, phase_values)

    if errors:
        # Still save report for inspection, then fail.
        write_csv(OUT_VALIDATION, validation)
        return {"errors": errors}

    evidence = generate_evidence(components, assumptions, phase_values, summary)

    write_csv(OUT_COMPONENTS, enriched)
    write_csv(OUT_ASSUMPTIONS, assumptions)
    write_csv(OUT_PHASES, phase_values)
    write_csv(OUT_AIMM, aimm_links)
    write_csv(OUT_SUMMARY, summary)
    write_csv(OUT_VALIDATION, validation)
    write_csv(OUT_EVIDENCE, evidence)

    class_totals = {}
    for r in components:
        class_totals[r["classe_gasto"]] = class_totals.get(r["classe_gasto"], 0.0) + to_float(r["valor_brl"])

    return {
        "errors": [],
        "total_budget": total_expected,
        "total_components": len(components),
        "total_assumptions": len(assumptions),
        "total_phase_rows": len(phase_values),
        "total_aimm_links": len(aimm_links),
        "class_totals": class_totals,
        "outputs": {
            "budget_components": str(OUT_COMPONENTS),
            "cost_assumption_registry": str(OUT_ASSUMPTIONS),
            "budget_phase_schedule": str(OUT_PHASES),
            "budget_aimm_linkage": str(OUT_AIMM),
            "budget_summary": str(OUT_SUMMARY),
            "budget_validation_report": str(OUT_VALIDATION),
            "evidence": str(OUT_EVIDENCE),
        }
    }
