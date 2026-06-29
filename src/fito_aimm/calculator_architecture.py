
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/calculator_architecture_rules.yaml")
SEED_SCHEMA = Path("data/reference/calculator_schema_seed.csv")
SEED_SCORING = Path("data/reference/scoring_model_spec_seed.csv")
SEED_FORMULAS = Path("data/reference/formulas_registry_seed.csv")
SEED_LAYERS = Path("data/reference/calculator_layers_map_seed.csv")
SEED_INPUTS = Path("data/reference/calculator_input_requirements_seed.csv")
DIMENSIONS = Path("data/reference/calculator_dimensions.csv")

OUT_SCHEMA = Path("data/processed/calculator_schema.csv")
OUT_SCORING = Path("data/processed/scoring_model_spec.csv")
OUT_FORMULAS = Path("data/processed/formulas_registry.csv")
OUT_LAYERS = Path("data/processed/calculator_layers_map.csv")
OUT_INPUTS = Path("data/processed/calculator_input_requirements.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_calculator_architecture.csv")


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


def validate_schema(schema: list[dict[str, str]], rules: dict[str, Any]) -> list[str]:
    errors = []
    required = ["id_indicador", "nome_tecnico", "camada", "dimensao", "descricao", "formula_conceitual", "unidade", "fonte_prevista", "periodicidade", "nivel_confianca_inicial", "limitacao"]
    valid_dims = set(rules.get("dimensoes_aimm", []))
    valid_layers = set((rules.get("camadas", {}) or {}).keys())

    errors.extend(check_unique(schema, "id_indicador", "calculator_schema"))

    for i, row in enumerate(schema, start=2):
        for field in required:
            if not row.get(field, "").strip():
                errors.append(f"calculator_schema linha {i}: campo obrigatório vazio: {field}")
        if row.get("dimensao") not in valid_dims:
            errors.append(f"calculator_schema linha {i}: dimensão inválida: {row.get('dimensao')}")
        if row.get("camada") not in valid_layers:
            errors.append(f"calculator_schema linha {i}: camada inválida: {row.get('camada')}")
    return errors


def validate_scoring(scoring: list[dict[str, str]]) -> list[str]:
    errors = []
    total_benefit = 0.0
    for i, row in enumerate(scoring, start=2):
        try:
            peso = float(row.get("peso_inicial", ""))
        except Exception:
            errors.append(f"scoring_model_spec linha {i}: peso inválido")
            continue
        if row.get("dimensao") != "risco":
            total_benefit += peso
    if total_benefit <= 0:
        errors.append("scoring_model_spec: soma de pesos positivos precisa ser maior que zero")
    return errors


def execute_calculator_architecture() -> dict[str, Any]:
    rules = load_yaml(RULES)
    schema = read_csv(SEED_SCHEMA)
    scoring = read_csv(SEED_SCORING)
    formulas = read_csv(SEED_FORMULAS)
    layers = read_csv(SEED_LAYERS)
    inputs = read_csv(SEED_INPUTS)
    dimensions = read_csv(DIMENSIONS)

    errors = []
    errors.extend(validate_schema(schema, rules))
    errors.extend(check_unique(formulas, "id_formula", "formulas_registry"))
    errors.extend(check_unique(inputs, "id_requisito", "calculator_input_requirements"))
    errors.extend(validate_scoring(scoring))

    if errors:
        return {"errors": errors}

    # Enriquecer schema com flags de prontidão.
    enriched_schema = []
    for row in schema:
        out = dict(row)
        out["status_arquitetura"] = "definido"
        out["requer_benchmark"] = "sim" if "benchmark" in row.get("formula_conceitual", "").lower() or row.get("dimensao") in {"gap", "mercado"} else "avaliar"
        out["pode_calcular_agora"] = "não"
        out["motivo_nao_calculo"] = "Rodada 4.11 define arquitetura; dados/benchmarks serão estruturados em rodadas posteriores."
        enriched_schema.append(out)

    # Enriquecer inputs com bloqueio operacional.
    enriched_inputs = []
    for row in inputs:
        out = dict(row)
        out["bloqueia_score_final"] = "sim" if row.get("status") in {"ausente", "pendente_parcial"} else "parcial"
        enriched_inputs.append(out)

    write_csv(OUT_SCHEMA, enriched_schema)
    write_csv(OUT_SCORING, scoring)
    write_csv(OUT_FORMULAS, formulas)
    write_csv(OUT_LAYERS, layers)
    write_csv(OUT_INPUTS, enriched_inputs)

    evidence = [{
        "id_evidencia": "EVD_CALCULATOR_ARCHITECTURE_4_11",
        "id_fonte": "CALCULATOR_ARCHITECTURE",
        "id_indicador": "SYS_02; MON_02",
        "tipo_evidencia": "arquitetura_calculadora",
        "pergunta_ou_lacuna": "A calculadora Fito+ Amazônia AIMM possui arquitetura em duas camadas, dimensões, fórmulas e requisitos de entrada definidos?",
        "url_ou_arquivo": "data/processed/calculator_schema.csv; data/processed/scoring_model_spec.csv; data/processed/formulas_registry.csv",
        "titulo_documento": "Arquitetura da calculadora AIMM em duas camadas — Rodada 4.11",
        "pagina_tabela_secao": "schema, scoring, formulas, layers e input requirements",
        "trecho_original_ou_descricao": f"Indicadores arquiteturais definidos: {len(enriched_schema)}; fórmulas registradas: {len(formulas)}; requisitos de entrada: {len(enriched_inputs)}; blocos de camada: {len(layers)}.",
        "resumo_ptbr": "Evidência de definição da arquitetura lógica da calculadora antes da implementação do motor de cálculo.",
        "valor_extraido": str(len(enriched_schema)),
        "unidade": "indicadores definidos",
        "periodo_referencia": "Rodada 4.11",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "geração automatizada a partir de registros seed e regras de arquitetura",
        "nivel_confianca": "alto_para_arquitetura; baixo_para_score_final",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_validacao_metodologica",
        "limitacoes": "Não calcula score final; depende de espécies, produtos, orçamento e benchmarks.",
        "uso_na_calculadora": "Base lógica da calculadora AIMM adaptada.",
        "status_evidencia": "pendente",
    }]
    write_csv(OUT_EVIDENCE, evidence)

    return {
        "errors": [],
        "total_indicadores": len(enriched_schema),
        "total_formulas": len(formulas),
        "total_requisitos": len(enriched_inputs),
        "total_blocos_camadas": len(layers),
        "total_dimensoes": len(dimensions),
        "outputs": {
            "calculator_schema": str(OUT_SCHEMA),
            "scoring_model_spec": str(OUT_SCORING),
            "formulas_registry": str(OUT_FORMULAS),
            "calculator_layers_map": str(OUT_LAYERS),
            "calculator_input_requirements": str(OUT_INPUTS),
            "evidence": str(OUT_EVIDENCE),
        }
    }
