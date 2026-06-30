# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_28_ingestao_arquivos")
MANIFEST = Path("data/manual/aimm_file_ingestion_manifest_seed.csv")

FILES = {
    "template": BASE / "TEMPLATE_MANIFESTO_INGESTAO_ARQUIVOS_AIMM_4_28.csv",
    "inventario": BASE / "INVENTARIO_ARQUIVOS_REPOSITORIO_AIMM_4_28.csv",
    "validacao": BASE / "VALIDACAO_INGESTAO_ARQUIVOS_AIMM_4_28.csv",
    "rotas": BASE / "ROTAS_DESTINO_ARQUIVOS_AIMM_4_28.csv",
    "regras": BASE / "REGRAS_INGESTAO_ARQUIVOS_AIMM_4_28.csv",
    "registry": Path("data/processed/aimm/aimm_file_ingestion_registry_4_28.csv"),
    "status": Path("data/processed/aimm/aimm_file_ingestion_status_4_28.csv"),
    "evidence": Path("data/evidence/evidence_aimm_file_ingestion_4_28.csv"),
    "report": Path("outputs/reports/RELATORIO_INGESTAO_ARQUIVOS_AIMM_4_28.md"),
    "log": Path("outputs/logs/teste_aimm_ingestao_arquivos_4_28.txt"),
}

ALLOWED_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".xlsx",
    ".xls",
    ".ods",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".gpkg",
    ".geojson",
    ".shp",
    ".dbf",
    ".shx",
    ".prj",
    ".qgz",
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".zip",
}

BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".msi",
    ".dll",
    ".scr",
    ".ps1",
    ".vbs",
}

ALLOWED_CATEGORIES = {
    "gis",
    "benchmark",
    "orcamento",
    "evidencia",
    "manual",
    "raw",
    "reference",
    "processed",
    "report",
    "log",
    "dashboard",
    "handoff",
    "outro_controlado",
}

ROUTES = [
    {
        "categoria": "gis",
        "destino_github": "data/raw/gis ou outputs/gis",
        "destino_drive": "09_gis",
        "observacao": "GeoPackage, QGZ, prints, tabelas relacionais e validações QGIS.",
    },
    {
        "categoria": "benchmark",
        "destino_github": "data/reference ou data/processed/benchmarks",
        "destino_drive": "04_outputs ou 02_evidencias",
        "observacao": "Fontes, proxies, matrizes e resultados normalizados.",
    },
    {
        "categoria": "orcamento",
        "destino_github": "data/manual ou data/processed/aimm",
        "destino_drive": "04_outputs",
        "observacao": "Componentes, pressupostos de custo, fases e validações.",
    },
    {
        "categoria": "evidencia",
        "destino_github": "data/evidence",
        "destino_drive": "02_evidencias",
        "observacao": "Arquivos de evidência e rastreabilidade.",
    },
    {
        "categoria": "manual",
        "destino_github": "outputs/aimm ou outputs/reports",
        "destino_drive": "04_outputs",
        "observacao": "Manuais operacionais, guias e documentos compartilháveis.",
    },
    {
        "categoria": "log",
        "destino_github": "outputs/logs",
        "destino_drive": "05_logs",
        "observacao": "Logs de execução e prints de validação.",
    },
    {
        "categoria": "raw",
        "destino_github": "data/raw",
        "destino_drive": "01_insumos_brutos",
        "observacao": "Arquivos originais controlados.",
    },
    {
        "categoria": "reference",
        "destino_github": "data/reference",
        "destino_drive": "00_configuracao ou 01_insumos_brutos",
        "observacao": "Seeds, listas, mapas e tabelas de referência.",
    },
]

