
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.calculator_architecture import execute_calculator_architecture

RELATORIO = Path("outputs/logs/teste_calculator_architecture.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_calculator_architecture()
    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Arquitetura da calculadora falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(p)
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    schema = read_csv(Path(outputs["calculator_schema"]))
    required_fields = ["id_indicador", "camada", "dimensao", "formula_conceitual", "fonte_prevista", "limitacao", "status_arquitetura"]
    for field in required_fields:
        if field not in schema[0]:
            raise ValueError(f"Campo obrigatório ausente no calculator_schema.csv: {field}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE CALCULATOR_ARCHITECTURE — Fito+ Amazônia",
        "=" * 88,
        f"Dimensões AIMM registradas: {result['total_dimensoes']}",
        f"Blocos de camada registrados: {result['total_blocos_camadas']}",
        f"Indicadores arquiteturais definidos: {result['total_indicadores']}",
        f"Fórmulas registradas: {result['total_formulas']}",
        f"Requisitos de entrada registrados: {result['total_requisitos']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['calculator_schema']}",
        f"- {outputs['scoring_model_spec']}",
        f"- {outputs['formulas_registry']}",
        f"- {outputs['calculator_layers_map']}",
        f"- {outputs['calculator_input_requirements']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "A arquitetura da calculadora AIMM em duas camadas foi gerada e validada estruturalmente.",
        "",
        "Trava: esta rodada define arquitetura. Não calcula score final, não cria benchmark definitivo e não seleciona OSCs.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
