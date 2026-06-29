
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.risk_osc import executar_risk_osc_screening

INPUT_ORGS = Path("data/processed/organizacoes_candidatas_mapaosc.csv")
RELATORIO = Path("outputs/logs/teste_risk_osc_screening.txt")

def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))

def main():
    if not INPUT_ORGS.exists():
        # Gera base Mapa OSCs se o artefato anterior ainda não foi salvo no repositório.
        from fito_aimm.coletor_mapaosc import coletar_mapaosc_municipios
        coletar_mapaosc_municipios()

    resultado = executar_risk_osc_screening()

    risk = ler_csv(Path(resultado["output_risk"]))
    shortlist = ler_csv(Path(resultado["output_shortlist"]))
    evidence = ler_csv(Path(resultado["output_evidence"]))

    if not risk:
        raise ValueError("risk_osc_screening.csv ficou vazio.")

    campos = [
        "nome_organizacao",
        "municipio",
        "uf",
        "risco_osc_score",
        "classe_risco_osc",
        "recomendacao_diligencia",
        "trava_decisoria",
    ]
    for campo in campos:
        if campo not in risk[0]:
            raise ValueError(f"Campo ausente em risk_osc_screening.csv: {campo}")

    for linha in risk[:20]:
        score = int(linha["risco_osc_score"])
        if score < 0 or score > 100:
            raise ValueError(f"Score fora do intervalo 0-100: {score}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE RISK_OSC_SCREENING — Fito+ Amazônia",
        "=" * 72,
        f"Organizações avaliadas: {resultado['total_organizacoes']}",
        f"Organizações em lista curta preliminar: {resultado['total_lista_curta']}",
        f"Arquivo risco: {resultado['output_risk']}",
        f"Arquivo lista curta: {resultado['output_shortlist']}",
        f"Arquivo evidências: {resultado['output_evidence']}",
        "",
        "Resumo por município:",
    ]

    for municipio, valores in sorted(resultado["resumo"].items()):
        conteudo.append(
            f"- {municipio}: {valores['total']} avaliadas; "
            f"{valores['baixo']} baixo risco; {valores['moderado']} moderado; "
            f"{valores['alto']} alto; {valores['lista_curta']} lista curta."
        )

    conteudo.extend([
        "",
        f"Linhas no risk_osc_screening.csv: {len(risk)}",
        f"Linhas na lista curta: {len(shortlist)}",
        f"Linhas de evidência: {len(evidence)}",
        "",
        "Resultado: SUCESSO.",
        "O screening preliminar de risco de OSCs foi gerado e está pronto para diligência documental.",
        "",
        "Limitação: resultado não seleciona executora. Exige validação documental, jurídica, contato ativo, entrevista e visita técnica.",
    ])

    texto = "\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)

if __name__ == "__main__":
    main()
