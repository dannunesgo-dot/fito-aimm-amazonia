
from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.fitomais_aimm_engine import calcular_por_texto

RELATORIO = Path("outputs/logs/teste_fitomais_aimm_engine.txt")

# Casos de teste derivados da mecânica oficial (Tabela 6 da AIMM Guidance Note).
# Formato: (project_rating, project_risco, market_rating, market_risco,
#           clima_inclusao, score_esperado, faixa_esperada, descricao)
CASOS = [
    ("Strong", "Unqualified", "Strong", "Qualified", False, 52, "Good",
     "Exemplo oficial da nota IFC (30 + 22 = 52)"),
    ("Very Strong", "Unqualified", "Very Strong", "Unqualified", False, 100, "Excellent",
     "Máximo possível (50 + 50)"),
    ("Marginal", "Qualified", "Marginal", "Qualified", False, 8, "Low",
     "Mínimo possível (4 + 4)"),
    ("Strong", "Unqualified", "Moderate", "Unqualified", False, 42, "Satisfactory",
     "Fronteira Satisfactory (30 + 12)"),
    ("Very Strong", "Qualified", "Strong", "Unqualified", False, 68, "Good",
     "Very Strong com risco (38 + 30)"),
    ("Moderate", "Unqualified", "Moderate", "Qualified", False, 20, "Low",
     "Dois moderados, um com risco (12 + 8)"),
    # Caso adicional: ajuste de clima/inclusão (+10).
    ("Strong", "Unqualified", "Strong", "Qualified", True, 62, "Good",
     "Exemplo oficial + ajuste clima/inclusão (52 + 10)"),
]


def main():
    falhas = []
    linhas_ok = []

    for pr, prk, mr, mrk, clima, esperado, faixa_esp, desc in CASOS:
        r = calcular_por_texto(pr, prk, mr, mrk, clima)
        ok_score = r.score_total == esperado
        ok_faixa = r.faixa == faixa_esp
        if ok_score and ok_faixa:
            linhas_ok.append(f"  [OK] {desc}: {r.score_total} ({r.faixa})")
        else:
            falhas.append(
                f"  [FALHA] {desc}: obtido {r.score_total} ({r.faixa}), "
                f"esperado {esperado} ({faixa_esp})"
            )

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    cabecalho = [
        "TESTE FITOMAIS_AIMM_ENGINE — Fito+ Amazônia",
        "=" * 86,
        "Valida a mecânica oficial do AIMM (IFC Guidance Note, março 2026)",
        f"Casos testados: {len(CASOS)}",
        f"Aprovados: {len(linhas_ok)} | Falhas: {len(falhas)}",
        "",
    ]
    corpo = linhas_ok + (["", "FALHAS:"] + falhas if falhas else [])
    rodape = [
        "",
        "Resultado: " + ("SUCESSO — motor conforme a norma IFC." if not falhas else "FALHA — motor diverge da norma."),
        "Trava: o motor calcula o score a partir de ratings; não deriva os ratings (isso é o sector framework Fito+).",
    ]
    texto = "\n".join(cabecalho + corpo + rodape)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)

    if falhas:
        raise ValueError(f"{len(falhas)} caso(s) de teste falharam. O motor NÃO está conforme a norma.")


if __name__ == "__main__":
    main()
