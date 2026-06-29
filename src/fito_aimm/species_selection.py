
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/species_selection_rules.yaml")
SPECIES_SEED = Path("data/reference/species_candidate_registry_seed.csv")
CRITERIA_SEED = Path("data/reference/species_selection_criteria_seed.csv")
MATRIX_SEED = Path("data/reference/species_selection_matrix_seed.csv")
ROUTES_SEED = Path("data/reference/species_product_route_seed.csv")

OUT_SPECIES = Path("data/processed/species_candidate_registry.csv")
OUT_CRITERIA = Path("data/processed/species_selection_criteria.csv")
OUT_MATRIX = Path("data/processed/species_selection_matrix.csv")
OUT_RANKING = Path("data/processed/species_priority_ranking.csv")
OUT_ROUTES = Path("data/processed/species_product_route_registry.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_species_selection.csv")


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


def validate_inputs(species: list[dict[str, str]], criteria: list[dict[str, str]], matrix: list[dict[str, str]], routes: list[dict[str, str]], rules: dict[str, Any]) -> list[str]:
    errors = []
    errors.extend(check_unique(species, "id_especie", "species_candidate_registry"))
    errors.extend(check_unique(criteria, "id_criterio", "species_selection_criteria"))
    errors.extend(check_unique(routes, "id_rota", "species_product_route"))

    species_ids = {r["id_especie"] for r in species}
    criteria_names = {r["criterio"] for r in criteria}
    matrix_ids = set()

    for i, row in enumerate(matrix, start=2):
        sid = row.get("id_especie", "")
        if sid not in species_ids:
            errors.append(f"species_selection_matrix linha {i}: id_especie desconhecido: {sid}")
        if sid in matrix_ids:
            errors.append(f"species_selection_matrix linha {i}: id_especie duplicado: {sid}")
        matrix_ids.add(sid)
        for criterio in criteria_names:
            if criterio not in row:
                errors.append(f"species_selection_matrix linha {i}: critério ausente: {criterio}")
                continue
            val = to_float(row.get(criterio), None)
            if val is None or val < 0 or val > 100:
                errors.append(f"species_selection_matrix linha {i}: valor fora de 0-100 em {criterio}: {row.get(criterio)}")

    for i, row in enumerate(routes, start=2):
        if row.get("id_especie") not in species_ids:
            errors.append(f"species_product_route linha {i}: id_especie desconhecido: {row.get('id_especie')}")

    # pesos devem somar aproximadamente 1.0
    weight_sum = sum(to_float(r.get("peso")) for r in criteria)
    if abs(weight_sum - 1.0) > 0.001:
        errors.append(f"species_selection_criteria: pesos somam {weight_sum}, esperado 1.0")

    return errors


