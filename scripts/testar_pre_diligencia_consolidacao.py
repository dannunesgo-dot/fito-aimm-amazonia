
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.pre_diligencia_consolidacao import executar_consolidacao_pre_diligencia

INPUT_STATUS = Path("data/processed/pre_diligencia_status_validacao.csv")
INPUT_FILA = Path("data/processed/pre_diligencia_fila_contato.csv")
RELATORIO = Path("outputs/logs/teste_pre_diligencia_consolidacao.txt")


def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    if not INPUT_STATUS.exists() or not INPUT_FILA.exists():
        raise FileNotFoundError(
            "Arquivos obrigatórios ausentes: pre_diligencia_status_validacao.csv e/ou pre_diligencia_fila_contato.csv. "
            "O workflow deve recuperar o artefato pre-diligencia-osc-fito-amazonia antes de executar este script."
        )

    resultado = executar_consolidacao_pre_diligencia()
    resumo = resultado["resumo"]
    arquivos = resultado["arquivos"]

    consolidado = ler_csv(Path(arquivos["consolidado"]))
    encaminhamentos = ler_csv(Path(arquivos["encaminhamentos"]))
    pendencias = ler_csv(Path(arquivos["pendencias"]))
    evidencias = ler_csv(Path(arquivos["evidencias"]))

    if not consolidado:
        raise ValueError("pre_diligencia_consolidado.csv ficou vazio.")
    if len(consolidado) != len(encaminhamentos) or len(consolidado) != len(pendencias):
        raise ValueError("Consolidado, encaminhamentos e pendências devem ter a mesma quantidade de linhas.")
    if len(evidencias) != 4:
        raise ValueError(f"evidence_pre_diligencia_consolidacao.csv deveria ter 4 linhas; tem {len(evidencias)}.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE PRE_DILIGENCIA_CONSOLIDACAO — Fito+ Amazônia",
        "=" * 86,
        f"Total consolidado: {resumo['total_consolidado']}",
        f"Continuar contato: {resumo['continuar_contato']}",
        f"Solicitar documentos: {resumo['solicitar_documentos']}",
        f"Recomendar visita: {resumo['recomendar_visita']}",
        f"Bloquear: {resumo['bloquear']}",
        f"Descartar: {resumo['descartar']}",
        f"Evidências geradas: {resumo['total_evidencias']}",
        "",
        "Arquivos gerados:",
        f"- {arquivos['consolidado']}",
        f"- {arquivos['encaminhamentos']}",
        f"- {arquivos['pendencias']}",
        f"- {arquivos['evidencias']}",
        "",
        "Resultado: SUCESSO.",
        "A consolidação da pré-diligência foi gerada para acompanhamento de contato, documentos e encaminhamentos.",
        "",
        "Trava: consolidação não seleciona executora. Se os campos manuais estiverem vazios, os encaminhamentos permanecem preliminares.",
    ]

    texto = "\\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
