"""
Funções de normalização consolidadas de múltiplos módulos.

Refactor/Phase1: Consolidação de normalizadores dispersos em:
- Antigo: src/fito_aimm/normalizador.py (removido)
- Antigo: src/fito_aimm/coletor_mapaosc.py (linhas 85-99)

Changelog:
- 2026-07-02: Consolidação inicial em utils/normalization.py
"""

import re
import unicodedata
from typing import Any


def por_milhao(valor: float, investimento: float) -> float:
    """
    Calcula proporção por milhão.
    
    Args:
        valor: Valor a ser normalizado
        investimento: Denominador (investimento em reais)
        
    Returns:
        float: Valor por milhão de investimento
        
    Raises:
        ValueError: Se investimento <= 0
        
    Example:
        >>> por_milhao(1000, 50_000_000)
        0.02
    """
    if investimento <= 0:
        raise ValueError("Investimento deve ser maior que zero.")
    return valor / (investimento / 1_000_000)


def percentual(parte: float, total: float) -> float:
    """
    Calcula percentual com proteção contra divisão por zero.
    
    Args:
        parte: Numerador (parte)
        total: Denominador (todo)
        
    Returns:
        float: Percentual (0.0 se total == 0)
        
    Example:
        >>> percentual(25, 100)
        0.25
        >>> percentual(10, 0)
        0.0
    """
    if total == 0:
        return 0.0
    return parte / total


def remover_acentos(texto: str) -> str:
    """
    Remove acentos de texto preservando a estrutura.
    
    Args:
        texto: Texto com possíveis acentos
        
    Returns:
        str: Texto sem acentos
        
    Example:
        >>> remover_acentos("Manaus")
        'Manaus'
        >>> remover_acentos("São Paulo")
        'Sao Paulo'
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto or ""))
        if not unicodedata.combining(c)
    )


def normalizar_texto(texto: Any, remover_acentos_flag: bool = True) -> str:
    """
    Normaliza texto para comparação: lowercase, sem espaços extras, opcionalmente sem acentos.
    
    Args:
        texto: Texto a normalizar (aceita None)
        remover_acentos_flag: Se True, remove acentos
        
    Returns:
        str: Texto normalizado
        
    Example:
        >>> normalizar_texto("  MANAUS  ")
        'manaus'
        >>> normalizar_texto("SÃO PAULO", remover_acentos_flag=True)
        'sao paulo'
    """
    texto = str(texto or "").lower().strip()
    if remover_acentos_flag:
        texto = remover_acentos(texto)
    return re.sub(r"\s+", " ", texto)


def normalizar_coluna(nome: str) -> str:
    """
    Normaliza nome de coluna para snake_case.
    
    Args:
        nome: Nome de coluna original
        
    Returns:
        str: Nome normalizado (snake_case)
        
    Example:
        >>> normalizar_coluna("Razão Social")
        'razao_social'
        >>> normalizar_coluna("CNPJ/ID")
        'cnpj_id'
    """
    nome = normalizar_texto(nome, remover_acentos_flag=True)
    return re.sub(r"[^a-z0-9]+", "_", nome).strip("_")


def detectar_delimitador(amostra: str) -> str:
    """
    Detecta delimitador de CSV (`;`, `,`, `\t`, `|`).
    
    Args:
        amostra: Primeiras linhas de arquivo CSV
        
    Returns:
        str: Delimitador mais provável
        
    Example:
        >>> detectar_delimitador("a;b;c\\n1;2;3")
        ';'
    """
    linhas = [linha for linha in amostra.splitlines() if linha.strip()]
    primeira_linha = linhas[0] if linhas else ""
    return max(";", ",", "\t", "|"], key=lambda sep: primeira_linha.count(sep))


def detectar_encoding(amostra_bytes: bytes) -> str:
    """
    Detecta encoding de bytes tentando decodificar com múltiplas opções.
    
    Args:
        amostra_bytes: Primeiros bytes de arquivo
        
    Returns:
        str: Encoding detectado (padrão: 'latin1')
        
    Example:
        >>> detectar_encoding(b'Manaus')
        'utf-8'
    """
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin1", "iso-8859-1"]:
        try:
            amostra_bytes.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin1"
