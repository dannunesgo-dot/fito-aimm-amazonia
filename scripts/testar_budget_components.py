
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.budget_components import execute_budget_components

RELATORIO = Path("outputs/logs/teste_budget_components.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    result = execute_budget_components()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Orçamento por componente falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(p)
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    components = read_csv(Path(outputs["budget_components"]))
    total = sum(float(row["valor_brl"]) for row in components)
    if round(total, 2) != round(result["total_budget"], 2):
        raise ValueError(f"Total de budget_components não fecha: {total} vs {result['total_budget']}")

    validation = read_csv(Path(outputs["budget_validation_report"]))
    if any(row["status"] == "erro" for row in validation):
        raise ValueError("budget_validation_report contém erro.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    class_lines = [f"- {cls}: {brl(value)}" for cls, value in sorted(result["class_totals"].items())]
    lines = [
        "TESTE BUDGET_COMPONENTS — Fito+ Amazônia",
        "=" * 86,
        f"Investimento total estruturado: {brl(result['total_budget'])}",
        f"Componentes orçamentários registrados: {result['total_components']}",
        f"Pressupostos de custo registrados: {result['total_assumptions']}",
        f"Linhas de cronograma/fase: {result['total_phase_rows']}",
        f"Vínculos AIMM registrados: {result['total_aimm_links']}",
        "",
        "Totais por classe de gasto:",
        *class_lines,
        "",
        "Arquivos gerados:",
        f"- {outputs['budget_components']}",
        f"- {outputs['cost_assumption_registry']}",
        f"- {outputs['budget_phase_schedule']}",
        f"- {outputs['budget_aimm_linkage']}",
        f"- {outputs['budget_summary']}",
        f"- {outputs['budget_validation_report']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "O orçamento preliminar por componente e os pressupostos de custo foram gerados e validados estruturalmente.",
        "",
        "Trava: orçamento preliminar não autoriza contratação, compra, convênio, termo de fomento, TED ou execução. Exige pesquisa de preços e memória de cálculo em rodada futura.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
