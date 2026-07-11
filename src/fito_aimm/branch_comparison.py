"""
Agente — Comparação entre branches (AIMM).

Compara um branch-alvo com o ``main``, de forma factual, e produz:

- diff classificado (ADICIONADO / MODIFICADO / REMOVIDO / RUIDO);
- ruído de versionamento isolado e quantificado (``__pycache__``, ``.pyc``,
  arquivos ``=...`` de erro de shell, logs);
- impacto no núcleo da cadeia AIMM (modificação em ``aimm_engine``,
  ``aimm_dashboard``, ``aimm_communication`` ou ``app.py``);
- módulos Python novos com suas classes e funções públicas (via AST).

O agente NÃO funde branches, NÃO decide merge, NÃO avalia mérito. Descreve o que
muda, com rastreabilidade.

Uso:
    from fito_aimm.branch_comparison import execute_branch_comparison
    resultado = execute_branch_comparison("refactor/phase2")

Convenções do repositório: função pública ``execute_*``; saídas CSV ``;`` /
``utf-8-sig``; retorno estruturado com ``errors``.
"""

from __future__ import annotations

import ast
import csv
import subprocess
from pathlib import Path
from typing import Any

BASE_REF = "origin/main"

# Módulos-núcleo da cadeia AIMM (modificação neles = impacto no núcleo).
_NUCLEO = {
    "src/fito_aimm/aimm_engine.py",
    "src/fito_aimm/aimm_dashboard.py",
    "src/fito_aimm/aimm_communication.py",
    "app.py",
}

# Prefixos de função pública reconhecidos (convenções do repositório).
_EXEC_PREFIXES = ("execute_", "executar_", "coletar_")

OUT_TABLE = Path("docs/BRANCH_COMPARISON_TABLE.csv")


