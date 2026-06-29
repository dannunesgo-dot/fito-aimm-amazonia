
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.pre_diligencia_manual_validator import executar_validacao_input_manual

BASE_STATUS = Path("data/processed/pre_diligencia_status_validacao.csv")
RELATORIO = Path("outputs/logs/teste_pre_diligencia_manual_validation.txt")


def ler_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    if not BASE_STATUS.exists():
        raise FileNotFoundError(
            "Arquivo obrigatório ausente: data/processed/pre_diligencia_status_validacao.csv. "
            "O workflow deve recuperar artefato da Rodada 4.8 antes de executar."
        )

    result = executar_validacao_input_manual()
    report = ler_csv(Path(result["arquivos"]["report"]))
    ready = ler_csv(Path(result["arquivos"]["ready"]))

    if not ready:
        raise ValueError("pre_diligencia_status_validacao_ready_for_drive.csv ficou vazio.")
    if not report:
        raise ValueError("pre_diligencia_manual_validation_report.csv ficou vazio.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE PRE_DILIGENCIA_MANUAL_VALIDATION — Fito+ Amazônia",
        "=" * 92,
        f"Linhas avaliadas: {result['total_linhas']}",
        f"Arquivo manual usado: {'sim' if result['usou_manual'] else 'não'}",
        f"Erros: {result['erros']}",
        f"Alertas: {result['alertas']}",
        "",
        "Arquivos gerados:",
        f"- {result['arquivos']['template']}",
        f"- {result['arquivos']['ready']}",
        f"- {result['arquivos']['report']}",
        f"- {result['arquivos']['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "A planilha de entrada manual foi preparada/validada para uso controlado no Drive e reincorporação ao GitHub.",
        "",
        "Trava: validação de preenchimento não seleciona executora nem confirma veracidade documental.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
