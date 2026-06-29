
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml


INPUT_STATUS = Path("data/processed/pre_diligencia_status_validacao.csv")
INPUT_FILA = Path("data/processed/pre_diligencia_fila_contato.csv")
OUTPUT_CONSOLIDADO = Path("data/processed/pre_diligencia_consolidado.csv")
OUTPUT_ENCAMINHAMENTOS = Path("data/processed/pre_diligencia_encaminhamentos.csv")
OUTPUT_PENDENCIAS = Path("data/processed/pre_diligencia_pendencias.csv")
OUTPUT_EVIDENCE = Path("data/evidence/evidence_pre_diligencia_consolidacao.csv")
RULES_PATH = Path("config/pre_diligencia_consolidacao_rules.yaml")


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {caminho}")
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def salvar_csv(caminho: Path, linhas: list[dict[str, Any]], campos: list[str] | None = None) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if campos is None:
        campos = list(linhas[0].keys()) if linhas else []
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(linhas)


def carregar_config() -> dict[str, Any]:
    if not RULES_PATH.exists():
        return {}
    with RULES_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def norm(valor: str | None) -> str:
    return re.sub(r"\s+", " ", str(valor or "").strip().lower())


def positivo(valor: str | None) -> bool:
    return norm(valor) in {"sim", "s", "yes", "true", "validado", "confirmado", "ok", "regular", "ativa", "apta"}


def contem_alerta(valor: str | None) -> bool:
    texto = norm(valor)
    alertas = ["sanção", "sancao", "impedimento", "irregular", "baixada", "inativa", "inapta", "fraude", "bloqueio"]
    return any(a in texto for a in alertas)


def situacao_aceita(valor: str | None) -> bool:
    texto = norm(valor)
    return any(v in texto for v in ["ativa", "regular", "apta"])


