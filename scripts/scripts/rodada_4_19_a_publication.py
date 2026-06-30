from __future__ import annotations

import csv
import json
import html
from pathlib import Path
from typing import Any


DRIVE_MAP_SEED = Path("data/reference/aimm_publication_drive_map_seed.csv")
REVIEW_SEED = Path("data/reference/aimm_visual_review_checklist_seed.csv")

OUT_DRIVE_MAP = Path("data/processed/aimm_drive_publication_map.csv")
OUT_CHECKLIST = Path("data/processed/aimm_visual_review_checklist.csv")
OUT_READINESS = Path("data/processed/aimm_publication_readiness_report.csv")
OUT_MANIFEST = Path("data/processed/aimm_publication_manifest.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_aimm_publication.csv")

OUT_README = Path("outputs/publication/README_PUBLICACAO_DRIVE.md")
OUT_REVIEW_MD = Path("outputs/publication/REVISAO_VISUAL_HUMANA.md")
OUT_INDEX_HTML = Path("outputs/publication/PACOTE_PUBLICACAO_INDEX.html")
OUT_UPLOAD_INSTRUCTIONS = Path("outputs/publication/drive_upload_instructions.md")
OUT_PAYLOAD = Path("outputs/publication/aimm_publication_payload.json")
OUT_LOG = Path("outputs/logs/teste_aimm_publication_4_19_a.txt")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def build_drive_map(seed_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in seed_rows:
        rows.append(
            {
                **row,
                "acao_usuario": "baixar artefato do GitHub Actions; extrair; enviar ao destino Drive indicado",
                "status_publicacao": "pendente_upload_drive",
            }
        )
    return rows


def build_readiness(drive_map: list[dict[str, str]], checklist: list[dict[str, str]]) -> list[dict[str, str]]:
    visual_required = sum(1 for row in drive_map if "revisao" in row["obrigatoriedade"])
    pending_review = sum(1 for row in checklist if row["status"] == "pendente")

    return [
        {
            "checagem": "mapa_drive",
            "status": "ok",
            "valor": str(len(drive_map)),
            "mensagem": "Mapa funcional de arquivamento Drive gerado.",
        },
        {
            "checagem": "checklist_revisao_visual",
            "status": "pendente_revisao_humana",
            "valor": str(len(checklist)),
            "mensagem": "Checklist de revisão visual gerado e pendente de preenchimento manual.",
        },
        {
            "checagem": "itens_revisao_visual_obrigatoria",
            "status": "pendente_revisao_humana",
            "valor": str(visual_required),
            "mensagem": "Arquivos visuais/editáveis exigem revisão humana antes de circulação.",
        },
        {
            "checagem": "pendencias_revisao",
            "status": "pendente",
            "valor": str(pending_review),
            "mensagem": "Pendências de revisão visual ainda não resolvidas.",
        },
        {
            "checagem": "trava_publicacao",
            "status": "trava",
            "valor": "nao_liberado_para_uso_externo",
            "mensagem": "Publicação no Drive não libera score AIMM final nem decisões executivas.",
        },
    ]


def build_readme(drive_map: list[dict[str, str]]) -> str:
    lines = [
        "# Fito+ Amazônia — Publicação no Google Drive",
        "",
        "## Finalidade",
        "",
        "Este pacote organiza os arquivos da Rodada 4.19-A para arquivamento no Google Drive e revisão visual humana.",
        "",
        "## Trava",
        "",
        "**Este pacote não libera score AIMM final, orçamento, OSCs, espécies, produtos ou rotas regulatórias.**",
        "",
        "## Procedimento",
        "",
        "1. Baixar o artefato `aimm-publication-fito-amazonia` no GitHub Actions.",
        "2. Extrair o ZIP no computador.",
        "3. Enviar cada arquivo ao destino Drive indicado.",
        "4. Preencher o checklist de revisão visual humana.",
        "5. Não circular externamente sem revisão concluída.",
        "",
        "## Mapa de arquivamento",
        "",
        "| Arquivo | Destino Drive | Obrigatoriedade |",
        "|---|---|---|",
    ]
    for row in drive_map:
        lines.append(f"| `{row['arquivo']}` | `{row['destino_drive']}` | {row['obrigatoriedade']} |")
    return "\n".join(lines)


def build_review_md(checklist: list[dict[str, str]]) -> str:
    lines = [
        "# Revisão Visual Humana — Fito+ Amazônia AIMM",
        "",
        "## Objetivo",
        "",
        "Confirmar se os arquivos visuais e comunicacionais estão legíveis, editáveis e sem ambiguidades antes de uso externo.",
        "",
        "## Trava",
        "",
        "**A revisão visual não aprova score AIMM final. Ela apenas verifica a qualidade comunicacional e operacional dos arquivos.**",
        "",
        "## Checklist",
        "",
        "| ID | Grupo | Arquivo | Critério | Checagem | Status | Observação |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(
            f"| {row['id_revisao']} | {row['grupo']} | `{row['arquivo']}` | "
            f"{row['criterio']} | {row['checagem']} | {row['status']} | {row.get('observacao_revisor', '')} |"
        )
    lines.extend(
        [
            "",
            "## Critério de encerramento",
            "",
            "A revisão visual só deve ser considerada concluída quando todos os itens estiverem como `ok` ou `ok_com_observacao`.",
        ]
    )
    return "\n".join(lines)


def build_upload_instructions(drive_map: list[dict[str, str]]) -> str:
    lines = [
        "# Instruções de upload para o Drive",
        "",
        "Use exatamente os destinos abaixo.",
        "",
    ]
    current = None
    for row in sorted(drive_map, key=lambda x: (x["destino_drive"], x["arquivo"])):
        if row["destino_drive"] != current:
            current = row["destino_drive"]
            lines.append(f"## {current}")
            lines.append("")
        lines.append(f"- `{row['arquivo']}` — {row['descricao']}")
    return "\n".join(lines)


def build_index_html(drive_map: list[dict[str, str]], checklist: list[dict[str, str]]) -> str:
    drive_rows = "\n".join(
        f"<tr><td>{html.escape(row['arquivo'])}</td><td>{html.escape(row['destino_drive'])}</td><td>{html.escape(row['obrigatoriedade'])}</td></tr>"
        for row in drive_map
    )
    review_rows = "\n".join(
        f"<tr><td>{html.escape(row['id_revisao'])}</td><td>{html.escape(row['arquivo'])}</td><td>{html.escape(row['criterio'])}</td><td>{html.escape(row['status'])}</td></tr>"
        for row in checklist
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Fito+ Amazônia — Pacote de Publicação</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; background: #ffffff; }}
h1 {{ font-size: 28px; }}
h2 {{ margin-top: 30px; border-bottom: 2px solid #111827; padding-bottom: 6px; }}
.warning {{ background: #fffbeb; border: 2px solid #92400e; padding: 14px; font-weight: bold; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
th, td {{ border: 1px solid #9ca3af; padding: 8px; text-align: left; }}
th {{ background: #e5e7eb; }}
</style>
</head>
<body>
<h1>Fito+ Amazônia — Pacote local/Drive de publicação</h1>
<div class="warning">TRAVA: pacote preliminar. Não libera score AIMM final nem aprova decisões executivas.</div>

<h2>Mapa de arquivamento Drive</h2>
<table>
<thead><tr><th>Arquivo</th><th>Destino Drive</th><th>Obrigatoriedade</th></tr></thead>
<tbody>{drive_rows}</tbody>
</table>

<h2>Checklist de revisão visual</h2>
<table>
<thead><tr><th>ID</th><th>Arquivo</th><th>Critério</th><th>Status</th></tr></thead>
<tbody>{review_rows}</tbody>
</table>

<h2>Readiness</h2>
<p>O pacote está pronto para arquivamento operacional, mas permanece pendente de revisão visual humana.</p>
</body>
</html>"""


def main() -> None:
    drive_seed = read_csv(DRIVE_MAP_SEED)
    review_seed = read_csv(REVIEW_SEED)

    drive_map = build_drive_map(drive_seed)
    checklist = [dict(row) for row in review_seed]
    readiness = build_readiness(drive_map, checklist)

    write_csv(OUT_DRIVE_MAP, drive_map)
    write_csv(OUT_CHECKLIST, checklist)
    write_csv(OUT_READINESS, readiness)

    OUT_README.parent.mkdir(parents=True, exist_ok=True)
    OUT_README.write_text(build_readme(drive_map), encoding="utf-8")
    OUT_REVIEW_MD.write_text(build_review_md(checklist), encoding="utf-8")
    OUT_UPLOAD_INSTRUCTIONS.write_text(build_upload_instructions(drive_map), encoding="utf-8")
    OUT_INDEX_HTML.write_text(build_index_html(drive_map, checklist), encoding="utf-8")

    payload = {
        "rodada": "4.19-A",
        "drive_map": drive_map,
        "visual_review_checklist": checklist,
        "readiness": readiness,
        "trava": "Publicação e revisão visual não liberam score AIMM final.",
    }
    OUT_PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_PUBLICATION_4_19_A",
            "tipo_evidencia": "pacote_drive_revisao_visual",
            "periodo_referencia": "Rodada 4.19-A",
            "territorio": "Fito+ Amazônia",
            "valor_extraido": str(len(drive_map)),
            "unidade": "arquivos mapeados",
            "status_conferencia": "pendente_upload_drive_e_revisao_visual_humana",
            "limitacoes": "Arquivamento no Drive é externo ao GitHub Actions; revisão visual deve ser feita manualmente.",
        }
    ]
    write_csv(OUT_EVIDENCE, evidence)

    outputs = {
        "drive_publication_map": OUT_DRIVE_MAP,
        "visual_review_checklist": OUT_CHECKLIST,
        "publication_readiness_report": OUT_READINESS,
        "readme_publicacao_drive": OUT_README,
        "revisao_visual_humana": OUT_REVIEW_MD,
        "pacote_publicacao_index": OUT_INDEX_HTML,
        "drive_upload_instructions": OUT_UPLOAD_INSTRUCTIONS,
        "publication_payload": OUT_PAYLOAD,
        "evidence": OUT_EVIDENCE,
        "publication_manifest": OUT_MANIFEST,
    }

    manifest = [
        {
            "id_arquivo": key,
            "arquivo": str(path),
            "existe": "sim" if path.exists() else "não",
            "uso": "pacote local/Drive de publicação e revisão visual humana",
        }
        for key, path in outputs.items()
    ]
    write_csv(OUT_MANIFEST, manifest)

    for path in outputs.values():
        if not path.exists():
            raise FileNotFoundError(f"Saída ausente: {path}")

    if not all(row["status"] == "pendente" for row in checklist):
        raise ValueError("Checklist deve iniciar como pendente.")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    log = "\n".join(
        [
            "TESTE AIMM_PUBLICATION — Fito+ Amazônia",
            "=" * 86,
            f"Itens mapeados para Drive: {len(drive_map)}",
            f"Itens de revisão visual humana: {len(checklist)}",
            f"Pendências iniciais de revisão: {sum(1 for row in checklist if row['status'] == 'pendente')}",
            "",
            "Resultado: SUCESSO.",
            "O pacote local/Drive de publicação e revisão visual humana foi gerado e validado estruturalmente.",
            "",
            "Trava: publicação no Drive e revisão visual não liberam score AIMM final nem decisões executivas.",
        ]
    )
    OUT_LOG.write_text(log, encoding="utf-8")
    print(log)


if __name__ == "__main__":
    main()
