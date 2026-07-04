"""
Camada de consulta SQL sobre o storage SQLite.
Oferece busca por OSCs, territórios e evidências usando a Storage persistente.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fito_aimm.storage import Storage, get_storage


@dataclass
class ResultadoBusca:
    id_fonte: str
    consulta: str
    url: str
    titulo: str
    status: str


def registrar_consulta(
    id_fonte: str,
    consulta: str,
    url: str,
    titulo: str = "",
) -> ResultadoBusca:
    """Registra uma consulta (compatível com interface v0.1)."""
    return ResultadoBusca(
        id_fonte=id_fonte,
        consulta=consulta,
        url=url,
        titulo=titulo,
        status="registrada",
    )


# ---------------------------------------------------------------------------
# Busca de OSCs
# ---------------------------------------------------------------------------

def buscar_oscs(
    municipio: str | None = None,
    uf: str | None = None,
    min_score: int | None = None,
    classificacao: str | None = None,
    texto: str | None = None,
    limit: int = 100,
    storage: Storage | None = None,
) -> list[dict[str, Any]]:
    """Busca OSCs no storage com filtros combinados.

    Args:
        municipio: Nome do município para filtrar (parcial, sem acento).
        uf: Sigla da UF para filtrar (ex: "AM", "PA").
        min_score: Score mínimo de triagem (inclusive).
        classificacao: Classificação de triagem ("alta_prioridade", etc.).
        texto: Texto livre para busca no nome ou área de atuação.
        limit: Número máximo de resultados.
        storage: Instância de Storage; usa instância global se None.

    Returns:
        Lista de organizações que atendem aos critérios.
    """
    st = storage or get_storage()
    partes: list[str] = []
    params: list[Any] = []

    if municipio:
        partes.append('LOWER("municipio") LIKE LOWER(?)')
        params.append(f"%{municipio}%")

    if uf:
        partes.append('"uf" = ?')
        params.append(uf.upper())

    if min_score is not None:
        partes.append("CAST(\"score_triagem\" AS INTEGER) >= ?")
        params.append(int(min_score))

    if classificacao:
        partes.append('"classificacao_triagem" = ?')
        params.append(classificacao)

    if texto:
        partes.append(
            '(LOWER("nome_organizacao") LIKE LOWER(?) OR LOWER("area_atuacao_ou_atividade") LIKE LOWER(?))'
        )
        params.extend([f"%{texto}%", f"%{texto}%"])

    where = ("WHERE " + " AND ".join(partes)) if partes else ""
    sql = (
        f'SELECT * FROM "organizacoes_candidatas_mapaosc" {where} '
        f'ORDER BY CAST("score_triagem" AS INTEGER) DESC '
        f"LIMIT {int(limit)}"
    )
    return st.query(sql, params)


def buscar_territorios(
    uf: str | None = None,
    regiao: str | None = None,
    storage: Storage | None = None,
) -> list[dict[str, Any]]:
    """Busca territórios no baseline IBGE com filtros opcionais.

    Args:
        uf: Sigla da UF para filtrar.
        regiao: Nome (parcial) da região geográfica.
        storage: Instância de Storage; usa instância global se None.

    Returns:
        Lista de territórios que atendem aos critérios.
    """
    st = storage or get_storage()
    partes: list[str] = []
    params: list[Any] = []

    if uf:
        partes.append('"uf" = ?')
        params.append(uf.upper())

    if regiao:
        partes.append('LOWER("regiao_nome") LIKE LOWER(?)')
        params.append(f"%{regiao}%")

    where = ("WHERE " + " AND ".join(partes)) if partes else ""
    sql = f'SELECT * FROM "territorios_ibge_baseline" {where} ORDER BY "municipio"'
    return st.query(sql, params)


def buscar_por_texto(
    texto: str,
    tabelas: list[str] | None = None,
    limit_por_tabela: int = 50,
    storage: Storage | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Busca texto livre em múltiplas tabelas do storage.

    Varre todas as colunas de cada tabela usando LIKE.

    Args:
        texto: Texto para busca (case-insensitive).
        tabelas: Lista de tabelas a pesquisar; usa todas disponíveis se None.
        limit_por_tabela: Máximo de resultados por tabela.
        storage: Instância de Storage; usa instância global se None.

    Returns:
        Dicionário ``{tabela: [registros]}`` com resultados por tabela.
    """
    st = storage or get_storage()
    # Obtém tabelas via listar_tabelas() para garantir que só consultamos tabelas existentes
    tabelas_existentes = set(st.listar_tabelas())
    tabelas_alvo = [t for t in (tabelas or list(tabelas_existentes)) if t in tabelas_existentes]
    resultados: dict[str, list[dict[str, Any]]] = {}

    for tabela in tabelas_alvo:
        # Descobre colunas usando PRAGMA parametrizado (tabela já validada contra lista SQLite)
        try:
            info = st.query("SELECT name FROM pragma_table_info(?)", [tabela])
        except Exception:
            continue
        colunas = [row["name"] for row in info if row.get("name") not in ("id", "data_hora_utc")]
        if not colunas:
            continue

        clausulas = [f'LOWER("{c}") LIKE LOWER(?)' for c in colunas]
        where = " OR ".join(clausulas)
        params_busca = [f"%{texto}%"] * len(colunas)
        sql = f'SELECT * FROM "{tabela}" WHERE {where} LIMIT {int(limit_por_tabela)}'

        try:
            rows = st.query(sql, params_busca)
            if rows:
                resultados[tabela] = rows
        except Exception:
            continue

    return resultados


def buscar_evidencias(
    id_indicador: str | None = None,
    territorio: str | None = None,
    status: str | None = None,
    storage: Storage | None = None,
) -> list[dict[str, Any]]:
    """Busca evidências registradas no storage.

    Args:
        id_indicador: Código do indicador (ex: "GAP_TERR_01").
        territorio: Nome do território (parcial).
        status: Status da evidência ("validada", "pendente", etc.).
        storage: Instância de Storage; usa instância global se None.

    Returns:
        Lista de evidências que atendem aos critérios.
    """
    st = storage or get_storage()
    partes: list[str] = []
    params: list[Any] = []

    if id_indicador:
        partes.append('LOWER("id_indicador") LIKE LOWER(?)')
        params.append(f"%{id_indicador}%")

    if territorio:
        partes.append('LOWER("territorio") LIKE LOWER(?)')
        params.append(f"%{territorio}%")

    if status:
        partes.append('"status_evidencia" = ?')
        params.append(status)

    where = ("WHERE " + " AND ".join(partes)) if partes else ""
    sql = f'SELECT * FROM "evidencias" {where} ORDER BY "id_evidencia"'
    return st.query(sql, params)


def resumo_storage(storage: Storage | None = None) -> dict[str, int]:
    """Retorna contagem de registros em todas as tabelas do storage.

    Args:
        storage: Instância de Storage; usa instância global se None.

    Returns:
        Dicionário ``{tabela: contagem}``.
    """
    st = storage or get_storage()
    return {tabela: st.contar_registros(tabela) for tabela in st.listar_tabelas()}
