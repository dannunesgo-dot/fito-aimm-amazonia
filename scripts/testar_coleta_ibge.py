from pathlib import Path
import csv
import sys

# Permite importar src/fito_aimm quando executado pela raiz do repositório.
sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.territorios import carregar_municipios_projeto
from fito_aimm.coletor_ibge import coletar_populacao_estimada_municipios


ARQUIVO_SAIDA = Path("data/raw/ibge/populacao_estimada_municipios.csv")
ARQUIVO_LOG = Path("data/reference/fetch_log.csv")
RELATORIO = Path("outputs/logs/teste_coleta_ibge.txt")

EXPECTED_MUNICIPIOS = len(carregar_municipios_projeto())


def ler_csv(caminho: Path):
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def main():
    linhas = coletar_populacao_estimada_municipios(
        arquivo_saida=ARQUIVO_SAIDA,
        arquivo_log=ARQUIVO_LOG,
        periodo="last",
    )

    if len(linhas) != EXPECTED_MUNICIPIOS:
        raise ValueError(f"Esperadas {EXPECTED_MUNICIPIOS} linhas de municípios; obtidas {len(linhas)}.")

    campos_obrigatorios = [
        "id_indicador",
        "fonte",
        "tabela_sidra",
        "variavel_sidra",
        "codigo_municipio_ibge",
        "municipio",
        "uf",
        "ano",
        "valor",
        "unidade",
    ]

    for numero, linha in enumerate(linhas, start=2):
        for campo in campos_obrigatorios:
            if not (linha.get(campo) or "").strip():
                raise ValueError(f"Linha {numero}: campo obrigatório vazio: {campo}")

        valor = linha["valor"].replace(".", "").replace(",", ".")
        try:
            float(valor)
        except ValueError as exc:
            raise ValueError(f"Linha {numero}: valor não numérico: {linha['valor']}") from exc

    log_linhas = ler_csv(ARQUIVO_LOG)
    if not log_linhas:
        raise ValueError("fetch_log.csv não recebeu registro da coleta.")

    ultimo_log = log_linhas[-1]
    if ultimo_log.get("status_coleta") != "sucesso":
        raise ValueError(f"Último registro do fetch_log não está como sucesso: {ultimo_log}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    conteudo = [
        "TESTE DE COLETA IBGE/SIDRA — Fito+ Amazônia",
        "=" * 60,
        f"Arquivo de saída: {ARQUIVO_SAIDA}",
        f"Arquivo de log: {ARQUIVO_LOG}",
        f"Linhas extraídas: {len(linhas)}",
        "",
        "Municípios coletados:",
    ]

    for linha in linhas:
        conteudo.append(
            f"- {linha['municipio']}/{linha['uf']} "
            f"({linha['codigo_municipio_ibge']}): {linha['valor']} {linha['unidade']} — ano {linha['ano']}"
        )

    conteudo.extend([
        "",
        "Resultado: SUCESSO.",
        "A conectividade IBGE/SIDRA, a extração, a normalização territorial e o fetch_log.csv funcionaram.",
    ])

    texto = "\n".join(conteudo)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
