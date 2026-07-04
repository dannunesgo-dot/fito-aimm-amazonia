
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.territorios import carregar_municipios_projeto
from fito_aimm.coletor_mapaosc import coletar_mapaosc_municipios

ARQUIVO_PROCESSADO = Path("data/processed/organizacoes_candidatas_mapaosc.csv")
ARQUIVO_RESUMO = Path("data/processed/resumo_organizacoes_mapaosc_municipios.csv")
ARQUIVO_EVIDENCIAS = Path("data/evidence/evidence_mapaosc_triagem.csv")
ARQUIVO_LOG = Path("data/reference/fetch_log.csv")
RELATORIO = Path("outputs/logs/teste_mapaosc_triagem.txt")

EXPECTED_MUNICIPIOS = len(carregar_municipios_projeto())

def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))

def main():
    resultado = coletar_mapaosc_municipios()
    processado = ler_csv(ARQUIVO_PROCESSADO)
    resumo = ler_csv(ARQUIVO_RESUMO)
    evidencias = ler_csv(ARQUIVO_EVIDENCIAS)
    fetch_log = ler_csv(ARQUIVO_LOG)

    if len(resumo) != EXPECTED_MUNICIPIOS:
        raise ValueError(f"Resumo municipal deveria conter {EXPECTED_MUNICIPIOS} linhas; contém {len(resumo)}.")
    if len(evidencias) != EXPECTED_MUNICIPIOS:
        raise ValueError(f"Evidências deveriam conter {EXPECTED_MUNICIPIOS} linhas; contêm {len(evidencias)}.")

    campos = ["nome_organizacao","municipio","uf","codigo_municipio_ibge","score_triagem","classificacao_triagem","fonte","limitacao"]
    for numero, linha in enumerate(processado[:20], start=2):
        for campo in campos:
            if campo not in linha:
                raise ValueError(f"Campo ausente no processado: {campo}")
        int(linha["score_triagem"])

    sucessos = [linha for linha in fetch_log if linha.get("fonte") == "SRC_MAPA_OSC" and linha.get("status_coleta") == "sucesso"]
    if not sucessos:
        raise ValueError("fetch_log.csv não contém coleta bem-sucedida SRC_MAPA_OSC.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE TRIAGEM MAPA DAS OSCs/IPEA — Fito+ Amazônia",
        "=" * 72,
        f"Arquivo processado: {ARQUIVO_PROCESSADO}",
        f"Arquivo resumo: {ARQUIVO_RESUMO}",
        f"Arquivo evidências: {ARQUIVO_EVIDENCIAS}",
        f"Arquivo fetch_log: {ARQUIVO_LOG}",
        "",
        f"Linhas processadas: {len(processado)}",
        f"Linhas de resumo municipal: {len(resumo)}",
        f"Linhas de evidência: {len(evidencias)}",
        f"Total de linhas lidas na base de origem: {resultado['total_linhas_lidas']}",
        f"Método de obtenção da base: {resultado['metodo_obtencao_base']}",
        f"Arquivo-base usado: {resultado['arquivo_base']}",
        f"Encoding detectado: {resultado['encoding']}",
        f"Delimitador detectado: {repr(resultado['delimitador'])}",
        "",
        "Resumo por município:",
    ]

    for linha in resumo:
        conteudo.append(
            f"- {linha['municipio']}/{linha['uf']}: "
            f"{linha['total_organizacoes_filtradas']} organizações; "
            f"{linha['alta_prioridade']} alta prioridade; "
            f"{linha['media_prioridade']} média prioridade; "
            f"{linha['com_marcador_cooperativa']} com marcador cooperativa; "
            f"{linha['com_marcador_associacao']} com marcador associação."
        )

    conteudo.append("")
    conteudo.append("Colunas detectadas automaticamente:")
    for chave, valor in resultado["colunas_detectadas"].items():
        conteudo.append(f"- {chave}: {valor}")

    conteudo.extend([
        "",
        "Resultado: SUCESSO.",
        "A triagem automatizada do Mapa das OSCs/Ipea gerou lista inicial de organizações candidatas, resumo municipal, evidências e fetch_log.",
        "",
        "Limitação: triagem remota não seleciona executora. Exige análise documental, contato, regularidade, capacidade operacional e validação de campo.",
    ])

    texto = "\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)

if __name__ == "__main__":
    main()
