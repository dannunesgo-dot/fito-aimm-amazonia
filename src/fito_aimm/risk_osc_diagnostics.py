
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml


INPUT_RISK = Path("data/processed/risk_osc_screening.csv")
OUTPUT_DIAG = Path("data/processed/risk_osc_diagnostics.csv")
OUTPUT_SCENARIOS = Path("data/processed/risk_osc_threshold_scenarios.csv")
OUTPUT_TOPN = Path("data/processed/organizacoes_pre_diligencia_topN.csv")
OUTPUT_CHECKLIST = Path("data/processed/checklist_contato_validacao.csv")
OUTPUT_EVIDENCE = Path("data/evidence/evidence_risk_osc_diagnostics.csv")
RULES_PATH = Path("config/risk_osc_diagnostics_rules.yaml")


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


def bool_text(cond: bool) -> str:
    return "sim" if cond else "não"


def municipio_key(linha: dict[str, str]) -> str:
    return f"{linha.get('municipio','')}/{linha.get('uf','')}"


def has_marker(linha: dict[str, str], marcador: str) -> bool:
    return marcador in str(linha.get("marcadores_triagem", ""))


def contato_minimo(linha: dict[str, str]) -> bool:
    return (not vazio(linha.get("email"))) or (not vazio(linha.get("telefone")))


def tem_aderencia_tematica(linha: dict[str, str]) -> bool:
    marcadores = str(linha.get("marcadores_triagem", ""))
    termos = [
        "cooperativa",
        "associacao",
        "saude",
        "agricultura_extrativismo_bioeconomia",
        "meio_ambiente_sustentabilidade",
        "pesquisa_educacao_capacitacao",
    ]
    return any(t in marcadores for t in termos)


def bloqueios(linha: dict[str, str]) -> list[str]:
    out = []
    if vazio(linha.get("cnpj_ou_id")):
        out.append("sem_cnpj_ou_id")
    if not contato_minimo(linha):
        out.append("sem_email_telefone")
    if vazio(linha.get("endereco")):
        out.append("sem_endereco")
    if has_marker(linha, "possivelmente_baixada_ou_inativa"):
        out.append("possivelmente_baixada_ou_inativa")
    if linha.get("trava_decisoria") and linha.get("trava_decisoria") != "apta_para_diligencia_preliminar":
        out.append(linha.get("trava_decisoria", "trava_nao_especificada"))
    return sorted(set(out))


def motivo_pre_diligencia(linha: dict[str, str]) -> str:
    motivos = []
    risco = int_safe(linha.get("risco_osc_score"), 999)
    if risco <= 30:
        motivos.append("baixo_risco_relativo")
    elif risco <= 60:
        motivos.append("risco_moderado")
    elif risco <= 75:
        motivos.append("risco_intermediario_para_contato_exploratorio")
    if contato_minimo(linha):
        motivos.append("possui_contato_minimo")
    if not vazio(linha.get("cnpj_ou_id")):
        motivos.append("possui_cnpj_ou_id")
    if tem_aderencia_tematica(linha):
        motivos.append("possui_marcador_tematico")
    if not motivos:
        motivos.append("selecionada_apenas_por_ranqueamento_relativo")
    return "|".join(motivos)