RULES = [
    {
        "regra": "extensao_permitida",
        "criterio": "arquivo deve ter extensao permitida",
        "bloqueia": "sim",
    },
    {
        "regra": "extensao_bloqueada",
        "criterio": "executaveis e scripts de risco nao entram como insumo",
        "bloqueia": "sim",
    },
    {
        "regra": "categoria_valida",
        "criterio": "categoria deve estar na lista controlada",
        "bloqueia": "sim",
    },
    {
        "regra": "arquivo_obrigatorio_existente",
        "criterio": "arquivo marcado como obrigatorio deve existir no repositorio",
        "bloqueia": "sim",
    },
    {
        "regra": "nome_sem_espaco",
        "criterio": "preferir nomes sem espacos; usar underscore",
        "bloqueia": "nao",
    },
    {
        "regra": "drive_manual",
        "criterio": "arquivamento no Drive continua manual ate API real",
        "bloqueia": "nao",
    },
    {
        "regra": "sem_score_final",
        "criterio": "ingestao nao libera score AIMM final",
        "bloqueia": "sim",
    },
]


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Nenhuma linha para gravar em {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    normalized = []
    for row in rows:
        normalized.append({key: row.get(key, "") for key in fieldnames})

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        file.seek(0)
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(file, delimiter=delimiter)
        return [dict(row) for row in reader]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def build_template() -> list[dict[str, str]]:
    return [
        {
            "id_arquivo": "EXEMPLO_001",
            "caminho_github": "data/raw/gis/municipio_manaus_1302603.gpkg",
            "nome_arquivo": "municipio_manaus_1302603.gpkg",
            "categoria": "gis",
            "obrigatorio": "nao",
            "origem": "Drive manual / IBGE / QGIS",
            "destino_drive": "09_gis/01_insumos_brutos",
            "status_esperado": "validar_existencia_extensao_categoria",
            "observacao": "Exemplo de GeoPackage municipal.",
        },
        {
            "id_arquivo": "EXEMPLO_002",
            "caminho_github": "data/reference/benchmark_proxy_seed.csv",
            "nome_arquivo": "benchmark_proxy_seed.csv",
            "categoria": "benchmark",
            "obrigatorio": "nao",
            "origem": "fonte tecnica controlada",
            "destino_drive": "04_outputs",
            "status_esperado": "validar_existencia_extensao_categoria",
            "observacao": "Exemplo de seed de benchmark.",
        },
        {
            "id_arquivo": "EXEMPLO_003",
            "caminho_github": "outputs/reports/RELATORIO_EXEMPLO.md",
            "nome_arquivo": "RELATORIO_EXEMPLO.md",
            "categoria": "report",
            "obrigatorio": "nao",
            "origem": "workflow AIMM",
            "destino_drive": "04_outputs",
            "status_esperado": "validar_existencia_extensao_categoria",
            "observacao": "Exemplo de relatório.",
        },
    ]


def inventory_repository() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ignored_parts = {".git", "__pycache__", ".pytest_cache"}

    for path in sorted(Path(".").rglob("*")):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue

        suffix = path.suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS and suffix not in BLOCKED_EXTENSIONS:
            continue

        rows.append(
            {
                "caminho": str(path).replace("\\", "/").lstrip("./"),
                "nome_arquivo": path.name,
                "extensao": suffix,
                "tamanho_bytes": str(file_size(path)),
                "sha256": sha256_file(path),
                "tipo": "bloqueado" if suffix in BLOCKED_EXTENSIONS else "permitido",
            }
        )

    return rows


def validate_manifest_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int, int]:
    validation: list[dict[str, str]] = []
    errors = 0
    warnings = 0

    for idx, row in enumerate(rows, start=1):
        file_id = row.get("id_arquivo", f"LINHA_{idx}")
        path_text = row.get("caminho_github", "").strip()
        categoria = row.get("categoria", "").strip()
        obrigatorio = row.get("obrigatorio", "").strip().lower()
        path = Path(path_text) if path_text else Path("__caminho_vazio__")
        suffix = path.suffix.lower()

        issues: list[str] = []
        status = "ok"

        if not path_text:
            issues.append("caminho_github_vazio")
            status = "erro"
            errors += 1

        if categoria not in ALLOWED_CATEGORIES:
            issues.append("categoria_invalida")
            status = "erro"
            errors += 1

        if suffix in BLOCKED_EXTENSIONS:
            issues.append("extensao_bloqueada")
            status = "erro"
            errors += 1

        if suffix not in ALLOWED_EXTENSIONS and suffix not in BLOCKED_EXTENSIONS:
            issues.append("extensao_nao_catalogada")
            status = "alerta" if status == "ok" else status
            warnings += 1

        exists = path.exists()
        if obrigatorio == "sim" and not exists:
            issues.append("arquivo_obrigatorio_ausente")
            status = "erro"
            errors += 1

        if " " in path_text:
            issues.append("nome_ou_caminho_com_espaco")
            status = "alerta" if status == "ok" else status
            warnings += 1

        validation.append(
            {
                "id_arquivo": file_id,
                "caminho_github": path_text,
                "categoria": categoria,
                "obrigatorio": obrigatorio,
                "existe_no_repositorio": "sim" if exists else "nao",
                "extensao": suffix,
                "status_validacao": status,
                "issues": "|".join(issues) if issues else "sem_issue",
                "tamanho_bytes": str(file_size(path)) if exists else "0",
                "sha256": sha256_file(path) if exists else "",
            }
        )

    return validation, errors, warnings


