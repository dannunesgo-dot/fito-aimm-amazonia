
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/product_pathway_rules.yaml")
PRODUCT_TYPES = Path("data/reference/product_type_registry_seed.csv")
PATHWAYS = Path("data/reference/product_pathway_registry_seed.csv")
REGULATORY = Path("data/reference/regulatory_route_registry_seed.csv")
QUALITY = Path("data/reference/quality_requirement_registry_seed.csv")
STAGES = Path("data/reference/value_chain_stage_registry_seed.csv")

OUT_PRODUCT_TYPES = Path("data/processed/product_type_registry.csv")
OUT_PATHWAYS = Path("data/processed/product_pathway_registry.csv")
OUT_REGULATORY = Path("data/processed/regulatory_route_registry.csv")
OUT_QUALITY = Path("data/processed/quality_requirement_registry.csv")
OUT_STAGES = Path("data/processed/value_chain_stage_registry.csv")
OUT_PRIORITY = Path("data/processed/product_pathway_priority_matrix.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_product_pathway.csv")


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


def validate_inputs(product_types, pathways, regulatory, quality, stages, rules) -> list[str]:
    errors = []
    errors.extend(check_unique(product_types, "id_produto_tipo", "product_type_registry"))
    errors.extend(check_unique(pathways, "id_rota_produto", "product_pathway_registry"))
    errors.extend(check_unique(regulatory, "id_rota_regulatoria", "regulatory_route_registry"))
    errors.extend(check_unique(quality, "id_requisito_qualidade", "quality_requirement_registry"))
    errors.extend(check_unique(stages, "id_elo", "value_chain_stage_registry"))

    product_codes = {r["codigo_produto"] for r in product_types}
    regulatory_codes = {r["codigo_produto"] for r in regulatory}
    criteria = (rules.get("criterios_prioridade_produto") or {})
    weight_sum = sum(to_float(v.get("peso")) for v in criteria.values())
    if abs(weight_sum - 1.0) > 0.001:
        errors.append(f"Pesos dos critérios somam {weight_sum}, esperado 1.0")

    for i, row in enumerate(pathways, start=2):
        code = row.get("codigo_produto", "")
        if code not in product_codes:
            errors.append(f"product_pathway linha {i}: codigo_produto sem tipo cadastrado: {code}")
        if code not in regulatory_codes:
            errors.append(f"product_pathway linha {i}: codigo_produto sem rota regulatória preliminar: {code}")
        for criterion in criteria.keys():
            if criterion not in row:
                errors.append(f"product_pathway linha {i}: critério ausente: {criterion}")
            else:
                val = to_float(row.get(criterion), None)
                if val is None or val < 0 or val > 100:
                    errors.append(f"product_pathway linha {i}: valor fora de 0-100 em {criterion}: {row.get(criterion)}")
    return errors


def calculate_priority(pathways: list[dict[str, str]], product_types: list[dict[str, str]], regulatory: list[dict[str, str]], rules: dict[str, Any]):
    criteria = rules.get("criterios_prioridade_produto") or {}
    type_by_code = {r["codigo_produto"]: r for r in product_types}
    reg_by_code = {r["codigo_produto"]: r for r in regulatory}

    pathways_out = []
    priority_rows = []

    for row in pathways:
        total = 0.0
        components = []
        out = dict(row)

        for criterion, meta in criteria.items():
            raw = to_float(row.get(criterion))
            weight = to_float(meta.get("peso"))
            direction = meta.get("direcao", "maior_melhor")
            adjusted = 100 - raw if direction == "menor_melhor" else raw
            contribution = adjusted * weight
            total += contribution
            out[f"{criterion}_ajustado"] = f"{adjusted:.2f}"
            out[f"{criterion}_contribuicao"] = f"{contribution:.2f}"
            components.append(f"{criterion}:{adjusted:.2f}*{weight:.2f}={contribution:.2f}")

        score = round(total, 2)
        product_type = type_by_code.get(row.get("codigo_produto", ""), {})
        regulatory_route = reg_by_code.get(row.get("codigo_produto", ""), {})

        out["score_prioridade_preliminar"] = f"{score:.2f}"
        out["faixa_prioridade_preliminar"] = score_band(score)
        out["status_score"] = "preliminar_baixa_confianca"
        out["componentes_score"] = "|".join(components)
        out["rota_regulatoria_preliminar"] = regulatory_route.get("rota_regulatoria_preliminar", "")
        out["complexidade_regulatoria_tipo"] = product_type.get("complexidade_regulatoria", "")
        out["status_decisao"] = "rota_para_estudo_nao_aprovada"
        pathways_out.append(out)

        priority_rows.append({
            "id_rota_produto": row.get("id_rota_produto", ""),
            "id_especie": row.get("id_especie", ""),
            "nome_cientifico": row.get("nome_cientifico", ""),
            "codigo_produto": row.get("codigo_produto", ""),
            "mercados_alvo": row.get("mercados_alvo", ""),
            "score_prioridade_preliminar": f"{score:.2f}",
            "faixa_prioridade_preliminar": score_band(score),
            "rota_regulatoria_preliminar": regulatory_route.get("rota_regulatoria_preliminar", ""),
            "status_evidencia": row.get("status_evidencia", ""),
            "status_decisao": "não_aprovada_apenas_priorizada_para_estudo",
            "proxima_acao": "validar_regulacao_mercado_qualidade_orcamento_e_sustentabilidade",
            "limitacao": "Score preliminar; não usar para decisão final de portfólio.",
        })

    priority_rows = sorted(priority_rows, key=lambda r: to_float(r["score_prioridade_preliminar"]), reverse=True)
    for idx, row in enumerate(priority_rows, start=1):
        row["rank_rota_preliminar"] = str(idx)

    return pathways_out, priority_rows


