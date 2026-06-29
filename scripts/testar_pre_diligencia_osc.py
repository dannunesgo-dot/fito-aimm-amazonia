
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.pre_diligencia_osc import executar_pre_diligencia_osc

INPUT_TOPN = Path("data/processed/organizacoes_pre_diligencia_topN.csv")
RELATORIO = Path("outputs/logs/teste_pre_diligencia_osc.txt")


def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    if not INPUT_TOPN.exists():
        raise FileNotFoundError(
            "Arquivo obrigatório ausente: data/processed/organizacoes_pre_diligencia_topN.csv. "
            "O workflow deve recuperar o artefato risk-osc-diagnostics-fito-amazonia antes de executar este script."
        )

    resultado = executar_pre_diligencia_osc()
    resumo = resultado["resumo"]
    arquivos = resultado["arquivos"]

    fila = ler_csv(Path(arquivos["fila"]))
    status = ler_csv(Path(arquivos["status"]))
    docs = ler_csv(Path(arquivos["documentos"]))
    evid = ler_csv(Path(arquivos["evidencias"]))

    if not fila:
        raise ValueError("pre_diligencia_fila_contato.csv ficou vazio.")
    if len(fila) != len(status) or len(fila) != len(docs):
        raise ValueError("Fila, status e solicitação documental devem ter a mesma quantidade de linhas.")
    if len(evid) != 4:
        raise ValueError(f"evidence_pre_diligencia_osc.csv deveria ter 4 linhas; tem {len(evid)}.")

    campos = [
        "id_pre_diligencia",
        "prioridade_operacional",
        "canal_preferencial",
        "nome_organizacao",
        "municipio",
        "uf",
        "status_contato",
        "trava",
    ]
    for campo in campos:
        if campo not in fila[0]:
            raise ValueError(f"Campo ausente na fila de contato: {campo}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE PRE_DILIGENCIA_OSC — Fito+ Amazônia",
        "=" * 78,
        f"Total na fila de contato: {resumo['total_fila']}",
        f"P1: {resumo['p1']}",
        f"P2: {resumo['p2']}",
        f"P3: {resumo['p3']}",
        f"P4: {resumo['p4']}",
        f"Linhas de status: {resumo['total_status']}",
        f"Linhas de solicitação documental: {resumo['total_docs']}",
        f"Evidências geradas: {resumo['total_evidencias']}",
        "",
        "Arquivos gerados:",
        f"- {arquivos['fila']}",
        f"- {arquivos['status']}",
        f"- {arquivos['documentos']}",
        f"- {arquivos['evidencias']}",
        "",
        "Resultado: SUCESSO.",
        "A fila operacional de pré-diligência foi gerada para contato, validação cadastral e solicitação documental.",
        "",
        "Trava: pré-diligência não seleciona executora. Exige validação cadastral, documental, contato ativo, entrevista e visita técnica.",
    ]

    texto = "\\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