def gerar_diagnosticos(linhas: list[dict[str, str]]) -> list[dict[str, str]]:
    diagn = []

    total = len(linhas)
    diagn.append({"escopo": "global", "grupo": "todos", "metrica": "total_organizacoes", "valor": str(total), "unidade": "organizações", "interpretacao": "Total de organizações avaliadas no screening de risco."})

    classes = ["baixo", "moderado", "alto"]
    for classe in classes:
        n = sum(1 for l in linhas if l.get("classe_risco_osc") == classe)
        pct = (n / total * 100) if total else 0
        diagn.append({"escopo": "global", "grupo": classe, "metrica": "classe_risco_osc", "valor": f"{n}", "unidade": "organizações", "interpretacao": f"{pct:.2f}% do total com risco {classe}."})

    for nome_metrica, func, interp in [
        ("sem_cnpj_ou_id", lambda l: vazio(l.get("cnpj_ou_id")), "Organizações sem identificador verificável."),
        ("sem_email_telefone", lambda l: not contato_minimo(l), "Organizações sem contato mínimo para diligência remota."),
        ("sem_endereco", lambda l: vazio(l.get("endereco")), "Organizações sem endereço registrado."),
        ("possivelmente_baixada_ou_inativa", lambda l: has_marker(l, "possivelmente_baixada_ou_inativa"), "Organizações com alerta de baixa ou inatividade."),
        ("com_aderencia_tematica", lambda l: tem_aderencia_tematica(l), "Organizações com pelo menos um marcador temático útil ao Fito+ Amazônia."),
    ]:
        n = sum(1 for l in linhas if func(l))
        pct = (n / total * 100) if total else 0
        diagn.append({"escopo": "global", "grupo": "todos", "metrica": nome_metrica, "valor": str(n), "unidade": "organizações", "interpretacao": f"{interp} Percentual: {pct:.2f}%."})

    municipios = sorted(set(municipio_key(l) for l in linhas))
    for mun in municipios:
        subset = [l for l in linhas if municipio_key(l) == mun]
        denom = len(subset)
        diagn.append({"escopo": "municipio", "grupo": mun, "metrica": "total_organizacoes", "valor": str(denom), "unidade": "organizações", "interpretacao": "Total avaliado no município."})
        for classe in classes:
            n = sum(1 for l in subset if l.get("classe_risco_osc") == classe)
            pct = (n / denom * 100) if denom else 0
            diagn.append({"escopo": "municipio", "grupo": mun, "metrica": f"risco_{classe}", "valor": str(n), "unidade": "organizações", "interpretacao": f"{pct:.2f}% no município."})
        n_contato = sum(1 for l in subset if contato_minimo(l))
        n_cnpj = sum(1 for l in subset if not vazio(l.get("cnpj_ou_id")))
        n_tema = sum(1 for l in subset if tem_aderencia_tematica(l))
        diagn.append({"escopo": "municipio", "grupo": mun, "metrica": "com_contato_minimo", "valor": str(n_contato), "unidade": "organizações", "interpretacao": "Possuem e-mail ou telefone para diligência inicial."})
        diagn.append({"escopo": "municipio", "grupo": mun, "metrica": "com_cnpj_ou_id", "valor": str(n_cnpj), "unidade": "organizações", "interpretacao": "Possuem identificador preenchido para verificação cadastral."})
        diagn.append({"escopo": "municipio", "grupo": mun, "metrica": "com_aderencia_tematica", "valor": str(n_tema), "unidade": "organizações", "interpretacao": "Possuem marcador temático relevante."})

    return diagn


def contar_cenario(linhas: list[dict[str, str]], id_cenario: str, top_n_por_mun: int = 25) -> tuple[int, dict[str, int]]:
    por_mun = {}
    if id_cenario == "S04_TOPN_MUNICIPIO":
        total = 0
        for mun in sorted(set(municipio_key(l) for l in linhas)):
            subset = [l for l in linhas if municipio_key(l) == mun]
            subset = sorted(subset, key=lambda x: (int_safe(x.get("risco_osc_score")), -int_safe(x.get("score_triagem"), 0)))
            n = min(top_n_por_mun, len(subset))
            por_mun[mun] = n
            total += n
        return total, por_mun

    def ok(l: dict[str, str]) -> bool:
        risco = int_safe(l.get("risco_osc_score"))
        if id_cenario == "S00_REGRAS_ATUAIS":
            return (
                l.get("trava_decisoria") == "apta_para_diligencia_preliminar"
                and l.get("recomendacao_diligencia") in ["priorizar_diligencia", "avaliar_com_cautela"]
            )
        if id_cenario == "S01_RISCO_BAIXO_MODERADO":
            return risco <= 60
        if id_cenario == "S02_RISCO_ATE_75":
            return risco <= 75
        if id_cenario == "S03_COM_CNPJ_E_CONTATO":
            return risco <= 70 and (not vazio(l.get("cnpj_ou_id"))) and contato_minimo(l)
        return False

    total = 0
    for mun in sorted(set(municipio_key(l) for l in linhas)):
        n = sum(1 for l in linhas if municipio_key(l) == mun and ok(l))
        por_mun[mun] = n
        total += n
    return total, por_mun


