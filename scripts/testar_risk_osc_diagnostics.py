
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.risk_osc_diagnostics import executar_diagnostico_risk_osc

INPUT_RISK = Path("data/processed/risk_osc_screening.csv")
RELATORIO = Path("outputs/logs/teste_risk_osc_diagnostics.txt")


def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    if not INPUT_RISK.exists():
        raise FileNotFoundError(
            "Arquivo obrigatório ausente: data/processed/risk_osc_screening.csv. "
            "O workflow deve recuperar o artefato risk-osc-screening-fito-amazonia antes de executar este script."
        )

    resultado = executar_diagnostico_risk_osc()
    arquivos = resultado["arquivos"]

    diagnosticos = ler_csv(Path(arquivos["diagnosticos"]))
    cenarios = ler_csv(Path(arquivos["cenarios"]))
    topn = ler_csv(Path(arquivos["topn"]))
    checklist = ler_csv(Path(arquivos["checklist"]))
    evidencias = ler_csv(Path(arquivos["evidencias"]))

    if not diagnosticos:
        raise ValueError("risk_osc_diagnostics.csv ficou vazio.")
    if not cenarios:
        raise ValueError("risk_osc_threshold_scenarios.csv ficou vazio.")
    if not topn:
        raise ValueError("organizacoes_pre_diligencia_topN.csv ficou vazio.")
    if len(topn) != len(checklist):
        raise ValueError("checklist_contato_validacao.csv deve ter a mesma quantidade de linhas do topN.")
    if len(evidencias) != 4:
        raise ValueError(f"evidence_risk_osc_diagnostics.csv deveria ter 4 linhas; tem {len(evidencias)}.")

    resumo = resultado["resumo"]

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE RISK_OSC_DIAGNOSTICS — Fito+ Amazônia",
        "=" * 78,
        f"Organizações avaliadas: {resumo['total_organizacoes']}",
        f"Cenário atual formal S00: {resumo['cenario_atual_total']}",
        f"Cenário topN S04: {resumo['cenario_topn_total']}",
        f"Organizações para pré-diligência topN: {resumo['total_pre_diligencia_topn']}",
        f"Linhas de checklist de contato: {resumo['total_checklist']}",
        f"Evidências geradas: {resumo['total_evidencias']}",
        "",
        "Arquivos gerados:",
        f"- {arquivos['diagnosticos']}",
        f"- {arquivos['cenarios']}",
        f"- {arquivos['topn']}",
        f"- {arquivos['checklist']}",
        f"- {arquivos['evidencias']}",
        "",
        "Resultado: SUCESSO.",
        "O diagnóstico do screening de risco foi gerado e produziu pré-lista controlada para contato/validação.",
        "",
        "Trava: pré-diligência não seleciona executora. Exige validação cadastral, documental, contato ativo, entrevista e visita técnica.",
    ]

    texto = "\\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
