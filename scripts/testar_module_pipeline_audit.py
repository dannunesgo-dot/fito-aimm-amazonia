
from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.module_pipeline_audit import execute_module_pipeline_audit

RELATORIO = Path("outputs/logs/teste_module_pipeline_audit.txt")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    result = execute_module_pipeline_audit()

    if result["errors"]:
        for err in result["errors"]:
            print(f"ERRO: {err}")
        raise ValueError(f"Auditoria de módulo/pipeline falhou com {len(result['errors'])} erro(s).")

    outputs = result["outputs"]
    for key, path in outputs.items():
        if not Path(path).exists():
            raise FileNotFoundError(f"Saída ausente: {key} -> {path}")

    # Inventário e tabela de evidência não podem estar vazios.
    if not read_csv(Path(outputs["module_pipeline_inventory"])):
        raise ValueError("Inventário de módulos vazio.")
    if not read_csv(Path(outputs["evidence_table"])):
        raise ValueError("Tabela de evidência vazia.")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "TESTE MODULE_PIPELINE_AUDIT — Fito+ Amazônia",
        "=" * 86,
        f"Módulos de negócio auditados: {result['total_negocio']}",
        f"Completos (IMPLEMENTADO): {result['total_implementado']}",
        f"Parciais (PARCIAL): {result['total_parcial']}",
        f"Conflitantes (CONFLITANTE): {result['total_conflitante']}",
        f"Saídas não publicadas por workflow: {result['total_unpublished_outputs']}",
        "",
        "Arquivos gerados:",
        f"- {outputs['module_pipeline_inventory']}",
        f"- {outputs['evidence_table']}",
        f"- {outputs['unpublished_outputs']}",
        f"- {outputs['evidence']}",
        "",
        "Resultado: SUCESSO.",
        "Trava: a auditoria não executa os módulos nem valida a correção dos cálculos; audita estrutura, declaração e publicação.",
    ]
    texto = "\n".join(linhas)
    RELATORIO.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
