
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.system_freeze_index import execute_system_freeze_index

RELATORIO = Path("outputs/logs/teste_system_freeze_index.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_system_freeze_index()
    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Congelamento técnico falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        if not Path(path).exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(Path(path))
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE SYSTEM_FREEZE_INDEX — Fito+ Amazônia",
        "=" * 86,
        f"Artefatos indexados: {result['total_artifacts']}",
        f"Rodadas registradas: {result['total_rounds']}",
        f"Rodadas validadas ou validadas com lacuna: {result['total_validated_rounds']}",
        f"Lacunas operacionais registradas: {result['total_gaps']}",
        f"Itens no manifesto Drive: {result['total_drive_items']}",
        f"Itens no mapa GitHub: {result['total_github_map']}",
        f"Itens ausentes a revisar no GitHub: {result['total_missing_review']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['master_artifact_index']}",
        f"- {outputs['round_status']}",
        f"- {outputs['drive_archive_manifest']}",
        f"- {outputs['github_repository_map']}",
        f"- {outputs['operational_gaps_register']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "O congelamento técnico e o índice mestre foram gerados para preparar a arquitetura da calculadora AIMM.",
        "",
        "Trava: este congelamento não altera resultados validados nem seleciona OSCs. Arquivamento no Drive permanece etapa operacional externa ao teste.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