def calculate_scores(species: list[dict[str, str]], criteria: list[dict[str, str]], matrix: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    species_by_id = {r["id_especie"]: r for r in species}
    criteria_meta = {r["criterio"]: r for r in criteria}

    matrix_out = []
    ranking = []

    for row in matrix:
        sid = row["id_especie"]
        total = 0.0
        components = []

        out_row = dict(row)
        for criterio, meta in criteria_meta.items():
            raw = to_float(row.get(criterio))
            weight = to_float(meta.get("peso"))
            direction = meta.get("direcao", "maior_melhor")
            adjusted = 100.0 - raw if direction == "menor_melhor" else raw
            contribution = adjusted * weight
            total += contribution
            components.append(f"{criterio}:{adjusted:.2f}*{weight:.2f}={contribution:.2f}")
            out_row[f"{criterio}_ajustado"] = f"{adjusted:.2f}"
            out_row[f"{criterio}_contribuicao"] = f"{contribution:.2f}"

        total = round(total, 2)
        out_row["score_preliminar"] = f"{total:.2f}"
        out_row["faixa_preliminar"] = score_band(total)
        out_row["status_score"] = "preliminar_baixa_confianca"
        out_row["componentes_score"] = "|".join(components)
        matrix_out.append(out_row)

        sp = species_by_id[sid]
        ranking.append({
            "id_especie": sid,
            "nome_cientifico": sp.get("nome_cientifico", ""),
            "nome_popular": sp.get("nome_popular", ""),
            "modalidade_produtiva": sp.get("modalidade_produtiva", ""),
            "produtos_potenciais": sp.get("produtos_potenciais", ""),
            "score_preliminar": f"{total:.2f}",
            "faixa_preliminar": score_band(total),
            "nivel_confianca": sp.get("nivel_confianca", "baixa"),
            "status_evidencia": sp.get("status_evidencia", "pendente"),
            "status_decisao": "não_selecionada_apenas_priorizada_para_estudo",
            "proxima_acao": "buscar_evidencias_tecnicas_mercado_regulatorias_e_territoriais",
            "limitacao": "Score preliminar; não usar para seleção final sem validação.",
        })

    ranking = sorted(ranking, key=lambda r: to_float(r["score_preliminar"]), reverse=True)
    for idx, row in enumerate(ranking, start=1):
        row["rank_preliminar"] = str(idx)

    return matrix_out, ranking


def generate_evidence(species: list[dict[str, str]], criteria: list[dict[str, str]], ranking: list[dict[str, Any]], routes: list[dict[str, str]]) -> list[dict[str, str]]:
    top = ranking[0] if ranking else {}
    return [{
        "id_evidencia": "EVD_SPECIES_SELECTION_4_12",
        "id_fonte": "SPECIES_SELECTION_ARCHITECTURE",
        "id_indicador": "GAP; INTENSIDADE; MERCADO; RISCO; MONITORAMENTO",
        "tipo_evidencia": "registro_matriz_especies",
        "pergunta_ou_lacuna": "Quais espécies candidatas devem ser priorizadas para estudos técnicos, mercadológicos, regulatórios e territoriais?",
        "url_ou_arquivo": "data/processed/species_candidate_registry.csv; data/processed/species_priority_ranking.csv",
        "titulo_documento": "Registro e matriz de seleção de espécies candidatas — Rodada 4.12",
        "pagina_tabela_secao": "species_candidate_registry; species_selection_matrix; species_priority_ranking",
        "trecho_original_ou_descricao": f"Espécies registradas: {len(species)}; critérios: {len(criteria)}; rotas produto-espécie: {len(routes)}; maior score preliminar: {top.get('nome_cientifico','')} ({top.get('score_preliminar','')}).",
        "resumo_ptbr": "Evidência de estruturação preliminar da matriz de seleção de espécies; não representa seleção final.",
        "valor_extraido": str(len(species)),
        "unidade": "espécies candidatas",
        "periodo_referencia": "Rodada 4.12",
        "territorio": "Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
        "metodo_extracao": "matriz multicritério preliminar com pesos configurados e scores de baixa confiança",
        "nivel_confianca": "baixo_para_decisao; médio_para_estrutura_metodologica",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_buscas_e_validacao_tecnica",
        "limitacoes": "Scores são preliminares e precisam de revisão por evidências, mercado, campo, regulação, orçamento e sustentabilidade.",
        "uso_na_calculadora": "Entrada inicial para a camada operacional de espécies e para critérios AIMM de mercado, intensidade, risco e gap.",
        "status_evidencia": "pendente",
    }]


def execute_species_selection() -> dict[str, Any]:
    rules = load_yaml(RULES)
    species = read_csv(SPECIES_SEED)
    criteria = read_csv(CRITERIA_SEED)
    matrix = read_csv(MATRIX_SEED)
    routes = read_csv(ROUTES_SEED)

    errors = validate_inputs(species, criteria, matrix, routes, rules)
    if errors:
        return {"errors": errors}

    matrix_out, ranking = calculate_scores(species, criteria, matrix)
    evidence = generate_evidence(species, criteria, ranking, routes)

    # Add status fields to species registry
    species_out = []
    for sp in species:
        out = dict(sp)
        out["status_decisao"] = "candidata_para_estudo_nao_selecionada"
        out["lacunas_criticas"] = "mercado|regulacao|qualidade|sustentabilidade|territorio|orcamento"
        species_out.append(out)

    write_csv(OUT_SPECIES, species_out)
    write_csv(OUT_CRITERIA, criteria)
    write_csv(OUT_MATRIX, matrix_out)
    write_csv(OUT_RANKING, ranking)
    write_csv(OUT_ROUTES, routes)
    write_csv(OUT_EVIDENCE, evidence)

    return {
        "errors": [],
        "total_species": len(species_out),
        "total_criteria": len(criteria),
        "total_routes": len(routes),
        "top_species": ranking[0]["nome_cientifico"] if ranking else "",
        "top_score": ranking[0]["score_preliminar"] if ranking else "",
        "outputs": {
            "species_candidate_registry": str(OUT_SPECIES),
            "species_selection_criteria": str(OUT_CRITERIA),
            "species_selection_matrix": str(OUT_MATRIX),
            "species_priority_ranking": str(OUT_RANKING),
            "species_product_route_registry": str(OUT_ROUTES),
            "evidence": str(OUT_EVIDENCE),
        },
    }