def indexar_por_id(linhas: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {l.get("id_pre_diligencia", ""): l for l in linhas if l.get("id_pre_diligencia")}


def avaliar_linha(status: dict[str, str], fila: dict[str, str] | None = None) -> dict[str, str]:
    fila = fila or {}

    contato_confirmado = (
        norm(status.get("status_contato")) in {"contato_confirmado", "confirmado"}
        or positivo(status.get("telefone_validado"))
        or positivo(status.get("email_validado"))
    )
    cnpj_ok = positivo(status.get("cnpj_validado"))
    situacao_ok = situacao_aceita(status.get("situacao_cadastral_validada"))
    representante_ok = positivo(status.get("representante_identificado"))
    aderencia_nao = norm(status.get("aderencia_tematica_validada")) in {"não", "nao", "não aderente", "nao aderente"}
    alerta_juridico = contem_alerta(status.get("risco_juridico_preliminar")) or contem_alerta(status.get("situacao_cadastral_validada"))

    pendencias = []
    if not contato_confirmado:
        pendencias.append("confirmar_contato")
    if not cnpj_ok:
        pendencias.append("validar_cnpj")
    if not situacao_ok:
        pendencias.append("validar_situacao_cadastral")
    if not representante_ok:
        pendencias.append("identificar_representante")
    if not positivo(status.get("documentos_recebidos")):
        pendencias.append("receber_documentos")

    if alerta_juridico:
        encaminhamento = "bloquear"
        justificativa = "alerta_juridico_ou_cadastral"
    elif aderencia_nao:
        encaminhamento = "descartar"
        justificativa = "sem_aderencia_tematica_validada"
    elif contato_confirmado and cnpj_ok and situacao_ok and representante_ok:
        if positivo(status.get("documentos_recebidos")):
            encaminhamento = "recomendar_visita"
            justificativa = "campos_minimos_e_documentos_recebidos"
        else:
            encaminhamento = "solicitar_documentos"
            justificativa = "campos_minimos_ok_documentos_pendentes"
    elif contato_confirmado:
        encaminhamento = "solicitar_documentos"
        justificativa = "contato_confirmado_com_pendencias"
    else:
        encaminhamento = "continuar_contato"
        justificativa = "sem_contato_confirmado"

    return {
        "contato_confirmado": "sim" if contato_confirmado else "não",
        "cnpj_ok": "sim" if cnpj_ok else "não",
        "situacao_cadastral_ok": "sim" if situacao_ok else "não",
        "representante_ok": "sim" if representante_ok else "não",
        "alerta_juridico": "sim" if alerta_juridico else "não",
        "pendencias_automaticas": "|".join(pendencias) if pendencias else "sem_pendencia_automatica",
        "encaminhamento_recomendado": encaminhamento,
        "justificativa_encaminhamento": justificativa,
        "trava": "não seleciona executora",
    }


def gerar_evidencias(consolidado: list[dict[str, str]]) -> list[dict[str, str]]:
    resumo: dict[str, dict[str, int]] = {}
    for l in consolidado:
        key = f"{l.get('municipio','')}/{l.get('uf','')}"
        if key not in resumo:
            resumo[key] = {
                "total": 0,
                "continuar_contato": 0,
                "solicitar_documentos": 0,
                "agendar_entrevista": 0,
                "recomendar_visita": 0,
                "bloquear": 0,
                "descartar": 0,
            }
        resumo[key]["total"] += 1
        enc = l.get("encaminhamento_recomendado", "continuar_contato")
        if enc not in resumo[key]:
            resumo[key][enc] = 0
        resumo[key][enc] += 1

    evid = []
    for territorio, v in sorted(resumo.items()):
        evid.append({
            "id_evidencia": "EVD_PRE_DILIGENCIA_CONS_" + territorio.replace("/", "_").replace(" ", "_").upper(),
            "id_fonte": "PRE_DILIGENCIA_OSC",
            "id_indicador": "RISK_OSC_01; MON_02; INT_BEN_05",
            "tipo_evidencia": "consolidacao_pre_diligencia",
            "pergunta_ou_lacuna": "Qual é o encaminhamento das organizações após validação preliminar?",
            "url_ou_arquivo": "data/processed/pre_diligencia_consolidado.csv",
            "titulo_documento": "Consolidação da pré-diligência OSC — Rodada 4.8",
            "pagina_tabela_secao": "consolidado e encaminhamentos",
            "trecho_original_ou_descricao": f"{territorio}: total={v['total']}; continuar_contato={v.get('continuar_contato',0)}; solicitar_documentos={v.get('solicitar_documentos',0)}; recomendar_visita={v.get('recomendar_visita',0)}; bloquear={v.get('bloquear',0)}; descartar={v.get('descartar',0)}.",
            "resumo_ptbr": "Evidência da consolidação da pré-diligência e encaminhamentos operacionais.",
            "valor_extraido": str(v["total"]),
            "unidade": "organizações",
            "periodo_referencia": "pós-Rodada 4.7",
            "territorio": territorio,
            "metodo_extracao": "consolidação automatizada de planilha de status de validação",
            "nivel_confianca": "baixo_sem_preenchimento_manual; aumenta após validação humana",
            "data_coleta": "",
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "pendente_validacao_humana",
            "limitacoes": "Se os campos manuais estiverem vazios, os encaminhamentos permanecem preliminares.",
            "uso_na_calculadora": "Monitoramento de pré-diligência e risco de organizações executoras.",
            "status_evidencia": "pendente",
        })
    return evid


def executar_consolidacao_pre_diligencia(
    input_status: Path = INPUT_STATUS,
    input_fila: Path = INPUT_FILA,
    output_consolidado: Path = OUTPUT_CONSOLIDADO,
    output_encaminhamentos: Path = OUTPUT_ENCAMINHAMENTOS,
    output_pendencias: Path = OUTPUT_PENDENCIAS,
    output_evidence: Path = OUTPUT_EVIDENCE,
) -> dict[str, Any]:
    status_rows = ler_csv(input_status)
    fila_rows = ler_csv(input_fila)
    fila_idx = indexar_por_id(fila_rows)

    consolidado = []
    encaminhamentos = []
    pendencias = []

    for row in status_rows:
        fid = row.get("id_pre_diligencia", "")
        fila = fila_idx.get(fid, {})
        avaliacao = avaliar_linha(row, fila)
        merged = {**fila, **row, **avaliacao}
        consolidado.append(merged)

        encaminhamentos.append({
            "id_pre_diligencia": fid,
            "nome_organizacao": merged.get("nome_organizacao", ""),
            "municipio": merged.get("municipio", ""),
            "uf": merged.get("uf", ""),
            "encaminhamento_recomendado": avaliacao["encaminhamento_recomendado"],
            "justificativa_encaminhamento": avaliacao["justificativa_encaminhamento"],
            "trava": avaliacao["trava"],
        })

        pendencias.append({
            "id_pre_diligencia": fid,
            "nome_organizacao": merged.get("nome_organizacao", ""),
            "municipio": merged.get("municipio", ""),
            "uf": merged.get("uf", ""),
            "pendencias_automaticas": avaliacao["pendencias_automaticas"],
            "contato_confirmado": avaliacao["contato_confirmado"],
            "cnpj_ok": avaliacao["cnpj_ok"],
            "situacao_cadastral_ok": avaliacao["situacao_cadastral_ok"],
            "representante_ok": avaliacao["representante_ok"],
            "alerta_juridico": avaliacao["alerta_juridico"],
        })

    evidencias = gerar_evidencias(consolidado)

    salvar_csv(output_consolidado, consolidado)
    salvar_csv(output_encaminhamentos, encaminhamentos)
    salvar_csv(output_pendencias, pendencias)
    salvar_csv(output_evidence, evidencias)

    resumo = {
        "total_consolidado": len(consolidado),
        "total_encaminhamentos": len(encaminhamentos),
        "total_pendencias": len(pendencias),
        "total_evidencias": len(evidencias),
        "recomendar_visita": sum(1 for l in encaminhamentos if l["encaminhamento_recomendado"] == "recomendar_visita"),
        "solicitar_documentos": sum(1 for l in encaminhamentos if l["encaminhamento_recomendado"] == "solicitar_documentos"),
        "continuar_contato": sum(1 for l in encaminhamentos if l["encaminhamento_recomendado"] == "continuar_contato"),
        "bloquear": sum(1 for l in encaminhamentos if l["encaminhamento_recomendado"] == "bloquear"),
        "descartar": sum(1 for l in encaminhamentos if l["encaminhamento_recomendado"] == "descartar"),
    }

    return {
        "resumo": resumo,
        "arquivos": {
            "consolidado": str(output_consolidado),
            "encaminhamentos": str(output_encaminhamentos),
            "pendencias": str(output_pendencias),
            "evidencias": str(output_evidence),
        },
    }
