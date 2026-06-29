
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml


INPUT_ORGS = Path("data/processed/organizacoes_candidatas_mapaosc.csv")
OUTPUT_RISK = Path("data/processed/risk_osc_screening.csv")
OUTPUT_SHORTLIST = Path("data/processed/organizacoes_lista_curta_diligencia.csv")
OUTPUT_EVIDENCE = Path("data/evidence/evidence_risk_osc_screening.csv")
RULES_PATH = Path("config/risk_osc_rules.yaml")


def carregar_yaml(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    with caminho.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo ausente: {caminho}. "
            "Rode primeiro o workflow mapaosc-triagem ou envie organizacoes_candidatas_mapaosc.csv para data/processed."
        )
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


def is_empty(value: str | None) -> bool:
    return not str(value or "").strip()


def calcular_risco_osc(linha: dict[str, str], config: dict[str, Any]) -> dict[str, Any]:
    pesos = config.get("pesos", {})
    risco = int(pesos.get("risco_base", 50))
    fatores = []

    classificacao = linha.get("classificacao_triagem", "")
    marcadores = linha.get("marcadores_triagem", "")

    if classificacao == "alta_prioridade":
        ajuste = int(pesos.get("reducao_alta_prioridade_mapaosc", -25))
        risco += ajuste
        fatores.append(f"alta_prioridade_mapaosc:{ajuste}")
    elif classificacao == "media_prioridade":
        ajuste = int(pesos.get("reducao_media_prioridade_mapaosc", -10))
        risco += ajuste
        fatores.append(f"media_prioridade_mapaosc:{ajuste}")
    elif classificacao == "baixa_prioridade":
        ajuste = int(pesos.get("acrescimo_baixa_prioridade_mapaosc", 20))
        risco += ajuste
        fatores.append(f"baixa_prioridade_mapaosc:+{ajuste}")

    if "possivelmente_baixada_ou_inativa" in marcadores:
        ajuste = int(pesos.get("acrescimo_possivelmente_baixada_ou_inativa", 35))
        risco += ajuste
        fatores.append(f"possivelmente_baixada_ou_inativa:+{ajuste}")

    if is_empty(linha.get("cnpj_ou_id")):
        ajuste = int(pesos.get("acrescimo_sem_cnpj_ou_id", 25))
        risco += ajuste
        fatores.append(f"sem_cnpj_ou_id:+{ajuste}")

    if is_empty(linha.get("email")) and is_empty(linha.get("telefone")):
        ajuste = int(pesos.get("acrescimo_sem_contato", 20))
        risco += ajuste
        fatores.append(f"sem_email_telefone:+{ajuste}")

    if is_empty(linha.get("endereco")):
        ajuste = int(pesos.get("acrescimo_sem_endereco", 10))
        risco += ajuste
        fatores.append(f"sem_endereco:+{ajuste}")

    for marcador, chave_peso in [
        ("cooperativa", "reducao_cooperativa"),
        ("associacao", "reducao_associacao"),
        ("saude", "reducao_aderencia_saude"),
        ("agricultura_extrativismo_bioeconomia", "reducao_aderencia_agricultura_bioeconomia"),
        ("meio_ambiente_sustentabilidade", "reducao_aderencia_meio_ambiente"),
        ("pesquisa_educacao_capacitacao", "reducao_aderencia_pesquisa_capacitacao"),
    ]:
        if marcador in marcadores:
            ajuste = int(pesos.get(chave_peso, 0))
            risco += ajuste
            fatores.append(f"{marcador}:{ajuste}")

    risco = max(0, min(100, risco))

    if risco <= 30:
        classe_risco = "baixo"
    elif risco <= 60:
        classe_risco = "moderado"
    else:
        classe_risco = "alto"

    if classe_risco == "baixo" and classificacao in ["alta_prioridade", "media_prioridade"]:
        recomendacao = "priorizar_diligencia"
    elif classe_risco == "moderado":
        recomendacao = "avaliar_com_cautela"
    else:
        recomendacao = "nao_priorizar_sem_comprovacao"

    if "possivelmente_baixada_ou_inativa" in marcadores or is_empty(linha.get("cnpj_ou_id")):
        trava = "bloqueada_ate_comprovacao_cadastral"
    elif is_empty(linha.get("email")) and is_empty(linha.get("telefone")):
        trava = "bloqueada_ate_contato_ativo"
    else:
        trava = "apta_para_diligencia_preliminar"

    return {
        "risco_osc_score": str(risco),
        "classe_risco_osc": classe_risco,
        "fatores_risco": "|".join(fatores),
        "recomendacao_diligencia": recomendacao,
        "trava_decisoria": trava,
    }


