
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.benchmark_proxy import execute_benchmark_proxy

RELATORIO = Path("outputs/logs/teste_benchmark_proxy.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_benchmark_proxy()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Benchmark/proxy falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")
        rows = read_csv(p)
        if not rows:
            raise ValueError(f"Saída vazia: {key} -> {path}")

    readiness = read_csv(Path(outputs["benchmark_readiness_matrix"]))
    if not any(row["status_prontidao"] == "bloqueado" for row in readiness):
        raise ValueError("A matriz deveria conter benchmarks bloqueados para IFC interno não público.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TESTE BENCHMARK_PROXY — Fito+ Amazônia",
        "=" * 86,
        f"Benchmarks/proxies registrados: {result['total_benchmarks']}",
        f"Métodos proxy registrados: {result['total_methods']}",
        f"Lacunas de benchmark registradas: {result['total_gaps']}",
        f"Fontes registradas: {result['total_sources']}",
        f"Dimensões AIMM mapeadas: {result['total_dimensions']}",
        f"Benchmarks/proxies bloqueados: {result['blocked']}",
        f"Benchmarks/proxies de baixa confiança: {result['low_confidence']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['benchmark_registry']}",
        f"- {outputs['proxy_method_registry']}",
        f"- {outputs['benchmark_gap_report']}",
        f"- {outputs['aimm_dimension_benchmark_map']}",
        f"- {outputs['source_registry_benchmark']}",
        f"- {outputs['benchmark_readiness_matrix']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "O registro de benchmarks, proxies e lacunas AIMM foi gerado e validado estruturalmente.",
        "",
        "Trava: benchmarks IFC internos não públicos permanecem bloqueados. Proxies são substitutos metodológicos temporários e não calculam score final.",
    ]
    text = "\n".join(lines)
    RELATORIO.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
