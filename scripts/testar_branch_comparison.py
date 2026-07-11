
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.branch_comparison import execute_branch_comparison

RELATORIO = Path("outputs/logs/teste_branch_comparison.txt")

# Branch usado para o teste automatizado. Pode ser sobrescrito por argumento.
BRANCH_TESTE = sys.argv[1] if len(sys.argv) > 1 else "refactor/phase2"


def main():
    result = execute_branch_comparison(BRANCH_TESTE, append_table=False)

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Comparação falhou com {len(result['errors'])} erro(s).")

    tabela = Path("docs/BRANCH_COMPARISON_TABLE.csv")
    if not tabela.exists():
        raise FileNotFoundError(f"Tabela de comparação não gerada: {tabela}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "TESTE BRANCH_COMPARISON — Fito+ Amazônia",
        "=" * 86,
        f"Branch comparado: {result['branch']} (commit {result['commit']})",
        f"Ahead: {result['ahead']}  Behind: {result['behind']}",
        f"Adicionados: {result['total_adicionados']}",
        f"Modificados: {result['total_modificados']}",
        f"Removidos: {result['total_removidos']}",
        f"Ruído isolado: {result['total_ruido']}",
        f"Impacto no núcleo: {result['impacto_nucleo']}",
    ]
    for nm in result["nucleo_modificado"]:
        linhas.append(f"  - núcleo modificado: {nm['arquivo']} ({nm['magnitude']})")
    linhas += [
        "",
        f"Módulos Python novos: {len(result['modulos_novos'])}",
        "",
        "Resultado: SUCESSO.",
        "Trava: o agente descreve o que muda; não decide merge nem avalia mérito.",
    ]
    texto = "\n".join(linhas)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
