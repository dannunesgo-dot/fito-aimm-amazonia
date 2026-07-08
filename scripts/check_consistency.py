#!/usr/bin/env python3
"""
check_consistency.py — Verificação rápida de consistência do repositório Fito+ Amazônia AIMM

Uso:
    python scripts/check_consistency.py
    python scripts/check_consistency.py --root /caminho/para/repositorio

Retorna exit code 0 se tudo OK (ou apenas avisos), 1 se houver falhas.
"""

import sys
import os
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = 0
FAIL = 0
WARN = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        print(f"  [OK]   {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}")
        if detail:
            print(f"         {detail}")
        FAIL += 1


def warn(label: str, detail: str = "") -> None:
    global WARN
    print(f"  [WARN] {label}")
    if detail:
        print(f"         {detail}")
    WARN += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(root: Path) -> int:
    print()
    print("=" * 62)
    print(" Verificação de Consistência — Fito+ Amazônia AIMM")
    print(f" Raiz: {root}")
    print("=" * 62)
    print()

    # ------------------------------------------------------------------
    # 1) Arquivos essenciais de execução
    # ------------------------------------------------------------------
    print("1. Arquivos essenciais de execução")

    essentials = [
        "app.py",
        "requirements.txt",
        ".env.example",
        "run-local.ps1",
        "stop-local.ps1",
        "status-local.ps1",
        "run-tests-local.ps1",
    ]

    for f in essentials:
        path = root / f
        check(f, path.exists(), f"Arquivo não encontrado: {path}")

    # ------------------------------------------------------------------
    # 2) Ambiente local
    # ------------------------------------------------------------------
    print()
    print("2. Ambiente local")

    env_path = root / ".env"
    if env_path.exists():
        check(".env presente (ambiente configurado)", True)
    else:
        warn(".env ausente", "Execute: cp .env.example .env  e preencha os valores")

    venv_python = root / ".venv" / "Scripts" / "python.exe"
    venv_python_linux = root / ".venv" / "bin" / "python"
    venv_ok = venv_python.exists() or venv_python_linux.exists()
    check(
        ".venv/python presente",
        venv_ok,
        "Crie com: python -m venv .venv && pip install -r requirements.txt",
    )

    # ------------------------------------------------------------------
    # 3) Consistência de documentação
    # ------------------------------------------------------------------
    print()
    print("3. Documentação de execução")

    docs = [
        "README.md",
        "README-local.md",
        "docs/INDEX.md",
    ]

    for d in docs:
        path = root / d
        check(d, path.exists(), f"Documento ausente: {path}")

    readme_path = root / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        check(
            "README.md menciona run-local.ps1",
            "run-local.ps1" in content,
            "README.md deve documentar run-local.ps1 como comando oficial",
        )

    readme_local_path = root / "README-local.md"
    if readme_local_path.exists():
        content = readme_local_path.read_text(encoding="utf-8")
        check(
            "README-local.md menciona comando oficial run-local.ps1",
            "run-local.ps1" in content,
            "README-local.md deve referenciar run-local.ps1 como caminho principal",
        )

    # ------------------------------------------------------------------
    # 4) Higiene de repositório
    # ------------------------------------------------------------------
    print()
    print("4. Higiene de repositório")

    tmp_path = root / "tmp"
    if tmp_path.exists():
        tmp_files = [f for f in tmp_path.iterdir() if f.is_file() and f.name != ".gitkeep"]
        if not tmp_files:
            check("tmp/ limpa (apenas .gitkeep)", True)
        else:
            names = ", ".join(f.name for f in tmp_files)
            warn(
                f"tmp/ contém {len(tmp_files)} arquivo(s) além de .gitkeep",
                f"Verifique se estão no .gitignore: {names}",
            )
    else:
        warn("Pasta tmp/ não encontrada", "Crie com: mkdir tmp && touch tmp/.gitkeep")

    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        gi = gitignore_path.read_text(encoding="utf-8")
        check(".gitignore inclui tmp/*", "tmp/*" in gi, "Adicione 'tmp/*' e '!tmp/.gitkeep' ao .gitignore")
        check(".gitignore inclui logs/", "logs/" in gi, "Adicione 'logs/' ao .gitignore")
    else:
        check(".gitignore existe", False, "Crie um arquivo .gitignore na raiz do projeto")

    # ------------------------------------------------------------------
    # Resumo
    # ------------------------------------------------------------------
    print()
    print("=" * 62)
    total = PASS + FAIL + WARN
    print(f" Resultado: {PASS} OK | {FAIL} FALHA | {WARN} AVISO | {total} verificações")
    print("=" * 62)
    print()

    if FAIL > 0:
        print("Corrija as falhas acima antes de iniciar o ambiente.")
        return 1
    elif WARN > 0:
        print("Verifique os avisos para garantir execução correta.")
        return 0
    else:
        print("Tudo OK. Ambiente pronto para .\\run-local.ps1")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verificação de consistência do repositório Fito+ Amazônia AIMM"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Raiz do repositório (default: parent do diretório scripts/)",
    )
    args = parser.parse_args()
    sys.exit(main(args.root))
