from __future__ import annotations

import csv
from pathlib import Path


INPUT_COMPLETED = Path("data/manual/aimm_visual_review_checklist_completed.csv")
INPUT_TEMPLATE = Path("data/reference/aimm_visual_review_checklist_seed.csv")

OUT_STATUS = Path("data/processed/aimm_visual_review_final_status.csv")
OUT_REPORT = Path("data/processed/aimm_visual_review_acceptance_report.csv")
OUT_MD = Path("outputs/review/REVISAO_VISUAL_RESULTADO.md")
OUT_LOG = Path("outputs/logs/teste_aimm_visual_review_4_19_b.txt")

VALID_STATUS = {"ok", "ok_com_observacao", "pendente", "reprovado"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def normalize_status(value: str) -> str:
    return (value or "").strip().lower()


def main() -> None:
    if INPUT_COMPLETED.exists():
        rows = read_csv(INPUT_COMPLETED)
        origem = str(INPUT_COMPLETED)
        modo = "checklist_manual_encontrado"
    else:
        rows = read_csv(INPUT_TEMPLATE)
        origem = str(INPUT_TEMPLATE)
        modo = "sem_checklist_manual_usando_template_pendente"

    total = len(rows)

    pendentes = 0
    aprovados = 0
    aprovados_com_observacao = 0
    reprovados = 0
    invalidos = 0

    report_rows: list[dict[str, str]] = []

    for row in rows:
        status = normalize_status(row.get("status", ""))

        if status not in VALID_STATUS:
            invalidos += 1
            aceitacao = "status_invalido"
        elif status == "pendente":
            pendentes += 1
            aceitacao = "nao_aceito"
        elif status == "ok":
            aprovados += 1
            aceitacao = "aceito"
        elif status == "ok_com_observacao":
            aprovados_com_observacao += 1
            aceitacao = "aceito_com_observacao"
        elif status == "reprovado":
            reprovados += 1
            aceitacao = "nao_aceito"
        else:
            invalidos += 1
            aceitacao = "status_invalido"

        report_rows.append(
            {
                "id_revisao": row.get("id_revisao", ""),
                "grupo": row.get("grupo", ""),
                "arquivo": row.get("arquivo", ""),
                "criterio": row.get("criterio", ""),
                "checagem": row.get("checagem", ""),
                "status": status,
                "observacao_revisor": row.get("observacao_revisor", ""),
                "aceitacao": aceitacao,
            }
        )

    if invalidos:
        situacao = "erro_status_invalido"
    elif reprovados:
        situacao = "reprovado"
    elif pendentes:
        situacao = "pendente_revisao_humana"
    else:
        situacao = "revisao_visual_concluida"

    status_rows = [
        {
            "rodada": "4.19-B",
            "origem_checklist": origem,
            "modo": modo,
            "total_itens": str(total),
            "ok": str(aprovados),
            "ok_com_observacao": str(aprovados_com_observacao),
            "pendente": str(pendentes),
            "reprovado": str(reprovados),
            "status_invalido": str(invalidos),
            "situacao_final": situacao,
            "libera_score_aimm_final": "nao",
            "libera_decisao_executiva": "nao",
            "observacao": "Revisao visual e controle de aceitacao nao substituem validacao tecnica, regulatoria, orcamentaria ou executiva.",
        }
    ]

    write_csv(OUT_STATUS, status_rows)
    write_csv(OUT_REPORT, report_rows)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    md_lines = [
        "# Resultado da Revisão Visual Humana — Rodada 4.19-B",
        "",
        "## Síntese",
        "",
        f"- Origem do checklist: `{origem}`",
        f"- Modo: `{modo}`",
        f"- Total de itens: `{total}`",
        f"- OK: `{aprovados}`",
        f"- OK com observação: `{aprovados_com_observacao}`",
        f"- Pendentes: `{pendentes}`",
        f"- Reprovados: `{reprovados}`",
        f"- Status inválidos: `{invalidos}`",
        f"- Situação final: `{situacao}`",
        "",
        "## Interpretação",
        "",
    ]

    if situacao == "pendente_revisao_humana":
        md_lines.extend(
            [
                "A revisão visual humana ainda não foi concluída.",
                "",
                "Isto é esperado quando ainda não existe o arquivo manual `data/manual/aimm_visual_review_checklist_completed.csv`.",
            ]
        )
    elif situacao == "revisao_visual_concluida":
        md_lines.append("A revisão visual foi concluída sem pendências ou reprovações.")
    elif situacao == "reprovado":
        md_lines.append("Há pelo menos um item reprovado. O pacote não deve circular até correção.")
    elif situacao == "erro_status_invalido":
        md_lines.append("Há status inválido no checklist. Corrigir antes de usar o resultado.")

    md_lines.extend(
        [
            "",
            "## Trava",
            "",
            "A revisão visual não libera score AIMM final, orçamento, OSCs, espécies, produtos ou rotas regulatórias.",
        ]
    )

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log_lines = [
        "TESTE AIMM_VISUAL_REVIEW — Fito+ Amazônia",
        "=" * 86,
        f"Origem: {origem}",
        f"Modo: {modo}",
        f"Total de itens: {total}",
        f"OK: {aprovados}",
        f"OK com observação: {aprovados_com_observacao}",
        f"Pendentes: {pendentes}",
        f"Reprovados: {reprovados}",
        f"Status inválidos: {invalidos}",
        f"Situação final: {situacao}",
        "",
        "Resultado: SUCESSO.",
        "A validação da revisão visual humana foi processada estruturalmente.",
        "",
        "Trava: revisão visual não libera score AIMM final nem decisões executivas.",
    ]

    log_text = "\n".join(log_lines)
    OUT_LOG.write_text(log_text, encoding="utf-8")

    print(log_text)

    if invalidos:
        raise ValueError("Há status inválido no checklist de revisão visual.")


if __name__ == "__main__":
    main()
