from pathlib import Path
import csv

ARQUIVOS = [
    Path("data/reference/source_registry.csv"),
    Path("data/evidence/evidence_registry.csv"),
    Path("data/reference/query_plan.csv"),
]

CAMPOS_OBRIGATORIOS = {
    "data/reference/source_registry.csv": [
        "id_fonte",
        "nome_fonte",
        "tipo_fonte",
        "url_principal",
        "uso_na_calculadora",
        "nivel_confiabilidade",
        "status_verificacao_link",
    ],
    "data/evidence/evidence_registry.csv": [
        "id_evidencia",
        "id_fonte",
        "id_indicador",
        "tipo_evidencia",
        "pergunta_ou_lacuna",
        "status_conferencia",
        "status_evidencia",
    ],
    "data/reference/query_plan.csv": [
        "id_plano_busca",
        "id_indicador",
        "nome_indicador",
        "papel_indicador",
        "pergunta_principal",
        "fonte_prioritaria",
        "fontes_alternativas",
        "metodo_coleta",
        "campos_a_extrair",
        "regra_conferencia",
        "criterio_aceitacao",
        "status_inicial",
    ],
}

PREFIXOS_FONTES_PLANEJADAS = (
    "SRC_CAMPO",
    "SRC_LABS",
    "SRC_ANVISA",
    "SRC_MERCADO",
    "SRC_GIS",
    "SRC_ORCAMENTO",
    "SRC_NOTAS",
    "SRC_CONTRATOS",
    "SRC_SPECIES",
    "SRC_SUS",
    "SRC_SURVEY",
    "SRC_RISK",
    "SRC_ND_GAIN",
    "SRC_CGEN",
    "SRC_CLIMATE",
    "SRC_GESTAO",
    "SRC_LITERATURA",
)

def ler_csv(caminho: Path):
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo ausente: {caminho}")

    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        linhas = list(leitor)
        cabecalho = leitor.fieldnames or []

    return cabecalho, linhas

def validar_estrutura(caminho: Path):
    cabecalho, linhas = ler_csv(caminho)

    campos_obrigatorios = CAMPOS_OBRIGATORIOS.get(str(caminho), [])
    campos_faltantes = [campo for campo in campos_obrigatorios if campo not in cabecalho]

    if campos_faltantes:
        raise ValueError(f"{caminho}: campos obrigatórios ausentes: {campos_faltantes}")

    if not linhas:
        raise ValueError(f"{caminho}: arquivo sem linhas de dados.")

    print(f"{caminho}: {len(linhas)} linhas, {len(cabecalho)} colunas")
    return cabecalho, linhas

def validar_ids_unicos(linhas, campo, nome_arquivo):
    vistos = set()
    duplicados = set()

    for numero_linha, linha in enumerate(linhas, start=2):
        valor = (linha.get(campo) or "").strip()

        if not valor:
            raise ValueError(f"{nome_arquivo}: linha {numero_linha} sem valor no campo {campo}")

        if valor in vistos:
            duplicados.add(valor)

        vistos.add(valor)

    if duplicados:
        raise ValueError(f"{nome_arquivo}: IDs duplicados em {campo}: {sorted(duplicados)[:20]}")

def fonte_planejada_aceitavel(id_fonte: str):
    if not id_fonte:
        return False

    return id_fonte.startswith(PREFIXOS_FONTES_PLANEJADAS)

def validar_fontes_do_query_plan(source_registry_linhas, query_plan_linhas):
    fontes_registradas = {
        (linha.get("id_fonte") or "").strip()
        for linha in source_registry_linhas
        if (linha.get("id_fonte") or "").strip()
    }

    fontes_nao_registradas = sorted({
        (linha.get("fonte_prioritaria") or "").strip()
        for linha in query_plan_linhas
        if (linha.get("fonte_prioritaria") or "").strip()
        and (linha.get("fonte_prioritaria") or "").strip() not in fontes_registradas
    })

    fontes_realmente_pendentes = [
        fonte for fonte in fontes_nao_registradas
        if not fonte_planejada_aceitavel(fonte)
    ]

    if fontes_nao_registradas:
        print("")
        print("AVISO: há fontes no query_plan.csv ainda não cadastradas no source_registry.csv.")
        print("Isto é aceitável nesta fase quando a fonte representa coleta de campo, laboratório, orçamento, GIS ou fonte interna futura.")
        print("Fontes não cadastradas encontradas:")
        for fonte in fontes_nao_registradas:
            tipo = "planejada/aceitável" if fonte_planejada_aceitavel(fonte) else "requer cadastro posterior"
            print(f"- {fonte}: {tipo}")

    if fontes_realmente_pendentes:
        print("")
        print("ATENÇÃO: algumas fontes deverão ser formalizadas no source_registry.csv em rodada posterior:")
        for fonte in fontes_realmente_pendentes:
            print(f"- {fonte}")

    return fontes_nao_registradas

def main():
    dados = {}

    for caminho in ARQUIVOS:
        _, linhas = validar_estrutura(caminho)
        dados[str(caminho)] = linhas

    validar_ids_unicos(
        dados["data/reference/source_registry.csv"],
        "id_fonte",
        "source_registry.csv",
    )

    validar_ids_unicos(
        dados["data/evidence/evidence_registry.csv"],
        "id_evidencia",
        "evidence_registry.csv",
    )

    validar_ids_unicos(
        dados["data/reference/query_plan.csv"],
        "id_plano_busca",
        "query_plan.csv",
    )

    fontes_nao_registradas = validar_fontes_do_query_plan(
        dados["data/reference/source_registry.csv"],
        dados["data/reference/query_plan.csv"],
    )

    buscas_planejadas = sum(
        1 for linha in dados["data/reference/query_plan.csv"]
        if (linha.get("status_inicial") or "").strip() == "planejado"
    )

    print("")
    print(f"query_plan.csv: {buscas_planejadas} buscas planejadas.")
    print(f"query_plan.csv: {len(fontes_nao_registradas)} fontes prioritárias ainda não cadastradas no source_registry.csv.")
    print("Validação inicial concluída com query_plan.csv.")
    print("Resultado: SUCESSO.")

if __name__ == "__main__":
    main()
