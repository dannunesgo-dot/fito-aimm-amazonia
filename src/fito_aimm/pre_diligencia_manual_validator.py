
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import yaml


BASE_STATUS = Path("data/processed/pre_diligencia_status_validacao.csv")
MANUAL_INPUT = Path("data/input/pre_diligencia_status_validacao_manual.csv")
OUTPUT_TEMPLATE = Path("data/processed/pre_diligencia_status_validacao_template_drive.csv")
OUTPUT_READY = Path("data/processed/pre_diligencia_status_validacao_ready_for_drive.csv")
OUTPUT_REPORT = Path("data/processed/pre_diligencia_manual_validation_report.csv")
OUTPUT_EVIDENCE = Path("data/evidence/evidence_pre_diligencia_manual_validation.csv")
RULES_PATH = Path("config/pre_diligencia_manual_validation_rules.yaml")


def ler_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def salvar_csv(path: Path, rows: list[dict[str, Any]], campos: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if campos is None:
        campos = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def config() -> dict[str, Any]:
    if not RULES_PATH.exists():
        return {}
    with RULES_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def norm(v: str | None) -> str:
    return str(v or "").strip().lower()


def gerar_template(base_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    # Mantém as colunas originais do status, adicionando campos de controle se não existirem.
    campos_extra = {
        "validacao_manual_status": "pendente",
        "erro_validacao": "",
        "alerta_validacao": "",
    }
    out = []
    for row in base_rows:
        r = dict(row)
        for k, v in campos_extra.items():
            r.setdefault(k, v)
        out.append(r)
    return out


def validar(rows: list[dict[str, str]], cfg: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    report = []
    ids = {}
    required = cfg.get("campos_obrigatorios_identificacao", [])
    controlled = cfg.get("campos_manuais_controlados", {})

    for idx, row in enumerate(rows, start=2):
        rid = row.get("id_pre_diligencia", "")
        if rid:
            ids.setdefault(rid, []).append(idx)

        for field in required:
            if not str(row.get(field, "")).strip():
                report.append({
                    "linha": str(idx),
                    "id_pre_diligencia": rid,
                    "campo": field,
                    "severidade": "erro",
                    "codigo": "VAL_CAMPO_OBRIGATORIO_VAZIO",
                    "mensagem": f"Campo obrigatório vazio: {field}",
                })

        for field, meta in controlled.items():
            allowed = [norm(x) for x in meta.get("permitido", [])]
            value = norm(row.get(field, ""))
            if value not in allowed:
                report.append({
                    "linha": str(idx),
                    "id_pre_diligencia": rid,
                    "campo": field,
                    "severidade": "erro",
                    "codigo": "VAL_VALOR_FORA_LISTA",
                    "mensagem": f"Valor não permitido para {field}: {row.get(field, '')}",
                })

        status = norm(row.get("status_contato"))
        telefone = norm(row.get("telefone_validado"))
        email = norm(row.get("email_validado"))
        if status == "contato_confirmado" and not (telefone or email):
            report.append({
                "linha": str(idx),
                "id_pre_diligencia": rid,
                "campo": "status_contato",
                "severidade": "alerta",
                "codigo": "ALERTA_CONTATO_CONFIRMADO_SEM_CANAL",
                "mensagem": "Contato confirmado sem telefone_validado ou email_validado.",
            })

        docs_solic = norm(row.get("documentos_solicitados"))
        docs_rec = norm(row.get("documentos_recebidos"))
        if docs_rec == "sim" and docs_solic in {"", "não", "nao"}:
            report.append({
                "linha": str(idx),
                "id_pre_diligencia": rid,
                "campo": "documentos_recebidos",
                "severidade": "alerta",
                "codigo": "ALERTA_DOCUMENTO_RECEBIDO_SEM_SOLICITACAO",
                "mensagem": "Documentos recebidos = sim, mas documentos_solicitados está vazio/não.",
            })

        decisao = norm(row.get("decisao_pos_contato"))
        obs = norm(row.get("observacoes_validacao"))
        if decisao in {"bloquear", "descartar"} and not obs:
            report.append({
                "linha": str(idx),
                "id_pre_diligencia": rid,
                "campo": "observacoes_validacao",
                "severidade": "alerta",
                "codigo": "ALERTA_BLOQUEIO_DESCARTE_SEM_OBSERVACAO",
                "mensagem": "Bloquear/descartar exige observação de validação.",
            })

    for rid, linhas in ids.items():
        if len(linhas) > 1:
            report.append({
                "linha": ",".join(map(str, linhas)),
                "id_pre_diligencia": rid,
                "campo": "id_pre_diligencia",
                "severidade": "erro",
                "codigo": "VAL_ID_DUPLICADO",
                "mensagem": "id_pre_diligencia duplicado.",
            })

    rows_validated = []
    errors_by_id = {}
    alerts_by_id = {}
    for item in report:
        rid = item.get("id_pre_diligencia", "")
        if item.get("severidade") == "erro":
            errors_by_id.setdefault(rid, []).append(item["codigo"])
        else:
            alerts_by_id.setdefault(rid, []).append(item["codigo"])

    for row in rows:
        r = dict(row)
        rid = r.get("id_pre_diligencia", "")
        r["validacao_manual_status"] = "erro" if errors_by_id.get(rid) else ("alerta" if alerts_by_id.get(rid) else "ok")
        r["erro_validacao"] = "|".join(errors_by_id.get(rid, []))
        r["alerta_validacao"] = "|".join(alerts_by_id.get(rid, []))
        rows_validated.append(r)

    if not report:
        report.append({
            "linha": "",
            "id_pre_diligencia": "",
            "campo": "",
            "severidade": "ok",
            "codigo": "SEM_ERROS",
            "mensagem": "Arquivo manual validado sem erros ou alertas.",
        })

    return rows_validated, report


def gerar_evidencia(total: int, erros: int, alertas: int, usou_manual: bool) -> list[dict[str, str]]:
    return [{
        "id_evidencia": "EVD_PRE_DILIGENCIA_MANUAL_VALIDATION",
        "id_fonte": "PRE_DILIGENCIA_CONSOLIDACAO",
        "id_indicador": "MON_02; RISK_OSC_01",
        "tipo_evidencia": "validacao_input_manual",
        "pergunta_ou_lacuna": "A planilha manual de pré-diligência está estruturalmente válida para reincorporação ao GitHub?",
        "url_ou_arquivo": "data/processed/pre_diligencia_manual_validation_report.csv",
        "titulo_documento": "Validação de entrada manual da pré-diligência — Rodada 4.9",
        "pagina_tabela_secao": "relatório de validação",
        "trecho_original_ou_descricao": f"Linhas avaliadas: {total}; erros: {erros}; alertas: {alertas}; arquivo manual usado: {'sim' if usou_manual else 'não'}.",
        "resumo_ptbr": "Evidência de validação estrutural da planilha editável de pré-diligência.",
        "valor_extraido": str(erros),
        "unidade": "erros",
        "periodo_referencia": "pós-Rodada 4.8",
        "territorio": "Manaus/AM; Benjamin Constant/AM; Belém/PA; Santarém/PA",
        "metodo_extracao": "validação automatizada de schema e valores controlados",
        "nivel_confianca": "alto_para_schema; baixo_para_conteúdo_manual_não_auditado",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_revisao_humana",
        "limitacoes": "A validação não confirma veracidade documental; apenas estrutura e consistência mínima.",
        "uso_na_calculadora": "Controle de qualidade dos dados manuais de pré-diligência.",
        "status_evidencia": "pendente",
    }]


def executar_validacao_input_manual(
    base_status: Path = BASE_STATUS,
    manual_input: Path = MANUAL_INPUT,
    output_template: Path = OUTPUT_TEMPLATE,
    output_ready: Path = OUTPUT_READY,
    output_report: Path = OUTPUT_REPORT,
    output_evidence: Path = OUTPUT_EVIDENCE,
) -> dict[str, Any]:
    cfg = config()
    base_rows = ler_csv(base_status)
    template = gerar_template(base_rows)
    campos = list(template[0].keys()) if template else []
    salvar_csv(output_template, template, campos=campos)

    usar_manual = manual_input.exists() and manual_input.stat().st_size > 0
    rows_to_validate = ler_csv(manual_input) if usar_manual else template

    validated, report = validar(rows_to_validate, cfg)
    campos_validated = list(validated[0].keys()) if validated else campos
    salvar_csv(output_ready, validated, campos=campos_validated)
    salvar_csv(output_report, report)

    erros = sum(1 for r in report if r.get("severidade") == "erro")
    alertas = sum(1 for r in report if r.get("severidade") == "alerta")
    evidence = gerar_evidencia(len(rows_to_validate), erros, alertas, usar_manual)
    salvar_csv(output_evidence, evidence)

    return {
        "total_linhas": len(rows_to_validate),
        "erros": erros,
        "alertas": alertas,
        "usou_manual": usar_manual,
        "arquivos": {
            "template": str(output_template),
            "ready": str(output_ready),
            "report": str(output_report),
            "evidence": str(output_evidence),
        }
    }
