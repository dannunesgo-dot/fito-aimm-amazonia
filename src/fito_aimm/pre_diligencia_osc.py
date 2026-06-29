
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml


INPUT_TOPN = Path("data/processed/organizacoes_pre_diligencia_topN.csv")
INPUT_CHECKLIST = Path("data/processed/checklist_contato_validacao.csv")
OUTPUT_QUEUE = Path("data/processed/pre_diligencia_fila_contato.csv")
OUTPUT_STATUS = Path("data/processed/pre_diligencia_status_validacao.csv")
OUTPUT_DOCS = Path("data/processed/pre_diligencia_solicitacao_documentos.csv")
OUTPUT_EVIDENCE = Path("data/evidence/evidence_pre_diligencia_osc.csv")
RULES_PATH = Path("config/pre_diligencia_osc_rules.yaml")


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


def vazio(valor: str | None) -> bool:
    return not str(valor or "").strip()


def int_safe(valor: str | None, default: int = 999) -> int:
    try:
        return int(float(str(valor or "").strip()))
    except Exception:
        return default


def prioridade_operacional(linha: dict[str, str], config: dict[str, Any]) -> str:
    parametros = config.get("parametros", {})
    risco = int_safe(linha.get("risco_osc_score"))
    bloqueios = str(linha.get("bloqueios_para_lista_curta_formal", ""))

    if "possivelmente_baixada_ou_inativa" in bloqueios:
        return "P4_bloqueio_cadastral"
    if "sem_cnpj_ou_id" in bloqueios:
        return "P4_bloqueio_identificacao"

    p1 = int(parametros.get("prioridade_1_risco_maximo", 40))
    p2 = int(parametros.get("prioridade_2_risco_maximo", 60))
    p3 = int(parametros.get("prioridade_3_risco_maximo", 75))

    if risco <= p1:
        return "P1_contatar_primeiro"
    if risco <= p2:
        return "P2_contatar_segundo"
    if risco <= p3:
        return "P3_contato_exploratorio"
    return "P4_baixa_prioridade"


def canal_preferencial(linha: dict[str, str]) -> str:
    if not vazio(linha.get("telefone_original")):
        return "telefone"
    if not vazio(linha.get("email_original")):
        return "email"
    if not vazio(linha.get("endereco_original")):
        return "localizar_por_endereco"
    return "sem_canal_disponivel"


def montar_fila_contato(topn: list[dict[str, str]], config: dict[str, Any]) -> list[dict[str, str]]:
    filas = []
    for linha in topn:
        prioridade = prioridade_operacional(linha, config)
        canal = canal_preferencial(linha)
        municipio = linha.get("municipio", "")
        uf = linha.get("uf", "")
        rank = linha.get("rank_pre_diligencia_municipio", "")

        filas.append({
            "id_pre_diligencia": f"PD_{uf}_{municipio}_{rank}".replace(" ", "_").replace("/", "_"),
            "rank_pre_diligencia_municipio": rank,
            "prioridade_operacional": prioridade,
            "canal_preferencial": canal,
            "cnpj_ou_id": linha.get("cnpj_ou_id", ""),
            "nome_organizacao": linha.get("nome_organizacao", ""),
            "municipio": municipio,
            "uf": uf,
            "risco_osc_score": linha.get("risco_osc_score", ""),
            "classe_risco_osc": linha.get("classe_risco_osc", ""),
            "score_triagem": linha.get("score_triagem", ""),
            "telefone_original": linha.get("telefone_original", linha.get("telefone", "")),
            "email_original": linha.get("email_original", linha.get("email", "")),
            "endereco_original": linha.get("endereco_original", linha.get("endereco", "")),
            "bloqueios_para_lista_curta_formal": linha.get("bloqueios_para_lista_curta_formal", ""),
            "motivo_pre_diligencia": linha.get("motivo_pre_diligencia", ""),
            "status_contato": "pendente",
            "data_primeira_tentativa": "",
            "data_ultima_tentativa": "",
            "numero_tentativas": "0",
            "resultado_contato": "",
            "observacoes_contato": "",
            "uso_autorizado": "contato_validacao_cadastral_documental",
            "trava": "não seleciona executora",
        })

    ordem = {
        "P1_contatar_primeiro": 1,
        "P2_contatar_segundo": 2,
        "P3_contato_exploratorio": 3,
        "P4_bloqueio_cadastral": 4,
        "P4_bloqueio_identificacao": 5,
        "P4_baixa_prioridade": 6,
    }
    return sorted(filas, key=lambda x: (x["municipio"], ordem.get(x["prioridade_operacional"], 99), int_safe(x["rank_pre_diligencia_municipio"])))