def main() -> None:
    template_rows = build_template()
    write_csv(FILES["template"], template_rows)

    if MANIFEST.exists():
        manifest_rows = read_csv(MANIFEST)
        manifest_mode = "manifesto_manual_detectado"
    else:
        manifest_rows = template_rows
        manifest_mode = "template_usado_por_manifesto_manual_ausente"

    inventory = inventory_repository()
    validation, errors, warnings = validate_manifest_rows(manifest_rows)

    registry = [
        {
            "rodada": "4.28",
            "pacote": "modulo_ingestao_validacao_arquivos",
            "manifesto_origem": str(MANIFEST),
            "modo_manifesto": manifest_mode,
            "itens_manifesto": str(len(manifest_rows)),
            "arquivos_inventariados": str(len(inventory)),
            "itens_validados": str(len(validation)),
            "alertas": str(warnings),
            "erros_estruturais": str(errors),
            "api_drive_github": "nao_implementada",
            "score_aimm_final": "nao_liberado",
            "status": "gerado" if errors == 0 else "gerado_com_erros",
        }
    ]

    status = [
        {
            "rodada": "4.28",
            "status": "sucesso" if errors == 0 else "erro",
            "erros_estruturais": str(errors),
            "alertas": str(warnings),
            "manifesto_manual_detectado": "sim" if MANIFEST.exists() else "nao",
            "ingestao_funcional": "sim",
            "processamento_conteudo": "nao",
            "api_drive_github": "nao_implementada",
            "score_aimm_final": "nao_liberado",
            "proxima_rodada": "4.29",
            "proxima_rodada_descricao": "modulo de benchmarks, fontes, extracao e normalizacao",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_FILE_INGESTION_4_28",
            "tipo_evidencia": "modulo_ingestao_arquivos",
            "descricao": "Modulo funcional inicial de ingestao e validacao de arquivos por manifesto.",
            "status": "gerado",
            "limitacao": "Nao acessa Drive por API e nao processa conteudo dos arquivos.",
        }
    ]

    report = [
        "# Relatório da Rodada 4.28 — módulo de ingestão e validação de arquivos",
        "",
        "## Resultado",
        "",
        "A rodada criou o módulo funcional inicial de ingestão controlada de arquivos.",
        "",
        "## O que funciona",
        "",
        "- Geração de template de manifesto.",
        "- Leitura de manifesto manual quando existir.",
        "- Inventário de arquivos versionados no repositório.",
        "- Validação de extensão, categoria, obrigatoriedade e existência.",
        "- Registro de rotas de destino GitHub/Drive.",
        "",
        "## O que ainda não faz",
        "",
        "- Não acessa Google Drive por API.",
        "- Não faz upload ou download automático.",
        "- Não extrai conteúdo dos arquivos.",
        "- Não calcula score AIMM final.",
        "",
        "## Status",
        "",
        f"- Modo do manifesto: `{manifest_mode}`",
        f"- Itens no manifesto: `{len(manifest_rows)}`",
        f"- Arquivos inventariados: `{len(inventory)}`",
        f"- Alertas: `{warnings}`",
        f"- Erros estruturais: `{errors}`",
        "",
        "## Próxima rodada",
        "",
        "Rodada 4.29 — módulo de benchmarks, fontes, extração e normalização.",
    ]

    log = [
        "TESTE AIMM_FILE_INGESTION_4_28 — Fito+ Amazônia",
        "=" * 86,
        f"Modo do manifesto: {manifest_mode}",
        f"Arquivo manifesto esperado: {MANIFEST}",
        f"Itens no manifesto: {len(manifest_rows)}",
        f"Arquivos inventariados no repositório: {len(inventory)}",
        f"Itens validados: {len(validation)}",
        f"Alertas: {warnings}",
        f"Erros estruturais: {errors}",
        "API GitHub-Drive ativa: nao",
        "Upload automatico Drive: nao",
        "Download automatico Drive: nao",
        "Ingestao funcional por manifesto: sim",
        "Processamento de conteudo dos arquivos: nao",
        "Score AIMM final liberado: nao",
        "",
        "Resultado: SUCESSO." if errors == 0 else "Resultado: ERRO.",
        "Modulo de ingestao e validacao de arquivos gerado.",
        "",
        "Trava: nao acessa Drive por API, nao processa conteudo e nao libera score AIMM final.",
    ]

    write_csv(FILES["inventario"], inventory if inventory else [{"status": "nenhum_arquivo_inventariado"}])
    write_csv(FILES["validacao"], validation if validation else [{"status": "nenhum_item_validado"}])
    write_csv(FILES["rotas"], ROUTES)
    write_csv(FILES["regras"], RULES)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["status"], status)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log))

    if errors:
        raise ValueError(f"Rodada 4.28 contém {errors} erro(s) estrutural(is).")


if __name__ == "__main__":
    main()
