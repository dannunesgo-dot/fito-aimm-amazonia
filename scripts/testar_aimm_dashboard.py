
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.aimm_dashboard import execute_aimm_dashboard

RELATORIO = Path("outputs/logs/teste_aimm_dashboard.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_aimm_dashboard()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Dashboard AIMM falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        if p.suffix == ".csv":
            rows = read_csv(p)
            if not rows:
                raise ValueError(f"CSV vazio: {key} -> {path}")
        else:
            text = p.read_text(encoding="utf-8")
            if not text.strip():
                raise ValueError(f"Arquivo textual vazio: {key} -> {path}")

    summary = read_csv(Path(outputs["executive_summary_csv"]))[0]
    if summary["pode_ser_usado_como_score_final"] != "não":
        raise ValueError("Trava violada: painel não pode liberar score final.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE AIMM_DASHBOARD — Fito+ Amazônia",
        "=" * 86,
        f"Score estrutural preliminar exibido: {result['score']}",
        f"Status de prontidão: {result['status']}",
        f"Cards executivos gerados: {result['cards']}",
        f"Dimensões exibidas: {result['dimensions']}",
        f"Bloqueios/lacunas exibidos: {result['blockers']}",
        f"Próximas ações registradas: {result['next_actions']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['executive_summary_csv']}",
        f"- {outputs['dashboard_cards_csv']}",
        f"- {outputs['dimension_view_csv']}",
        f"- {outputs['next_actions_csv']}",
        f"- {outputs['output_manifest']}",
        f"- {outputs['evidence_csv']}",
        f"- {outputs['executive_summary_md']}",
        f"- {outputs['dashboard_payload_json']}",
        "",
        "Resultado: SUCESSO.",
        "O painel/resumo executivo e os outputs da calculadora AIMM foram gerados e validados estruturalmente.",
        "",
        "Trava: o painel apresenta resultado estrutural preliminar. Não libera score AIMM final nem aprova decisões executivas.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
