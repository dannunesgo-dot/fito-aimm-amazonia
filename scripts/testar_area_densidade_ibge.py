from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.coletor_ibge_geociencias import executar_pipeline_area_densidade_ibge


ARQUIVO_LOG = Path("data/reference/fetch_log.csv")
ARQUIVO_RESULTADO = Path("data/processed/territorios_ibge_area_densidade.csv")
ARQUIVO_EVIDENCIA = Path("data/evidence/evidence_ibge_area_densidade.csv")
RELATORIO = Path("outputs/logs/teste_area_densidade_ibge.txt")


def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def main():
    resultado = executar_pipeline_area_densidade_ibge(arquivo_log=ARQUIVO_LOG)

    linhas = ler_csv(ARQUIVO_RESULTADO)
    evidencias = ler_csv(ARQUIVO_EVIDENCIA)
    fetch_log = ler_csv(ARQUIVO_LOG)

    if len(linhas) != 4:
        raise ValueError(f"Esperadas 4 linhas no resultado; obtidas {len(linhas)}.")

    if len(evidencias) != 4:
        raise ValueError(f"Esperadas 4 evidências; obtidas {len(evidencias)}.")

    campos = [
        "codigo_municipio_ibge",
        "municipio",
        "uf",
        "populacao_estimada",
        "area_territorial_km2",
        "densidade_estimada_hab_km2",
        "fonte_area",
        "fonte_populacao",
        "limitacao",
    ]

    for numero, linha in enumerate(linhas, start=2):
        for campo in campos:
            if not (linha.get(campo) or "").strip():
                raise ValueError(f"Linha {numero}: campo obrigatório vazio: {campo}")

        area = float(linha["area_territorial_km2"])
        dens = float(linha["densidade_estimada_hab_km2"])
        pop = float(linha["populacao_estimada"])

        if area <= 0:
            raise ValueError(f"Linha {numero}: área inválida: {area}")
        if dens <= 0:
            raise ValueError(f"Linha {numero}: densidade inválida: {dens}")
        if abs((pop / area) - dens) > 0.01:
            raise ValueError(f"Linha {numero}: densidade incoerente com população/área.")

    sucessos = [l for l in fetch_log if l.get("status_coleta") == "sucesso"]
    if len(sucessos) < 2:
        raise ValueError("fetch_log.csv deveria conter pelo menos duas coletas bem-sucedidas na rodada.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE ÁREA TERRITORIAL E DENSIDADE — IBGE/Geociências — Fito+ Amazônia",
        "=" * 84,
        f"Arquivo resultado: {ARQUIVO_RESULTADO}",
        f"Arquivo evidências: {ARQUIVO_EVIDENCIA}",
        f"Arquivo fetch_log: {ARQUIVO_LOG}",
        "",
        f"Linhas de população: {len(resultado['populacao'])}",
        f"Linhas de áreas: {len(resultado['areas'])}",
        f"Linhas de área/densidade: {len(linhas)}",
        f"Linhas de evidências: {len(evidencias)}",
        "",
        "Área territorial e densidade estimada:",
    ]

    for linha in linhas:
        conteudo.append(
            f"- {linha['municipio']}/{linha['uf']} ({linha['codigo_municipio_ibge']}): "
            f"área {linha['area_territorial_km2']} km²; "
            f"população {linha['populacao_estimada']}; "
            f"densidade estimada {linha['densidade_estimada_hab_km2']} hab/km²."
        )

    conteudo.extend([
        "",
        "Resultado: SUCESSO.",
        "O coletor de IBGE/Geociências baixou a planilha oficial de áreas territoriais, extraiu os municípios do projeto, calculou densidade estimada e gerou evidências auditáveis.",
        "",
        "Limitação: densidade estimada não substitui densidade demográfica censitária oficial."
    ])

    texto = "\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
