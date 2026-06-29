
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.species_selection import execute_species_selection

RELATORIO = Path("outputs/logs/teste_species_selection.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_species_selection()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Matriz de espécies falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(p)
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    ranking = read_csv(Path(outputs["species_priority_ranking"]))
    required = ["rank_preliminar", "id_especie", "nome_cientifico", "score_preliminar", "status_decisao", "limitacao"]
    for field in required:
        if field not in ranking[0]:
            raise ValueError(f"Campo obrigatório ausente no ranking: {field}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE SPECIES_SELECTION — Fito+ Amazônia",
        "=" * 86,
        f"Espécies candidatas registradas: {result['total_species']}",
        f"Critérios de seleção registrados: {result['total_criteria']}",
        f"Rotas espécie-produto registradas: {result['total_routes']}",
        f"Maior score preliminar: {result['top_species']} ({result['top_score']})",
        "",
        "Arquivos gerados:",
        f"- {outputs['species_candidate_registry']}",
        f"- {outputs['species_selection_criteria']}",
        f"- {outputs['species_selection_matrix']}",
        f"- {outputs['species_priority_ranking']}",
        f"- {outputs['species_product_route_registry']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "O registro e a matriz de seleção de espécies candidatas foram gerados e validados estruturalmente.",
        "",
        "Trava: a pontuação é preliminar, de baixa confiança e não seleciona espécie final. Exige validação por evidências, mercado, campo, regulação, orçamento e sustentabilidade.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