def montar_status_validacao(fila: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for linha in fila:
        out.append({
            "id_pre_diligencia": linha["id_pre_diligencia"],
            "cnpj_ou_id": linha["cnpj_ou_id"],
            "nome_organizacao": linha["nome_organizacao"],
            "municipio": linha["municipio"],
            "uf": linha["uf"],
            "prioridade_operacional": linha["prioridade_operacional"],
            "status_contato": "pendente",
            "telefone_validado": "",
            "email_validado": "",
            "representante_identificado": "",
            "cargo_representante": "",
            "cnpj_validado": "",
            "situacao_cadastral_validada": "",
            "natureza_juridica_validada": "",
            "endereco_validado": "",
            "aderencia_tematica_validada": "",
            "capacidade_operacional_preliminar": "",
            "risco_juridico_preliminar": "",
            "documentos_solicitados": "",
            "documentos_recebidos": "",
            "necessita_entrevista": "",
            "necessita_visita": "",
            "decisao_pos_contato": "pendente",
            "responsavel_pela_validacao": "",
            "data_atualizacao": "",
            "observacoes_validacao": "",
        })
    return out


def montar_solicitacao_documentos(fila: list[dict[str, str]]) -> list[dict[str, str]]:
    documentos = [
        "Comprovante de CNPJ ou cadastro equivalente",
        "Estatuto social ou documento constitutivo",
        "Ata de eleição/posse da diretoria vigente",
        "Documento que comprove representante legal ou ponto focal autorizado",
        "Comprovante de endereço",
        "Certidões de regularidade fiscal/trabalhista quando aplicável",
        "Portfólio, relatório ou evidência de atuação territorial",
        "Evidência de atuação em saúde, agricultura, bioeconomia, sustentabilidade, P&D ou capacitação",
        "Informação sobre equipe, estrutura operacional e capacidade de prestação de contas",
    ]
    out = []
    for linha in fila:
        out.append({
            "id_pre_diligencia": linha["id_pre_diligencia"],
            "nome_organizacao": linha["nome_organizacao"],
            "municipio": linha["municipio"],
            "uf": linha["uf"],
            "canal_preferencial": linha["canal_preferencial"],
            "mensagem_base": (
                "Prezados(as), estamos realizando etapa preliminar de validação cadastral e documental "
                "para mapeamento de organizações com possível aderência ao projeto Fito+ Amazônia. "
                "Esta solicitação não representa seleção, contratação ou compromisso de parceria."
            ),
            "documentos_solicitados": " | ".join(documentos),
            "prazo_sugerido_dias": "10",
            "status_envio": "pendente",
            "data_envio": "",
            "resposta_recebida": "",
            "observacoes": "",
        })
    return out


def gerar_evidencias(fila: list[dict[str, str]]) -> list[dict[str, str]]:
    resumo: dict[str, dict[str, int]] = {}
    for linha in fila:
        key = f"{linha['municipio']}/{linha['uf']}"
        if key not in resumo:
            resumo[key] = {"total": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 0}
        resumo[key]["total"] += 1
        pr = linha["prioridade_operacional"]
        if pr.startswith("P1"):
            resumo[key]["P1"] += 1
        elif pr.startswith("P2"):
            resumo[key]["P2"] += 1
        elif pr.startswith("P3"):
            resumo[key]["P3"] += 1
        else:
            resumo[key]["P4"] += 1

    evid = []
    for territorio, v in sorted(resumo.items()):
        evid.append({
            "id_evidencia": "EVD_PRE_DILIGENCIA_" + territorio.replace("/", "_").replace(" ", "_").upper(),
            "id_fonte": "RISK_OSC_DIAGNOSTICS",
            "id_indicador": "RISK_OSC_01; MON_02; INT_BEN_05",
            "tipo_evidencia": "fila_pre_diligencia",
            "pergunta_ou_lacuna": "Quais organizações devem ser contatadas para validação cadastral e documental preliminar?",
            "url_ou_arquivo": "data/processed/pre_diligencia_fila_contato.csv",
            "titulo_documento": "Fila operacional de pré-diligência OSC — Rodada 4.7",
            "pagina_tabela_secao": "fila de contato e validação documental",
            "trecho_original_ou_descricao": f"{territorio}: {v['total']} organizações na fila; P1={v['P1']}; P2={v['P2']}; P3={v['P3']}; P4={v['P4']}.",
            "resumo_ptbr": "Evidência de organização da pré-diligência para contato e validação documental.",
            "valor_extraido": str(v["total"]),
            "unidade": "organizações",
            "periodo_referencia": "pós-Rodada 4.6",
            "territorio": territorio,
            "metodo_extracao": "geração automatizada a partir de organizacoes_pre_diligencia_topN.csv",
            "nivel_confianca": "médio_para_planejamento; baixo_para_decisão_final",
            "data_coleta": "",
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "pendente_execucao_manual",
            "limitacoes": "Fila não seleciona executora; depende de validação cadastral, documental, contato, entrevista e visita técnica.",
            "uso_na_calculadora": "Organização da diligência e monitoramento de risco de executores.",
            "status_evidencia": "pendente",
        })
    return evid


def executar_pre_diligencia_osc(
    input_topn: Path = INPUT_TOPN,
    input_checklist: Path = INPUT_CHECKLIST,
    output_queue: Path = OUTPUT_QUEUE,
    output_status: Path = OUTPUT_STATUS,
    output_docs: Path = OUTPUT_DOCS,
    output_evidence: Path = OUTPUT_EVIDENCE,
) -> dict[str, Any]:
    config = carregar_config()
    topn = ler_csv(input_topn)
    if not topn:
        raise ValueError("organizacoes_pre_diligencia_topN.csv está vazio.")

    fila = montar_fila_contato(topn, config)
    status = montar_status_validacao(fila)
    docs = montar_solicitacao_documentos(fila)
    evidencias = gerar_evidencias(fila)

    salvar_csv(output_queue, fila)
    salvar_csv(output_status, status)
    salvar_csv(output_docs, docs)
    salvar_csv(output_evidence, evidencias)

    resumo = {
        "total_fila": len(fila),
        "total_status": len(status),
        "total_docs": len(docs),
        "total_evidencias": len(evidencias),
        "p1": sum(1 for l in fila if l["prioridade_operacional"].startswith("P1")),
        "p2": sum(1 for l in fila if l["prioridade_operacional"].startswith("P2")),
        "p3": sum(1 for l in fila if l["prioridade_operacional"].startswith("P3")),
        "p4": sum(1 for l in fila if l["prioridade_operacional"].startswith("P4")),
    }

    return {
        "resumo": resumo,
        "arquivos": {
            "fila": str(output_queue),
            "status": str(output_status),
            "documentos": str(output_docs),
            "evidencias": str(output_evidence),
        },
    }
