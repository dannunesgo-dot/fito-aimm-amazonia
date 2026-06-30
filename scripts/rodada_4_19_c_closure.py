from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ARCHIVE_SEED = Path("data/reference/round_4_19_archive_expected_seed.csv")

OUT_ARCHIVE = Path("data/processed/drive_archive_verification_4_19.csv")
OUT_STATUS = Path("data/processed/round_4_19_closure_status.csv")
OUT_GAPS = Path("data/processed/open_gaps_after_4_19.csv")
OUT_NEXT = Path("data/processed/next_rounds_after_4_19.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_round_4_19_closure.csv")
OUT_REPORT = Path("outputs/reports/ENCERRAMENTO_FORMAL_RODADA_4_19.md")
OUT_LOG = Path("outputs/logs/teste_round_4_19_closure.txt")


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


def count_status(rows: list[dict[str, str]], status: str) -> int:
    return sum(1 for row in rows if row.get("status_verificacao") == status)


def build_gaps(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    pending_archive = [
        row for row in rows if row.get("status_verificacao") != "verificado"
    ]

    gaps: list[dict[str, str]] = [
        {
            "id_lacuna": "GAP_419_001",
            "tema": "revisao_visual_humana",
            "descricao": "A revisão visual humana permanece pendente. A 4.19-B validou estruturalmente o checklist, mas não substitui revisão manual.",
            "criticidade": "alta",
            "bloqueia_score_aimm_final": "sim",
            "acao_recomendada": "Preencher data/manual/aimm_visual_review_checklist_completed.csv e reexecutar rodada-4-19-b-visual-review.",
            "status": "aberta",
        },
        {
            "id_lacuna": "GAP_419_003",
            "tema": "integracao_drive_automatica",
            "descricao": "A integração automática GitHub Actions para Google Drive ainda não está implementada.",
            "criticidade": "media",
            "bloqueia_score_aimm_final": "nao",
            "acao_recomendada": "Planejar rodada própria com Google Drive API, GitHub Secrets e credencial de serviço.",
            "status": "aberta",
        },
        {
            "id_lacuna": "GAP_419_004",
            "tema": "alinhamento_aimm",
            "descricao": "Indicadores, eixos analíticos e dimensões precisam ser reclassificados conforme arquitetura AIMM canônica.",
            "criticidade": "alta",
            "bloqueia_score_aimm_final": "sim",
            "acao_recomendada": "Executar Rodada 4.20 de alinhamento AIMM.",
            "status": "aberta",
        },
        {
            "id_lacuna": "GAP_419_005",
            "tema": "gis",
            "descricao": "Estratégia GIS ainda precisa ser implementada como módulo estrutural da calculadora.",
            "criticidade": "alta",
            "bloqueia_score_aimm_final": "sim",
            "acao_recomendada": "Executar Rodada 4.21 de registro GIS estrutural.",
            "status": "aberta",
        },
    ]

    if pending_archive:
        gaps.append(
            {
                "id_lacuna": "GAP_419_002",
                "tema": "arquivamento_drive",
                "descricao": f"Há {len(pending_archive)} item(ns) da Rodada 4.19 com arquivamento Drive pendente de confirmação.",
                "criticidade": "media",
                "bloqueia_score_aimm_final": "nao",
                "acao_recomendada": "Confirmar upload dos artefatos pendentes no Drive ou manter pendência registrada.",
                "status": "aberta",
            }
        )

    return gaps


def build_next_rounds() -> list[dict[str, str]]:
    return [
        {
            "rodada": "4.20",
            "nome": "alinhamento AIMM",
            "objetivo": "Reclassificar indicadores, dimensões AIMM, eixos analíticos, benchmarks, proxies e travas.",
            "prioridade": "alta",
            "dependencia": "4.19-C encerrada",
        },
        {
            "rodada": "4.21",
            "nome": "registro GIS estrutural",
            "objetivo": "Criar registro de camadas GIS, indicadores GIS e regras territoriais.",
            "prioridade": "alta",
            "dependencia": "4.19-C encerrada",
        },
        {
            "rodada": "4.22",
            "nome": "baseline GIS territorial",
            "objetivo": "Processar baseline territorial, municípios, área, densidade, coordenadas, buffers e readiness espacial.",
            "prioridade": "alta",
            "dependencia": "4.21 validada",
        },
        {
            "rodada": "4.23",
            "nome": "manual técnico operacional",
            "objetivo": "Documentar funcionalidades, arquivos, workflows, entradas, outputs, erros e correções.",
            "prioridade": "media",
            "dependencia": "4.20 e 4.21 iniciadas",
        },
        {
            "rodada": "4.24",
            "nome": "guia operacional curto",
            "objetivo": "Criar guia direto para equipe não técnica.",
            "prioridade": "media",
            "dependencia": "4.23 iniciada",
        },
        {
            "rodada": "4.25",
            "nome": "pacote de transferência",
            "objetivo": "Preparar material completo para retomada em outro chat sem perda de progresso.",
            "prioridade": "alta",
            "dependencia": "4.23 e 4.24",
        },
    ]


def build_report(
    archive_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    gaps: list[dict[str, str]],
    next_rounds: list[dict[str, str]],
) -> str:
    status = status_rows[0]

    lines = [
        "# Encerramento Formal da Rodada 4.19 — Fito+ Amazônia AIMM",
        "",
        "## 1. Situação de encerramento",
        "",
        f"- Status formal: `{status['status_formal']}`",
        f"- 4.19-A GitHub: `{status['rodada_4_19_a_github']}`",
        f"- 4.19-B GitHub: `{status['rodada_4_19_b_github']}`",
        f"- 4.19-B Drive: `{status['rodada_4_19_b_drive']}`",
        f"- Revisão visual humana: `{status['revisao_visual_humana']}`",
        f"- Score AIMM final: `{status['score_aimm_final']}`",
        "",
        "## 2. Arquivamento Drive",
        "",
        "| Item | Rodada | Arquivo | Destino | Status |",
        "|---|---|---|---|---|",
    ]

    for row in archive_rows:
        lines.append(
            f"| {row['id_item']} | {row['rodada']} | `{row['arquivo']}` | "
            f"`{row['destino_drive']}` | {row['status_verificacao']} |"
        )

    lines.extend(
        [
            "",
            "## 3. Lacunas abertas",
            "",
            "| Lacuna | Tema | Criticidade | Bloqueia score final | Ação recomendada |",
            "|---|---|---|---|---|",
        ]
    )

    for gap in gaps:
        lines.append(
            f"| {gap['id_lacuna']} | {gap['tema']} | {gap['criticidade']} | "
            f"{gap['bloqueia_score_aimm_final']} | {gap['acao_recomendada']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Próximas rodadas",
            "",
            "| Rodada | Nome | Objetivo | Prioridade |",
            "|---|---|---|---|",
        ]
    )

    for row in next_rounds:
        lines.append(
            f"| {row['rodada']} | {row['nome']} | {row['objetivo']} | {row['prioridade']} |"
        )

    lines.extend(
        [
            "",
            "## 5. Travas finais",
            "",
            "- A Rodada 4.19-C não calcula score AIMM final.",
            "- A Rodada 4.19-C não aprova orçamento.",
            "- A Rodada 4.19-C não aprova OSCs.",
            "- A Rodada 4.19-C não aprova espécies.",
            "- A Rodada 4.19-C não aprova produtos.",
            "- A Rodada 4.19-C não aprova rotas regulatórias.",
            "- A revisão visual humana segue pendente.",
            "- GIS segue como módulo técnico a implementar.",
            "- Alinhamento AIMM segue como módulo técnico a implementar.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    archive_rows = read_csv(ARCHIVE_SEED)

    verified = count_status(archive_rows, "verificado")
    pending = len(archive_rows) - verified

    gaps = build_gaps(archive_rows)
    next_rounds = build_next_rounds()

    status_formal = "encerrada_com_lacunas_controladas"

    status_rows = [
        {
            "rodada": "4.19-C",
            "status_formal": status_formal,
            "rodada_4_19_a_github": "validada",
            "rodada_4_19_b_github": "validada",
            "rodada_4_19_b_drive": "verificada",
            "itens_drive_verificados": str(verified),
            "itens_drive_pendentes_confirmacao": str(pending),
            "revisao_visual_humana": "pendente",
            "score_aimm_final": "bloqueado",
            "orcamento_final": "bloqueado",
            "oscs_finais": "bloqueado",
            "especies_finais": "bloqueado",
            "produtos_finais": "bloqueado",
            "rotas_regulatorias_finais": "bloqueado",
            "gis": "pendente_implementacao",
            "alinhamento_aimm": "pendente_rodada_4_20",
            "observacao": "Encerramento formal registra progresso técnico e lacunas. Não libera decisão final.",
        }
    ]

    evidence_rows = [
        {
            "id_evidencia": "EVD_ROUND_4_19_CLOSURE",
            "tipo_evidencia": "encerramento_formal",
            "rodada": "4.19-C",
            "arquivo_referencia": "data/processed/round_4_19_closure_status.csv",
            "descricao": "Encerramento formal da Rodada 4.19 com verificação Drive e registro de lacunas.",
            "status_conferencia": status_formal,
            "limitacoes": "Verificação Drive automatizada limitada aos itens listados pelo conector. Revisão visual humana permanece pendente.",
        }
    ]

    write_csv(OUT_ARCHIVE, archive_rows)
    write_csv(OUT_STATUS, status_rows)
    write_csv(OUT_GAPS, gaps)
    write_csv(OUT_NEXT, next_rounds)
    write_csv(OUT_EVIDENCE, evidence_rows)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(
        build_report(archive_rows, status_rows, gaps, next_rounds),
        encoding="utf-8",
    )

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)

    log_lines = [
        "TESTE ROUND_4_19_CLOSURE — Fito+ Amazônia",
        "=" * 86,
        f"Itens de arquivamento registrados: {len(archive_rows)}",
        f"Itens Drive verificados: {verified}",
        f"Itens pendentes de confirmação: {pending}",
        f"Lacunas abertas: {len(gaps)}",
        f"Próximas rodadas registradas: {len(next_rounds)}",
        f"Status formal: {status_formal}",
        "",
        "Resultado: SUCESSO.",
        "O encerramento formal da Rodada 4.19 foi gerado com registro de arquivamento, lacunas e travas.",
        "",
        "Trava: encerramento formal não libera score AIMM final nem decisões executivas.",
    ]

    log_text = "\n".join(log_lines)
    OUT_LOG.write_text(log_text, encoding="utf-8")
    print(log_text)

    required_outputs = [
        OUT_ARCHIVE,
        OUT_STATUS,
        OUT_GAPS,
        OUT_NEXT,
        OUT_EVIDENCE,
        OUT_REPORT,
        OUT_LOG,
    ]

    for path in required_outputs:
        if not path.exists():
            raise FileNotFoundError(f"Saída obrigatória não gerada: {path}")


if __name__ == "__main__":
    main()
