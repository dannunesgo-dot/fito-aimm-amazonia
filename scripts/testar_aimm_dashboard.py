
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.aimm_dashboard import execute_aimm_dashboard

RELATORIO = Path("outputs/logs/teste_aimm_dashboard.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_aimm_dashboard()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Dashboard falhou com {len(result['errors'])} erro(s).")

    # Todas as saídas declaradas devem existir.
    outputs = result["outputs"]
    for chave, caminho in outputs.items():
        if not Path(caminho).exists():
            raise FileNotFoundError(f"Saída ausente: {chave} -> {caminho}")

    # A visão por eixo deve ter exatamente os dois eixos oficiais.
    eixos = read_csv(Path(outputs["axes"]))
    nomes = {e["eixo"] for e in eixos}
    esperados = {"Project Outcome", "Market Outcome"}
    if nomes != esperados:
        raise ValueError(f"Eixos incorretos: {nomes}. Esperado: {esperados}")

    # O score deve bater com a soma dos eixos (+ ajuste).
    soma = sum(int(e["pontos_ajustados"]) for e in eixos) + result["ajuste_clima_inclusao"]
    if soma != result["score_total"]:
        raise ValueError(
            f"Score inconsistente: eixos somam {soma}, mas score_total é {result['score_total']}"
        )

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "TESTE AIMM_DASHBOARD — Fito+ Amazônia",
        "=" * 86,
        "Dashboard religado ao motor oficial (fitomais_aimm_engine).",
        "",
        f"Score AIMM: {result['score_total']} ({result['faixa']})",
        f"  Project Outcome: {result['project']['rating']} / {result['project']['risco']} = {result['project']['pontos']} pontos",
        f"  Market Outcome:  {result['market']['rating']} / {result['market']['risco']} = {result['market']['pontos']} pontos",
        f"  Ajuste clima/inclusão: {result['ajuste_clima_inclusao']}",
        "",
        "Memória de cálculo:",
    ]
    linhas += [f"  - {m}" for m in result["memoria_calculo"]]
    linhas += [
        "",
        f"Status do resultado: {result['status']}",
        "",
        "Verificações estruturais:",
        "  [OK] Todas as saídas declaradas foram geradas.",
        "  [OK] Visão por eixo contém exatamente Project Outcome e Market Outcome.",
        "  [OK] Score total confere com a soma dos eixos.",
        "",
        "Resultado: SUCESSO.",
    ]
    if result["provisorio"]:
        linhas.append(
            "TRAVA: ratings PROVISÓRIOS de exemplo. O score NÃO é avaliação real. "
            "Os ratings reais virão do sector framework Fito+ (Camada 2)."
        )
    texto = "\n".join(linhas)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
