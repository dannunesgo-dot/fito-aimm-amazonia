from pathlib import Path
import csv
from collections import Counter

ARQUIVOS = {
    "dicionario": Path("data/reference/dicionario_indicadores.csv"),
    "fontes": Path("data/reference/source_registry.csv"),
    "evidencias": Path("data/evidence/evidence_registry.csv"),
    "plano_buscas": Path("data/reference/query_plan.csv"),
}

SAIDA = Path("outputs/teste_funcional_query_plan_relatorio.txt")

CAMPOS_QUERY_PLAN_OBRIGATORIOS = [
    "id_plano_busca",
    "id_indicador",
    "nome_indicador",
    "papel_indicador",
    "pergunta_principal",
    "fonte_prioritaria",
    "metodo_coleta",
    "campos_a_extrair",
    "regra_conferencia",
    "criterio_aceitacao",
    "status_inicial",
]

def ler_csv(caminho: Path):
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo ausente: {caminho}")

    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        linhas = list(leitor)
        cabecalho = leitor.fieldnames or []

    if not linhas:
        raise ValueError(f"Arquivo sem dados: {caminho}")

    return cabecalho, linhas

def verificar_campos(cabecalho, campos_obrigatorios, nome_base):
    faltantes = [campo for campo in campos_obrigatorios if campo not in cabecalho]
    if faltantes:
        raise ValueError(f"{nome_base}: campos obrigatórios ausentes: {faltantes}")

def verificar_preenchimento(linhas, campos, nome_base):
    erros = []
    for numero_linha, linha in enumerate(linhas, start=2):
        for campo in campos:
            if not (linha.get(campo) or "").strip():
                erros.append(f"{nome_base}: linha {numero_linha} sem preenchimento no campo {campo}")
    return erros

def main():
    relatorio = []
    relatorio.append("TESTE FUNCIONAL QUERY_PLAN — Fito+ Amazônia")
    relatorio.append("=" * 60)

    dados = {}
    cabecalhos = {}

    for nome, caminho in ARQUIVOS.items():
        cabecalho, linhas = ler_csv(caminho)
        cabecalhos[nome] = cabecalho
        dados[nome] = linhas
        relatorio.append(f"{nome}: {len(linhas)} linhas, {len(cabecalho)} colunas — OK")

    verificar_campos(cabecalhos["plano_buscas"], CAMPOS_QUERY_PLAN_OBRIGATORIOS, "query_plan.csv")

    erros_preenchimento = verificar_preenchimento(
        dados["plano_buscas"],
        CAMPOS_QUERY_PLAN_OBRIGATORIOS,
        "query_plan.csv"
    )

    if erros_preenchimento:
        raise ValueError("\n".join(erros_preenchimento[:30]))

    ids_dicionario = {
        (linha.get("id_indicador") or "").strip()
        for linha in dados["dicionario"]
        if (linha.get("id_indicador") or "").strip()
    }

    ids_query = [
        (linha.get("id_indicador") or "").strip()
        for linha in dados["plano_buscas"]
    ]

    ids_query_set = set(ids_query)
    ids_faltando_no_dicionario = sorted(ids_query_set - ids_dicionario)
    ids_sem_plano = sorted(ids_dicionario - ids_query_set)

    if ids_faltando_no_dicionario:
        raise ValueError(f"Há id_indicador no query_plan ausente do dicionário: {ids_faltando_no_dicionario[:20]}")

    if ids_sem_plano:
        raise ValueError(f"Há id_indicador no dicionário sem plano de busca: {ids_sem_plano[:20]}")

    duplicados = [item for item, contagem in Counter(ids_query).items() if contagem > 1]
    if duplicados:
        raise ValueError(f"Há indicadores duplicados no query_plan: {duplicados[:20]}")

    contagem_papel = Counter(linha["papel_indicador"] for linha in dados["plano_buscas"])
    relatorio.append("")
    relatorio.append("Distribuição por papel do indicador:")
    for papel, total in sorted(contagem_papel.items()):
        relatorio.append(f"- {papel}: {total}")

    contagem_status = Counter(linha["status_inicial"] for linha in dados["plano_buscas"])
    relatorio.append("")
    relatorio.append("Distribuição por status inicial:")
    for status, total in sorted(contagem_status.items()):
        relatorio.append(f"- {status}: {total}")

    fontes_registradas = {
        (linha.get("id_fonte") or "").strip()
        for linha in dados["fontes"]
        if (linha.get("id_fonte") or "").strip()
    }

    fontes_query = {
        (linha.get("fonte_prioritaria") or "").strip()
        for linha in dados["plano_buscas"]
        if (linha.get("fonte_prioritaria") or "").strip()
    }

    fontes_nao_cadastradas = sorted(fontes_query - fontes_registradas)

    relatorio.append("")
    relatorio.append(f"Fontes prioritárias distintas no query_plan: {len(fontes_query)}")
    relatorio.append(f"Fontes prioritárias já cadastradas no source_registry: {len(fontes_query & fontes_registradas)}")
    relatorio.append(f"Fontes prioritárias ainda não cadastradas: {len(fontes_nao_cadastradas)}")

    if fontes_nao_cadastradas:
        relatorio.append("")
        relatorio.append("Fontes ainda não cadastradas, aceitáveis como pendências operacionais da próxima rodada:")
        for fonte in fontes_nao_cadastradas:
            relatorio.append(f"- {fonte}")

    relatorio.append("")
    relatorio.append("Resultado final: SUCESSO.")
    relatorio.append("O query_plan.csv está funcionalmente coerente com o dicionário de indicadores.")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(relatorio), encoding="utf-8")

    print("\n".join(relatorio))

if __name__ == "__main__":
    main()
