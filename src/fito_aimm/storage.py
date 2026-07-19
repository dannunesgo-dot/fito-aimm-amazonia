"""
Camada de armazenamento consultável (SQLite + Parquet).
Substitui o pipeline exclusivo em CSV por storage queryable com suporte a consultas SQL.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

try:
    import pandas as pd
    _PANDAS_OK = True
except ImportError:  # pragma: no cover
    _PANDAS_OK = False


_DEFAULT_DB = Path("data/storage/fito_aimm.sqlite")


class Storage:
    """Armazenamento SQLite thread-safe com suporte a exportação/importação Parquet."""

    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        # Inicializa WAL mode para melhor concorrência em leituras paralelas
        with self._conexao() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA synchronous=NORMAL")

    def _conexao(self) -> sqlite3.Connection:
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level=None,  # autocommit; transações gerenciadas explicitamente
            )
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def fechar(self) -> None:
        """Fecha a conexão SQLite da thread atual, liberando recursos."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    @contextmanager
    def _transacao(self) -> Generator[sqlite3.Connection, None, None]:
        con = self._conexao()
        con.execute("BEGIN")
        try:
            yield con
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise

    def _garantir_colunas(self, con: sqlite3.Connection, tabela: str, colunas: list[str]) -> None:
        """Adiciona colunas que ainda não existem na tabela."""
        existentes = {
            row["name"]
            for row in con.execute(
                "SELECT name FROM pragma_table_info(?)", (tabela,)
            ).fetchall()
        }
        for col in colunas:
            if col not in existentes:
                # Usa aspas duplas padrão SQL para identificadores
                con.execute(
                    f'ALTER TABLE "{tabela}" ADD COLUMN "{col}" TEXT'
                )

    def _criar_tabela(self, con: sqlite3.Connection, tabela: str, colunas: list[str]) -> None:
        cols_def = ", ".join(f'"{c}" TEXT' for c in colunas)
        con.execute(
            f'CREATE TABLE IF NOT EXISTS "{tabela}" '
            f"(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            f"data_hora_utc TEXT DEFAULT CURRENT_TIMESTAMP, "
            f"{cols_def})"
        )

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    # Colunas gerenciadas internamente pelo Storage; não devem ser inseridas pelo usuário.
    _COLUNAS_RESERVADAS = frozenset({"id", "data_hora_utc"})

    def salvar_registros(self, tabela: str, registros: list[dict[str, Any]]) -> int:
        """Insere registros na tabela, criando-a e adicionando colunas automaticamente.

        Colunas reservadas (``id``, ``data_hora_utc``) são ignoradas para evitar
        conflitos com as colunas internas do Storage.

        Returns:
            Número de registros inseridos.
        """
        if not registros:
            return 0

        self._validar_identificador(tabela)

        # Filtra colunas reservadas antes de qualquer operação
        colunas = [
            self._validar_identificador(c)
            for c in registros[0].keys()
            if c not in self._COLUNAS_RESERVADAS
        ]
        if not colunas:
            return 0

        with self._transacao() as con:
            self._criar_tabela(con, tabela, colunas)
            self._garantir_colunas(con, tabela, colunas)

            cols_quoted = ", ".join(f'"{c}"' for c in colunas)
            placeholders = ", ".join("?" * len(colunas))
            sql = f'INSERT INTO "{tabela}" ({cols_quoted}) VALUES ({placeholders})'
            valores = [
                [str(r.get(c) if r.get(c) is not None else "") for c in colunas]
                for r in registros
            ]
            con.executemany(sql, valores)
        return len(registros)

    def carregar_registros(
        self,
        tabela: str,
        filtros: dict[str, str] | None = None,
        limit: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[dict[str, str]]:
        """Carrega registros de uma tabela com filtros opcionais.

        Returns:
            Lista de dicionários com os registros encontrados.
        """
        self._validar_identificador(tabela)
        con = self._conexao()
        if not self._tabela_existe(con, tabela):
            return []

        sql = f'SELECT * FROM "{tabela}"'
        params: list[str] = []

        if filtros:
            for k in filtros:
                self._validar_identificador(k)
            clausulas = [f'"{k}" = ?' for k in filtros]
            sql += " WHERE " + " AND ".join(clausulas)
            params.extend(str(v) for v in filtros.values())

        if order_by:
            self._validar_identificador(order_by)
            direcao = "DESC" if order_desc else "ASC"
            sql += f' ORDER BY "{order_by}" {direcao}'

        if limit is not None:
            sql += f" LIMIT {int(limit)}"

        cursor = con.execute(sql, params)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def query(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        """Executa SQL de leitura arbitrário e retorna lista de dicionários.

        Use para consultas complexas com JOIN, GROUP BY, etc.
        """
        con = self._conexao()
        cursor = con.execute(sql, params or [])
        if cursor.description is None:
            return []
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def exportar_parquet(self, tabela: str, destino: Path) -> Path:
        """Exporta tabela SQLite para Parquet via pandas/pyarrow."""
        if not _PANDAS_OK:
            raise ImportError("pandas é necessário para exportar Parquet.")
        registros = self.carregar_registros(tabela)
        if not registros:
            raise ValueError(f"Tabela '{tabela}' está vazia.")
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(registros).to_parquet(destino, index=False)
        return destino

    def importar_parquet(self, tabela: str, origem: Path) -> int:
        """Importa dados de um arquivo Parquet para uma tabela SQLite."""
        if not _PANDAS_OK:
            raise ImportError("pandas é necessário para importar Parquet.")
        df = pd.read_parquet(Path(origem))
        registros = df.to_dict(orient="records")
        return self.salvar_registros(tabela, registros)

    def listar_tabelas(self) -> list[str]:
        """Lista todas as tabelas no banco de dados."""
        con = self._conexao()
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]

    def contar_registros(self, tabela: str) -> int:
        """Conta registros em uma tabela. Retorna 0 se a tabela não existir."""
        self._validar_identificador(tabela)
        con = self._conexao()
        if not self._tabela_existe(con, tabela):
            return 0
        row = con.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()
        return int(row[0]) if row else 0

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _validar_identificador(nome: str) -> str:
        """Valida que um identificador SQL não contém aspas duplas (escape de identificadores).

        Identificadores são envolvidos em aspas duplas no SQL gerado; rejeita nomes
        que contenham aspas duplas para prevenir injeção via interpolação de string.
        """
        if '"' in nome:
            raise ValueError(
                f"Nome de tabela ou coluna inválido: '{nome}'. "
                "Identificadores não podem conter aspas duplas."
            )
        return nome

    @staticmethod
    def _tabela_existe(con: sqlite3.Connection, tabela: str) -> bool:
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (tabela,),
        ).fetchone()
        return row is not None


# ------------------------------------------------------------------
# Instância global por processo (singleton)
# ------------------------------------------------------------------

_storage_global: Storage | None = None
_storage_lock = threading.Lock()


def get_storage(db_path: Path = _DEFAULT_DB) -> Storage:
    """Retorna instância global de Storage (singleton por processo)."""
    global _storage_global
    with _storage_lock:
        if _storage_global is None or _storage_global.db_path != Path(db_path):
            _storage_global = Storage(db_path)
    return _storage_global