def gerar_cenarios(linhas: list[dict[str, str]], config: dict[str, Any]) -> list[dict[str, str]]:
    top_n = int(config.get("parametros", {}).get("top_n_por_municipio", 25))
    cenarios_cfg = config.get("cenarios", [])
    linhas_out = []

    for c in cenarios_cfg:
        total, por_mun = contar_cenario(linhas, c["id_cenario"], top_n)
        linhas_out.append({
            "id_cenario": c["id_cenario"],
            "nome_cenario": c.get("nome", ""),
            "descricao": c.get("descricao", ""),
            "territorio": "TOTAL",
            "organizacoes_enquadradas": str(total),
            "uso_permitido": "diagnostico_e_pre_diligencia",
            "trava": "não seleciona executora",
            "interpretacao": "Cenário usado para calibrar limiares e planejar contato/validação."
        })
        for mun, n in por_mun.items():
            linhas_out.append({
                "id_cenario": c["id_cenario"],
                "nome_cenario": c.get("nome", ""),
                "descricao": c.get("descricao", ""),
                "territorio": mun,
                "organizacoes_enquadradas": str(n),
                "uso_permitido": "diagnostico_e_pre_diligencia",
                "trava": "não seleciona executora",
                "interpretacao": "Contagem municipal no cenário."
            })

    return linhas_out


def gerar_topn(linhas: list[dict[str, str]], config: dict[str, Any]) -> list[dict[str, str]]:
    top_n = int(config.get("parametros", {}).get("top_n_por_municipio", 25))
    output = []
    campos_extra = [
        "rank_pre_diligencia_municipio",
        "motivo_pre_diligencia",
        "bloqueios_para_lista_curta_formal",
        "uso_autorizado",
        "status_pre_diligencia",
    ]

    for mun in sorted(set(municipio_key(l) for l in linhas)):
        subset = [dict(l) for l in linhas if municipio_key(l) == mun]
        subset = sorted(subset, key=lambda x: (
            int_safe(x.get("risco_osc_score")),
            -int_safe(x.get("score_triagem"), 0),
            x.get("nome_organizacao", "")
        ))
        for rank, linha in enumerate(subset[:top_n], start=1):
            b = bloqueios(linha)
            linha["rank_pre_diligencia_municipio"] = str(rank)
            linha["motivo_pre_diligencia"] = motivo_pre_diligencia(linha)
            linha["bloqueios_para_lista_curta_formal"] = "|".join(b) if b else "sem_bloqueio_automatico_identificado"
            linha["uso_autorizado"] = "contato_validacao_cadastral_documental"
            linha["status_pre_diligencia"] = "pendente_contato"
            output.append(linha)

    return output