def executar_risk_osc_screening(
    input_orgs: Path = INPUT_ORGS,
    output_risk: Path = OUTPUT_RISK,
    output_shortlist: Path = OUTPUT_SHORTLIST,
    output_evidence: Path = OUTPUT_EVIDENCE,
) -> dict[str, Any]:
    config = carregar_yaml(RULES_PATH)
    organizacoes = ler_csv(input_orgs)

    linhas_risco = []
    for linha in organizacoes:
        risco = calcular_risco_osc(linha, config)
        linhas_risco.append({**linha, **risco})

    linhas_ordenadas = sorted(
        linhas_risco,
        key=lambda x: (
            int(x.get("risco_osc_score") or 100),
            -int(x.get("score_triagem") or 0)
        )
    )

    campos = list(linhas_ordenadas[0].keys()) if linhas_ordenadas else []
    salvar_csv(output_risk, linhas_ordenadas, campos=campos)

    lista_curta = [
        linha for linha in linhas_ordenadas
        if linha.get("recomendacao_diligencia") in ["priorizar_diligencia", "avaliar_com_cautela"]
        and linha.get("trava_decisoria") == "apta_para_diligencia_preliminar"
    ][:50]
    salvar_csv(output_shortlist, lista_curta, campos=campos)

    resumo = {}
    for linha in linhas_ordenadas:
        municipio = f"{linha.get('municipio','')}/{linha.get('uf','')}"
        if municipio not in resumo:
            resumo[municipio] = {"total": 0, "baixo": 0, "moderado": 0, "alto": 0, "lista_curta": 0}
        resumo[municipio]["total"] += 1
        classe = linha.get("classe_risco_osc", "alto")
        resumo[municipio][classe] += 1

    for linha in lista_curta:
        municipio = f"{linha.get('municipio','')}/{linha.get('uf','')}"
        if municipio in resumo:
            resumo[municipio]["lista_curta"] += 1

    evidencias = []
    for municipio, valores in resumo.items():
        evidencias.append({
            "id_evidencia": "EVD_RISK_OSC_" + re.sub(r"[^A-Za-z0-9]+", "_", municipio).strip("_").upper(),
            "id_fonte": "SRC_MAPA_OSC",
            "id_indicador": "RISK_OSC_01; INT_BEN_05; MON_02",
            "tipo_evidencia": "screening_risco_automatizado",
            "pergunta_ou_lacuna": "Qual é o risco preliminar das organizações candidatas identificadas por município?",
            "url_ou_arquivo": str(output_risk),
            "titulo_documento": "Screening preliminar de risco de OSCs — Fito+ Amazônia",
            "pagina_tabela_secao": "data/processed/risk_osc_screening.csv",
            "trecho_original_ou_descricao": (
                f"{municipio}: {valores['total']} organizações avaliadas; "
                f"{valores['baixo']} baixo risco; {valores['moderado']} risco moderado; "
                f"{valores['alto']} alto risco; {valores['lista_curta']} em lista curta preliminar."
            ),
            "resumo_ptbr": "Evidência automatizada de risco preliminar de organizações candidatas.",
            "valor_extraido": str(valores["lista_curta"]),
            "unidade": "organizações",
            "periodo_referencia": "maio/2026",
            "territorio": municipio,
            "metodo_extracao": "screening automatizado sobre resultado do Mapa das OSCs",
            "nivel_confianca": "baixo_para_decisao_final; médio_para_triagem",
            "data_coleta": "",
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "pendente_verificacao_humana",
            "limitacoes": "Não substitui diligência documental, consulta cadastral, contato ativo, entrevista e visita técnica.",
            "uso_na_calculadora": "Risco preliminar de capacidade executora e priorização de diligência.",
            "status_evidencia": "pendente",
        })

    campos_evidencia = list(evidencias[0].keys()) if evidencias else []
    salvar_csv(output_evidence, evidencias, campos=campos_evidencia)

    return {
        "total_organizacoes": len(linhas_ordenadas),
        "total_lista_curta": len(lista_curta),
        "resumo": resumo,
        "output_risk": str(output_risk),
        "output_shortlist": str(output_shortlist),
        "output_evidence": str(output_evidence),
    }
