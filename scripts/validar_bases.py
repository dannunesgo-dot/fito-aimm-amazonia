from pathlib import Path
import csv
import sys

ARQUIVOS = [
    Path("data/reference/source_registry.csv"),
    Path("data/evidence/evidence_registry.csv"),
    Path("data/reference/query_plan.csv"),
]

CAMPOS_OBRIGATORIOS = {
    "data/reference/source_registry.csv": [
        "id_fonte", "nome_fonte", "tipo_fonte", "url_principal",
        "uso_na_calculadora", "nivel_confiabilidade", "status_verificacao_link"
    ],
    "data/evidence/evidence_registry.csv": [
        "id_evidencia", "id_fonte", "id_indicador", "tipo_evidencia",
        "pergunta_ou_lacuna", "status_conferencia", "status_evidencia"
    ],
    "data/reference/query_plan.csv": [
        "id_plano_busca", "id_indicador", "nome_indicador", "papel_indicador",
        "pergunta_principal", "fonte_prioritaria", "metodo_coleta",
        "campos_a_extrair", "regra_conferencia", "criterio_aceitacao", "status_inicial"
    ],
}

def ler_csv(caminho: Path):
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo ausente: {caminho}")
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        linhas = list(leitor)
        cabecalho = leitor.fieldnames or []
    return cabecalho, linhas

def validar_estrutura(caminho: Path):
    cabecalho, linhas = ler_csv(caminho)
    obrigatorios = CAMPOS_OBRIGATORIOS.get(str(caminho), [])
    faltantes = [c for c in obrigatorios if c not in cabecalho]
    if faltantes:
        raise ValueError(f"{caminho}: campos obrigatórios ausentes: {faltantes}")
    if not linhas:
        raise ValueError(f"{caminho}: arquivo sem linhas de dados.")
    print(f"{caminho}: {len(linhas)} linhas, {len(cabecalho)} colunas")
    return cabecalho, linhas

def validar_ids_unicos(linhas, campo, nome_arquivo):
    vistos = set()
    duplicados = set()
    for linha in linhas:
        valor = (linha.get(campo) or "").strip()
        if not valor:
            raise ValueError(f"{nome_arquivo}: há linha sem {campo}")
        if valor in vistos:
            duplicados.add(valor)
        vistos.add(valor)
    if duplicados:
        raise ValueError(f"{nome_arquivo}: IDs duplicados em {campo}: {sorted(duplicados)[:10]}")

def main():
    dados = {}
    for caminho in ARQUIVOS:
        cabecalho, linhas = validar_estrutura(caminho)
        dados[str(caminho)] = linhas

    validar_ids_unicos(dados["data/reference/source_registry.csv"], "id_fonte", "source_registry.csv")
    validar_ids_unicos(dados["data/evidence/evidence_registry.csv"], "id_evidencia", "evidence_registry.csv")
    validar_ids_unicos(dados["data/reference/query_plan.csv"], "id_plano_busca", "query_plan.csv")

    fontes = {linha["id_fonte"].strip() for linha in dados["data/reference/source_registry.csv"]}
    plano = dados["data/reference/query_plan.csv"]

    fontes_nao_registradas = sorted({
        linha["fonte_prioritaria"].strip()
        for linha in plano
        if linha.get("fonte_prioritaria") and linha["fonte_prioritaria"].strip() not in fontes
        and not linha["fonte_prioritaria"].strip().startswith("SRC_CAMPO")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_LABS")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_ANVISA")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_MERCADO")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_GIS")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_ORCAMENTO")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_NOTAS")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_CONTRATOS")
        and not linha["fonte_prioritaria"].strip().startswith("SRC_SPECIES")
    })

    if fontes_nao_registradas:
        raise ValueError(f"query_plan.csv: fontes prioritárias não registradas: {fontes_nao_registradas}")

    planejados = sum(1 for linha in plano if linha.get("status_inicial") == "planejado")
    print(f"query_plan.csv: {planejados} buscas planejadas.")
    print("Validação inicial concluída com query_plan.csv.")

if __name__ == "__main__":
    main()
