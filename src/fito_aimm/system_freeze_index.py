
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


SEED_ARTIFACTS = Path("data/reference/master_artifact_index_seed.csv")
SEED_ROUNDS = Path("data/reference/round_status_seed.csv")
SEED_DRIVE = Path("data/reference/drive_archive_manifest_seed.csv")
SEED_GITHUB = Path("data/reference/github_repository_map_seed.csv")
SEED_GAPS = Path("data/reference/operational_gaps_register_seed.csv")
RULES = Path("config/system_freeze_rules.yaml")

OUT_ARTIFACTS = Path("data/processed/master_artifact_index.csv")
OUT_ROUNDS = Path("data/processed/round_status.csv")
OUT_DRIVE = Path("data/processed/drive_archive_manifest.csv")
OUT_GITHUB = Path("data/processed/github_repository_map.csv")
OUT_GAPS = Path("data/processed/operational_gaps_register.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_system_freeze_index.csv")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def file_status(row: dict[str, str]) -> str:
    github_path = row.get("github_path", "").strip()
    manter = row.get("manter_github", "").strip().lower()

    if not github_path:
        return "não_aplicável_artefato_externo"
    if Path(github_path).exists():
        return "presente_no_repositorio"
    if manter in {"não", "nao"}:
        return "ausente_permitido_nao_versionar"
    if manter == "opcional":
        return "ausente_permitido_artefato_drive_ou_actions"
    return "ausente_revisar"


def validate_unique(rows: list[dict[str, str]], field: str, label: str) -> list[str]:
    seen: dict[str, int] = {}
    errors = []
    for i, row in enumerate(rows, start=2):
        key = row.get(field, "").strip()
        if not key:
            errors.append(f"{label}: linha {i} sem {field}")
        elif key in seen:
            errors.append(f"{label}: {field} duplicado: {key}")
        else:
            seen[key] = i
    return errors


def execute_system_freeze_index() -> dict[str, Any]:
    cfg = load_yaml(RULES)
    artifacts = read_csv(SEED_ARTIFACTS)
    rounds = read_csv(SEED_ROUNDS)
    drive = read_csv(SEED_DRIVE)
    github = read_csv(SEED_GITHUB)
    gaps = read_csv(SEED_GAPS)

    errors = []
    errors.extend(validate_unique(artifacts, "artifact_id", "master_artifact_index"))
    errors.extend(validate_unique(gaps, "id_lacuna", "operational_gaps_register"))

    valid_drive = set(cfg.get("pastas_drive_validas", []))
    valid_status = set(cfg.get("status_rodada_validos", []))

    for i, row in enumerate(rounds, start=2):
        if row.get("status") not in valid_status:
            errors.append(f"round_status linha {i}: status inválido: {row.get('status')}")

    for i, row in enumerate(drive, start=2):
        if row.get("destino_drive_exato") not in valid_drive:
            errors.append(f"drive_archive_manifest linha {i}: pasta Drive inválida: {row.get('destino_drive_exato')}")

    # Enriquecer índice mestre com status de presença no repositório.
    artifacts_out = []
    for row in artifacts:
        out = dict(row)
        out["status_repositorio"] = file_status(row)
        out["acao_recomendada"] = (
            "arquivar_no_drive" if out["tipo"] == "zip_workflow"
            else "manter_indice_e_arquivar_conforme_manifesto"
        )
        artifacts_out.append(out)

    # Copiar e normalizar demais registros.
    write_csv(OUT_ARTIFACTS, artifacts_out)
    write_csv(OUT_ROUNDS, rounds)
    write_csv(OUT_DRIVE, drive)
    write_csv(OUT_GITHUB, github)
    write_csv(OUT_GAPS, gaps)

    # Evidência sintética.
    total_validated_rounds = sum(1 for r in rounds if r.get("status") in {"validada", "validada_com_lacuna"})
    total_gaps = len(gaps)
    total_artifacts = len(artifacts_out)
    total_missing_review = sum(1 for r in artifacts_out if r.get("status_repositorio") == "ausente_revisar")

    evidence = [{
        "id_evidencia": "EVD_SYSTEM_FREEZE_INDEX_4_10",
        "id_fonte": "SYSTEM_FREEZE_INDEX",
        "id_indicador": "MON_02; RISK_OSC_01; SYS_01",
        "tipo_evidencia": "congelamento_tecnico",
        "pergunta_ou_lacuna": "O sistema possui índice mestre, status de rodadas, manifesto Drive/GitHub e lacunas operacionais consolidadas?",
        "url_ou_arquivo": "data/processed/master_artifact_index.csv; data/processed/round_status.csv; data/processed/drive_archive_manifest.csv",
        "titulo_documento": "Congelamento técnico e índice mestre — Rodada 4.10",
        "pagina_tabela_secao": "índice mestre, status de rodadas, manifesto de arquivamento e lacunas",
        "trecho_original_ou_descricao": f"Artefatos indexados: {total_artifacts}; rodadas validadas/validadas com lacuna: {total_validated_rounds}; lacunas ativas: {total_gaps}; itens ausentes a revisar no GitHub: {total_missing_review}.",
        "resumo_ptbr": "Evidência de organização do sistema antes da arquitetura da calculadora AIMM.",
        "valor_extraido": str(total_artifacts),
        "unidade": "artefatos indexados",
        "periodo_referencia": "pós-Rodada 4.9-A",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "consolidação automatizada a partir de registros seed e verificação de presença no repositório",
        "nivel_confianca": "alto_para_estrutura; dependente_de_arquivamento_manual_no_drive",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_arquivamento_drive",
        "limitacoes": "Não verifica se o arquivo foi efetivamente enviado ao Google Drive; apenas define destino e regra.",
        "uso_na_calculadora": "Base de governança, rastreabilidade e retomada do sistema AIMM.",
        "status_evidencia": "pendente",
    }]
    write_csv(OUT_EVIDENCE, evidence)

    return {
        "errors": errors,
        "total_artifacts": total_artifacts,
        "total_rounds": len(rounds),
        "total_validated_rounds": total_validated_rounds,
        "total_gaps": total_gaps,
        "total_drive_items": len(drive),
        "total_github_map": len(github),
        "total_missing_review": total_missing_review,
        "outputs": {
            "master_artifact_index": str(OUT_ARTIFACTS),
            "round_status": str(OUT_ROUNDS),
            "drive_archive_manifest": str(OUT_DRIVE),
            "github_repository_map": str(OUT_GITHUB),
            "operational_gaps_register": str(OUT_GAPS),
            "evidence": str(OUT_EVIDENCE),
        },
    }
