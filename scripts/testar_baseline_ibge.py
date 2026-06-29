from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.coletor_ibge import executar_pipeline_baseline_ibge


ARQUIVO_LOG = Path("data/reference/fetch_log.csv")
ARQUIVO_BASELINE = Path("data/processed/territorios_ibge_baseline.csv")
ARQUIVO_EVIDENCIAS = Path("data/evidence/evidence_ibge_territorios.csv")
RELATORIO = Path("outputs/logs/teste_baseline_ibge.txt")


def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def main():
    resultado = executar_pipeline_baseline_ibge(arquivo_log=ARQUIVO_LOG)

    baseline = ler_csv(ARQUIVO_BASELINE)
    evidencias = ler_csv(ARQUIVO_EVIDENCIAS)
    fetch_log = ler_csv(ARQUIVO_LOG)

    if len(baseline) != 4:
        raise ValueError(f"Baseline deveria conter 4 municípios; contém {len(baseline)}.")

    if len(evidencias) != 4:
        raise ValueError(f"Evidências territoriais deveriam conter 4 linhas; contêm {len(evidencias)}.")

    campos_baseline = [
        "codigo_municipio_ibge",
        "municipio",
        "uf",
        "regiao_nome",
        "populacao_estimada",
        "ano_populacao_estimada",
        "status_baseline",
    ]

    for numero, linha in enumerate(baseline, start=2):
        for campo in campos_baseline:
            if not (linha.get(campo) or "").strip():
                raise ValueError(f"Baseline linha {numero}: campo obrigatório vazio: {campo}")

        float(linha["populacao_estimada"].replace(".", "").replace(",", "."))

    sucessos_recentes = [linha for linha in fetch_log if linha.get("status_coleta") == "sucesso"]
    if len(sucessos_recentes) < 2:
        raise ValueError("fetch_log.csv deveria conter ao menos 2 coletas com sucesso nesta rodada.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE BASELINE IBGE/SIDRA + LOCALIDADES — Fito+ Amazônia",
        "=" * 72,
        f"Arquivo baseline: {ARQUIVO_BASELINE}",
        f"Arquivo evidências: {ARQUIVO_EVIDENCIAS}",
        f"Arquivo fetch_log: {ARQUIVO_LOG}",
        "",
        f"Linhas de população: {len(resultado['populacao'])}",
        f"Linhas de localidades: {len(resultado['localidades'])}",
        f"Linhas de baseline: {len(baseline)}",
        f"Linhas de evidências: {len(evidencias)}",
        "",
        "Baseline municipal coletado:",
    ]

    for linha in baseline:
        conteudo.append(
            f"- {linha['municipio']}/{linha['uf']} "
            f"({linha['codigo_municipio_ibge']}): {linha['populacao_estimada']} pessoas; "
            f"região {linha['regiao_nome']}; região imediata {linha['regiao_imediata_nome']}; "
            f"ano {linha['ano_populacao_estimada']}"
        )

    conteudo.extend([
        "",
        "Resultado: SUCESSO.",
        "A coleta ampliada IBGE/SIDRA + Localidades gerou baseline territorial e evidências auditáveis.",
        "",
        "Limitação registrada: área territorial, densidade e ruralidade serão incorporadas após confirmação das tabelas/arquivos oficiais adequados.",
    ])

    texto = "\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