def gerar_checklist(topn: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for linha in topn:
        rows.append({
            "rank_pre_diligencia_municipio": linha.get("rank_pre_diligencia_municipio", ""),
            "cnpj_ou_id": linha.get("cnpj_ou_id", ""),
            "nome_organizacao": linha.get("nome_organizacao", ""),
            "municipio": linha.get("municipio", ""),
            "uf": linha.get("uf", ""),
            "risco_osc_score": linha.get("risco_osc_score", ""),
            "classe_risco_osc": linha.get("classe_risco_osc", ""),
            "telefone_original": linha.get("telefone", ""),
            "email_original": linha.get("email", ""),
            "endereco_original": linha.get("endereco", ""),
            "bloqueios_para_lista_curta_formal": linha.get("bloqueios_para_lista_curta_formal", ""),
            "status_contato": "pendente",
            "telefone_validado": "",
            "email_validado": "",
            "representante_identificado": "",
            "cnpj_validado": "",
            "situacao_cadastral_validada": "",
            "documentos_solicitados": "",
            "documentos_recebidos": "",
            "necessita_visita": "",
            "observacoes_validacao": "",
            "decisao_pos_contato": "pendente",
        })
    return rows


def gerar_evidencias(diagn: list[dict[str, str]], scenarios: list[dict[str, str]], topn: list[dict[str, str]]) -> list[dict[str, str]]:
    evid = []
    total_topn = len(topn)
    municipios = sorted({r["grupo"] for r in diagn if r["escopo"] == "municipio" and r["metrica"] == "total_organizacoes"})
    for mun in municipios:
        total = next((r["valor"] for r in diagn if r["escopo"] == "municipio" and r["grupo"] == mun and r["metrica"] == "total_organizacoes"), "0")
        top = sum(1 for l in topn if municipio_key(l) == mun)
        scen_s00 = next((r["organizacoes_enquadradas"] for r in scenarios if r["id_cenario"] == "S00_REGRAS_ATUAIS" and r["territorio"] == mun), "0")
        scen_s04 = next((r["organizacoes_enquadradas"] for r in scenarios if r["id_cenario"] == "S04_TOPN_MUNICIPIO" and r["territorio"] == mun), "0")
        evid.append({
            "id_evidencia": "EVD_RISK_OSC_DIAG_" + re.sub(r"[^A-Za-z0-9]+", "_", mun).strip("_").upper(),
            "id_fonte": "SRC_MAPA_OSC; RISK_OSC_SCREENING",
            "id_indicador": "RISK_OSC_01; INT_BEN_05; MON_02",
            "tipo_evidencia": "diagnostico_screening_e_cenario",
            "pergunta_ou_lacuna": "Por que a lista curta ficou zerada e quais organizações devem entrar em contato/validação preliminar?",
            "url_ou_arquivo": "data/processed/risk_osc_diagnostics.csv; data/processed/risk_osc_threshold_scenarios.csv; data/processed/organizacoes_pre_diligencia_topN.csv",
            "titulo_documento": "Diagnóstico do screening de risco OSC — Rodada 4.6",
            "pagina_tabela_secao": "diagnóstico agregado; cenários de limiar; top N por município",
            "trecho_original_ou_descricao": f"{mun}: {total} organizações avaliadas; cenário atual formal S00 enquadra {scen_s00}; topN para pré-diligência propõe {top} contatos controlados; cenário S04 enquadra {scen_s04}.",
            "resumo_ptbr": "Evidência diagnóstica para explicar lista curta zerada e organizar contato preliminar sem seleção automática.",
            "valor_extraido": str(top),
            "unidade": "organizações em pré-diligência",
            "periodo_referencia": "maio/2026",
            "territorio": mun,
            "metodo_extracao": "análise automatizada sobre risk_osc_screening.csv",
            "nivel_confianca": "médio_para_triagem; baixo_para_decisão_final",
            "data_coleta": "",
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "pendente_verificacao_humana",
            "limitacoes": "Pré-diligência não seleciona executora; exige validação cadastral, documental, contato, entrevista e visita técnica.",
            "uso_na_calculadora": "Calibração do risco OSC e planejamento de diligência documental.",
            "status_evidencia": "pendente",
        })
    return evid


def executar_diagnostico_risk_osc(
    input_risk: Path = INPUT_RISK,
    output_diag: Path = OUTPUT_DIAG,
    output_scenarios: Path = OUTPUT_SCENARIOS,
    output_topn: Path = OUTPUT_TOPN,
    output_checklist: Path = OUTPUT_CHECKLIST,
    output_evidence: Path = OUTPUT_EVIDENCE,
) -> dict[str, Any]:
    config = carregar_config()
    linhas = ler_csv(input_risk)
    if not linhas:
        raise ValueError("risk_osc_screening.csv está vazio.")

    diagn = gerar_diagnosticos(linhas)
    scenarios = gerar_cenarios(linhas, config)
    topn = gerar_topn(linhas, config)
    checklist = gerar_checklist(topn)
    evidence = gerar_evidencias(diagn, scenarios, topn)

    salvar_csv(output_diag, diagn)
    salvar_csv(output_scenarios, scenarios)
    salvar_csv(output_topn, topn)
    salvar_csv(output_checklist, checklist)
    salvar_csv(output_evidence, evidence)

    resumo = {
        "total_organizacoes": len(linhas),
        "total_pre_diligencia_topn": len(topn),
        "total_checklist": len(checklist),
        "total_evidencias": len(evidence),
        "cenario_atual_total": next((r["organizacoes_enquadradas"] for r in scenarios if r["id_cenario"] == "S00_REGRAS_ATUAIS" and r["territorio"] == "TOTAL"), "0"),
        "cenario_topn_total": next((r["organizacoes_enquadradas"] for r in scenarios if r["id_cenario"] == "S04_TOPN_MUNICIPIO" and r["territorio"] == "TOTAL"), "0"),
    }
    return {
        "resumo": resumo,
        "diagnosticos": diagn,
        "cenarios": scenarios,
        "topn": topn,
        "checklist": checklist,
        "evidencias": evidence,
        "arquivos": {
            "diagnosticos": str(output_diag),
            "cenarios": str(output_scenarios),
            "topn": str(output_topn),
            "checklist": str(output_checklist),
            "evidencias": str(output_evidence),
        }
    }
