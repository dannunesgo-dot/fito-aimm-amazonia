from pathlib import Path
import csv

arquivos = [
    Path("data/reference/source_registry.csv"),
    Path("data/evidence/evidence_registry.csv"),
]

for arquivo in arquivos:
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo ausente: {arquivo}")
    with arquivo.open(encoding="utf-8-sig") as f:
        leitor = csv.reader(f, delimiter=";")
        cabecalho = next(leitor)
        linhas = list(leitor)
    print(f"{arquivo}: {len(linhas)} linhas, {len(cabecalho)} colunas")

print("Validação inicial concluída.")
