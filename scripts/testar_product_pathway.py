
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.product_pathway import execute_product_pathway

RELATORIO = Path("outputs/logs/teste_product_pathway.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_product_pathway()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Rotas de produtos falharam com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(p)
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    priority = read_csv(Path(outputs["product_pathway_priority_matrix"]))
    required = ["rank_rota_preliminar", "id_rota_produto", "nome_cientifico", "codigo_produto", "score_prioridade_preliminar", "status_decisao", "limitacao"]
    for field in required:
        if field not in priority[0]:
            raise ValueError(f"Campo obrigatório ausente na matriz de prioridade: {field}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE PRODUCT_PATHWAY — Fito+ Amazônia",
        "=" * 86,
        f"Tipos de produto registrados: {result['total_product_types']}",
        f"Rotas espécie-produto registradas: {result['total_pathways']}",
        f"Rotas regulatórias preliminares registradas: {result['total_regulatory']}",
        f"Requisitos de qualidade registrados: {result['total_quality']}",
        f"Elos de cadeia de valor registrados: {result['total_stages']}",
        f"Maior score preliminar: {result['top_pathway']} ({result['top_score']})",
        "",
        "Arquivos gerados:",
        f"- {outputs['product_type_registry']}",
        f"- {outputs['product_pathway_registry']}",
        f"- {outputs['regulatory_route_registry']}",
        f"- {outputs['quality_requirement_registry']}",
        f"- {outputs['value_chain_stage_registry']}",
        f"- {outputs['product_pathway_priority_matrix']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "O registro de produtos e rotas produtivas/regulatórias foi gerado e validado estruturalmente.",
        "",
        "Trava: as rotas são preliminares, de baixa confiança e não aprovam produto, registro, compra pública ou portfólio final.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
