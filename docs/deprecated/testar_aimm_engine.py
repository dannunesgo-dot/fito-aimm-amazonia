
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.aimm_engine import execute_aimm_engine

RELATORIO = Path("outputs/logs/teste_aimm_engine.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_aimm_engine()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Motor AIMM falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(p)
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    overall = read_csv(Path(outputs["aimm_overall_score"]))[0]
    if overall["pode_ser_usado_como_score_final"] != "não":
        raise ValueError("Trava violada: resultado não pode ser usado como score final.")

    validation = read_csv(Path(outputs["aimm_engine_validation_report"]))
    if any(row["status"] == "erro" for row in validation):
        raise ValueError("Relatório de validação contém erro.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE AIMM_ENGINE — Fito+ Amazônia",
        "=" * 86,
        f"Indicadores processados: {result['total_indicators']}",
        f"Dimensões processadas: {result['total_dimensions']}",
        f"Bloqueios/lacunas ativos: {result['total_blockers']}",
        f"Penalidade de risco preliminar: {result['risk_penalty']}",
        f"Fator de monitoramento preliminar: {result['monitoring_factor']}",
        f"Score estrutural preliminar: {result['score']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['aimm_indicator_scores']}",
        f"- {outputs['aimm_dimension_scores']}",
        f"- {outputs['aimm_overall_score']}",
        f"- {outputs['aimm_blockers_report']}",
        f"- {outputs['aimm_engine_validation_report']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "O motor inicial da calculadora AIMM foi executado e validado estruturalmente.",
        "",
        "Trava: o score é estrutural, preliminar e não pode ser usado como score AIMM final validado.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