def _run_git(args: list[str]) -> str:
    """Executa git e retorna stdout (string). Lança em erro."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falhou: {result.stderr.strip()}")
    return result.stdout


def _is_ruido(caminho: str) -> bool:
    nome = caminho.split("/")[-1]
    return (
        "__pycache__" in caminho
        or caminho.endswith(".pyc")
        or nome.startswith("=")
        or caminho.endswith(".log")
    )


def _categoria(caminho: str) -> str:
    if caminho.endswith(".py"):
        return "modulo_python"
    if caminho.endswith((".md", ".txt")):
        return "documento"
    if caminho.startswith("config/") or caminho.endswith((".yaml", ".yml")) and ".github" not in caminho:
        return "config"
    if ".github/workflows" in caminho:
        return "workflow"
    if caminho.startswith("data/") or caminho.endswith((".csv", ".xls", ".xlsx", ".pdf", ".gpkg")):
        return "dado"
    return "outro"


def _tipo(status: str) -> str:
    return {"A": "ADICIONADO", "M": "MODIFICADO", "D": "REMOVIDO"}.get(status[0], "MODIFICADO")


def _classes_e_funcoes(branch: str, caminho: str) -> list[str]:
    """Extrai classes e funções públicas de um módulo do branch, via AST."""
    try:
        src = _run_git(["show", f"origin/{branch}:{caminho}"])
        tree = ast.parse(src, filename=caminho)
    except Exception:
        return []
    itens: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            itens.append(f"class {node.name}")
        elif isinstance(node, ast.FunctionDef):
            if node.name == "main" or node.name.startswith(_EXEC_PREFIXES):
                itens.append(f"def {node.name}")
    return itens


def _magnitude(branch: str, caminho: str) -> str:
    """Retorna 'X+ Y-' de git diff --stat para um arquivo modificado."""
    try:
        out = _run_git(["diff", "--numstat", f"{BASE_REF}...origin/{branch}", "--", caminho])
        if out.strip():
            partes = out.split()
            if len(partes) >= 2:
                return f"{partes[0]}+ {partes[1]}-"
    except Exception:
        pass
    return "?"


def execute_branch_comparison(branch: str, append_table: bool = True) -> dict[str, Any]:
    errors: list[str] = []

    # Confirma que o branch existe.
    remotos = _run_git(["branch", "-r"])
    if f"origin/{branch}" not in remotos:
        raise ValueError(f"Branch remoto não encontrado: origin/{branch}. Rode git fetch --all.")

    ahead = _run_git(["rev-list", "--count", f"{BASE_REF}..origin/{branch}"]).strip()
    behind = _run_git(["rev-list", "--count", f"origin/{branch}..{BASE_REF}"]).strip()
    commit = _run_git(["rev-parse", "--short", f"origin/{branch}"]).strip()

    # Diff classificado.
    diff = _run_git(["diff", "--name-status", f"{BASE_REF}...origin/{branch}"])
    linhas_tabela: list[dict[str, str]] = []
    adicionados: list[str] = []
    modificados: list[str] = []
    removidos: list[str] = []
    ruido: list[str] = []
    nucleo_modificado: list[dict[str, str]] = []
    modulos_novos: list[dict[str, Any]] = []

    for linha in diff.splitlines():
        if not linha.strip():
            continue
        partes = linha.split("\t")
        status = partes[0]
        caminho = partes[-1]

        if _is_ruido(caminho):
            ruido.append(caminho)
            linhas_tabela.append({
                "branch": branch, "arquivo": caminho, "tipo": "RUIDO",
                "categoria": _categoria(caminho), "impacto_nucleo": "nao",
                "observacao": "ruido de versionamento (nao contado como conteudo)",
            })
            continue

        tipo = _tipo(status)
        is_nucleo = caminho in _NUCLEO and tipo == "MODIFICADO"
        obs = ""

        if tipo == "ADICIONADO":
            adicionados.append(caminho)
            if caminho.startswith("src/") and caminho.endswith(".py"):
                itens = _classes_e_funcoes(branch, caminho)
                modulos_novos.append({"arquivo": caminho, "itens": itens})
                obs = f"{len(itens)} classe(s)/funcao(oes)" if itens else "sem classe/funcao publica"
        elif tipo == "MODIFICADO":
            modificados.append(caminho)
            if is_nucleo:
                mag = _magnitude(branch, caminho)
                nucleo_modificado.append({"arquivo": caminho, "magnitude": mag})
                obs = f"NUCLEO modificado: {mag}"
        elif tipo == "REMOVIDO":
            removidos.append(caminho)

        linhas_tabela.append({
            "branch": branch, "arquivo": caminho, "tipo": tipo,
            "categoria": _categoria(caminho),
            "impacto_nucleo": "sim" if is_nucleo else "nao",
            "observacao": obs,
        })

    # Persistir tabela (append ou create).
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    fields = ["branch", "arquivo", "tipo", "categoria", "impacto_nucleo", "observacao"]
    existe = OUT_TABLE.exists()
    modo = "a" if (append_table and existe) else "w"
    with OUT_TABLE.open(modo, encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        if modo == "w":
            w.writeheader()
        w.writerows(linhas_tabela)

    return {
        "errors": errors,
        "branch": branch,
        "commit": commit,
        "ahead": ahead,
        "behind": behind,
        "total_adicionados": len(adicionados),
        "total_modificados": len(modificados),
        "total_removidos": len(removidos),
        "total_ruido": len(ruido),
        "impacto_nucleo": "sim" if nucleo_modificado else "nao",
        "nucleo_modificado": nucleo_modificado,
        "modulos_novos": modulos_novos,
        "adicionados": adicionados,
        "modificados": modificados,
        "removidos": removidos,
        "ruido_amostra": ruido[:5],
    }


if __name__ == "__main__":
    import sys
    alvo = sys.argv[1] if len(sys.argv) > 1 else "refactor/phase2"
    r = execute_branch_comparison(alvo)
    print(f"Branch: {r['branch']} (ahead={r['ahead']}, behind={r['behind']})")
    print(f"Adicionados: {r['total_adicionados']} | Modificados: {r['total_modificados']} | "
          f"Removidos: {r['total_removidos']} | Ruído: {r['total_ruido']}")
    print(f"Impacto no núcleo: {r['impacto_nucleo']}")
    for nm in r["nucleo_modificado"]:
        print(f"  núcleo: {nm['arquivo']} ({nm['magnitude']})")