def generate_evidence(pathways, product_types, regulatory, quality, stages, priority):
    top = priority[0] if priority else {}
    return [{
        "id_evidencia": "EVD_PRODUCT_PATHWAY_4_13",
        "id_fonte": "PRODUCT_PATHWAY_ARCHITECTURE",
        "id_indicador": "MERCADO; INTENSIDADE; RISCO; MONITORAMENTO",
        "tipo_evidencia": "registro_rotas_produtivas_regulatorias",
        "pergunta_ou_lacuna": "Quais produtos e rotas produtivas/regulatórias devem ser priorizados para estudos técnicos do Fito+ Amazônia?",
        "url_ou_arquivo": "data/processed/product_pathway_registry.csv; data/processed/product_pathway_priority_matrix.csv",
        "titulo_documento": "Produtos e rotas produtivas/regulatórias — Rodada 4.13",
        "pagina_tabela_secao": "product_pathway_registry; regulatory_route_registry; product_pathway_priority_matrix",
        "trecho_original_ou_descricao": f"Tipos de produto: {len(product_types)}; rotas espécie-produto: {len(pathways)}; rotas regulatórias preliminares: {len(regulatory)}; requisitos de qualidade: {len(quality)}; elos de cadeia: {len(stages)}; rota com maior score preliminar: {top.get('nome_cientifico','')} / {top.get('codigo_produto','')} ({top.get('score_prioridade_preliminar','')}).",
        "resumo_ptbr": "Evidência de estruturação preliminar das rotas produtivas e regulatórias; não representa aprovação de produto.",
        "valor_extraido": str(len(pathways)),
        "unidade": "rotas espécie-produto",
        "periodo_referencia": "Rodada 4.13",
        "territorio": "Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
        "metodo_extracao": "matriz multicritério preliminar com pesos configurados e rotas regulatórias conceituais",
        "nivel_confianca": "baixo_para_decisao; médio_para_estrutura_metodologica",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_validacao_normativa_mercado_qualidade_orcamento",
        "limitacoes": "A rota regulatória é preliminar; requer validação normativa, técnica, mercado, qualidade, orçamento e sustentabilidade.",
        "uso_na_calculadora": "Entrada para camadas de produto, mercado, risco, qualidade, orçamento e intensidade.",
        "status_evidencia": "pendente",
    }]


def execute_product_pathway() -> dict[str, Any]:
    rules = load_yaml(RULES)
    product_types = read_csv(PRODUCT_TYPES)
    pathways = read_csv(PATHWAYS)
    regulatory = read_csv(REGULATORY)
    quality = read_csv(QUALITY)
    stages = read_csv(STAGES)

    errors = validate_inputs(product_types, pathways, regulatory, quality, stages, rules)
    if errors:
        return {"errors": errors}

    pathways_out, priority = calculate_priority(pathways, product_types, regulatory, rules)
    evidence = generate_evidence(pathways_out, product_types, regulatory, quality, stages, priority)

    write_csv(OUT_PRODUCT_TYPES, product_types)
    write_csv(OUT_PATHWAYS, pathways_out)
    write_csv(OUT_REGULATORY, regulatory)
    write_csv(OUT_QUALITY, quality)
    write_csv(OUT_STAGES, stages)
    write_csv(OUT_PRIORITY, priority)
    write_csv(OUT_EVIDENCE, evidence)

    return {
        "errors": [],
        "total_product_types": len(product_types),
        "total_pathways": len(pathways_out),
        "total_regulatory": len(regulatory),
        "total_quality": len(quality),
        "total_stages": len(stages),
        "top_pathway": f"{priority[0]['nome_cientifico']} / {priority[0]['codigo_produto']}" if priority else "",
        "top_score": priority[0]["score_prioridade_preliminar"] if priority else "",
        "outputs": {
            "product_type_registry": str(OUT_PRODUCT_TYPES),
            "product_pathway_registry": str(OUT_PATHWAYS),
            "regulatory_route_registry": str(OUT_REGULATORY),
            "quality_requirement_registry": str(OUT_QUALITY),
            "value_chain_stage_registry": str(OUT_STAGES),
            "product_pathway_priority_matrix": str(OUT_PRIORITY),
            "evidence": str(OUT_EVIDENCE),
        },
    }
