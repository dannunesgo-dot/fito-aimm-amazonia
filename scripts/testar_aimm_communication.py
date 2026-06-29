
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.aimm_communication import execute_aimm_communication

RELATORIO = Path("outputs/logs/teste_aimm_communication.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_aimm_communication()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Comunicação AIMM falhou com {len(result['errors'])} erro(s).")

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

    html_text = Path(outputs["html_dashboard"]).read_text(encoding="utf-8")
    svg_text = Path(outputs["svg_dashboard"]).read_text(encoding="utf-8")
    brief_text = Path(outputs["communication_brief"]).read_text(encoding="utf-8")

    required_terms = ["preliminar", "não", "score AIMM final"]
    for term in required_terms:
        if term not in html_text and term not in brief_text:
            raise ValueError(f"Trava textual não encontrada nos outputs: {term}")

    if "<svg" not in svg_text:
        raise ValueError("SVG inválido ou sem tag <svg>.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE AIMM_COMMUNICATION — Fito+ Amazônia",
        "=" * 86,
        f"Score estrutural preliminar comunicado: {result['score']}",
        f"Mensagens executivas registradas: {result['messages']}",
        f"Cards usados no pacote: {result['cards']}",
        f"Dimensões usadas no pacote: {result['dimensions']}",
        f"Próximas ações usadas no pacote: {result['next_actions']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['communication_messages']}",
        f"- {outputs['visual_outputs_index']}",
        f"- {outputs['html_dashboard']}",
        f"- {outputs['svg_dashboard']}",
        f"- {outputs['mermaid_flow']}",
        f"- {outputs['communication_brief']}",
        f"- {outputs['communication_payload']}",
        f"- {outputs['evidence']}",
        f"- {outputs['package_manifest']}",
        "",
        "Resultado: SUCESSO.",
        "O pacote editável de comunicação e visualização do dashboard AIMM foi gerado e validado estruturalmente.",
        "",
        "Trava: comunicação preliminar. Não libera score AIMM final, orçamento, OSCs, espécies, produtos ou rotas regulatórias.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
