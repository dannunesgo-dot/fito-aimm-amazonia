
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.architecture_analysis import execute_architecture_analysis

RELATORIO = Path("outputs/logs/teste_architecture_analysis.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_architecture_analysis()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Análise de arquitetura falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        if not Path(path).exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")

    if not read_csv(Path(outputs["api_table"])):
        raise ValueError("Tabela de APIs vazia.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "TESTE ARCHITECTURE_ANALYSIS — Fito+ Amazônia",
        "=" * 86,
        f"Módulos de negócio analisados: {result['total_modulos']}",
        f"APIs externas consumidas: {result['total_apis_externas']}",
        f"Endpoints Flask internos: {result['total_endpoints']}",
        f"Arestas de dependência entre módulos: {result['total_arestas']}",
        f"Dependências de stack: {len(result['stack'])}",
        f"Portas Caddy: {', '.join(result['portas_caddy'])}",
        f"Variáveis de ambiente (.env.example): {', '.join(result['env_vars'])}",
        "",
        "Arquivos gerados:",
        f"- {outputs['api_table']}",
        f"- {outputs['dependency_graph']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "Trava: eixos Objetivo e Funcionalidades exigem leitura interpretativa (no relatório); estado de APIs externas requer verificação com rede.",
    ]
    texto = "\n".join(linhas)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
