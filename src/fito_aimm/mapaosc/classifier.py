from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd

from ..territorios import carregar_municipios_projeto
from .fetcher import agora_utc_iso


MUNICIPIOS_PROJETO = carregar_municipios_projeto()


def contem_alguma(texto_norm: str, palavras: list[str], normalize: Callable[[Any], str]) -> bool:
    return any(normalize(p) in texto_norm for p in palavras)


def classificar_organizacao(
    row: pd.Series,
    colmap: dict[str, str],
    criterios: dict[str, Any],
    texto_bruto: str,
    normalize: Callable[[Any], str],
) -> dict[str, Any]:
    palavras = criterios.get("palavras_chave", {})
    pontos = criterios.get("pontuacao", {})
    texto = normalize(texto_bruto)
    score = int(pontos.get("base_municipio_alvo", 20))
    flags = []

    situacao = normalize(row.get(colmap.get("situacao", ""), "")) if colmap.get("situacao") else ""
    if any(x in situacao for x in ["baixada", "inativa", "encerrada"]):
        score += int(pontos.get("penalidade_baixada_inativa", -40))
        flags.append("possivelmente_baixada_ou_inativa")
    else:
        score += int(pontos.get("ativa_ou_sem_baixa", 15))
        flags.append("ativa_ou_sem_baixa_identificada")

    for chave, ponto_nome, flag in [
        ("associacao", "tipo_associacao", "associacao"),
        ("cooperativa", "tipo_cooperativa", "cooperativa"),
        ("fundacao", "tipo_fundacao", "fundacao"),
        ("saude", "area_saude", "saude"),
        ("agricultura_extrativismo_bioeconomia", "area_agricultura_extrativismo_bioeconomia", "agricultura_extrativismo_bioeconomia"),
        ("meio_ambiente_sustentabilidade", "area_meio_ambiente_sustentabilidade", "meio_ambiente_sustentabilidade"),
        ("pesquisa_educacao_capacitacao", "area_pesquisa_educacao_capacitacao", "pesquisa_educacao_capacitacao"),
    ]:
        if contem_alguma(texto, palavras.get(chave, []), normalize):
            score += int(pontos.get(ponto_nome, 0))
            flags.append(flag)

    def get_col(chave: str) -> str:
        col = colmap.get(chave, "")
        return str(row.get(col, "") or "").strip() if col else ""

    if get_col("email") or get_col("telefone"):
        score += int(pontos.get("possui_email_ou_telefone", 10))
        flags.append("contato_minimo")
    if get_col("endereco"):
        score += int(pontos.get("possui_endereco", 5))
        flags.append("endereco")
    if not (get_col("email") or get_col("telefone") or get_col("endereco")):
        score += int(pontos.get("penalidade_dado_minimo_insuficiente", -10))
        flags.append("dados_contato_insuficientes")

    classe = "alta_prioridade" if score >= 70 else ("media_prioridade" if score >= 40 else "baixa_prioridade")
    return {"score_triagem": score, "classificacao_triagem": classe, "marcadores_triagem": "|".join(flags)}


def gerar_resumo_por_municipio(linhas: list[dict[str, str]]) -> list[dict[str, str]]:
    resumo = {
        f"{item['municipio']}/{item['uf']}": {"total": 0, "alta": 0, "media": 0, "baixa": 0, "coop": 0, "assoc": 0}
        for item in MUNICIPIOS_PROJETO.values()
    }
    for linha in linhas:
        chave = f"{linha['municipio']}/{linha['uf']}"
        if chave not in resumo:
            continue
        resumo[chave]["total"] += 1
        if linha["classificacao_triagem"] == "alta_prioridade":
            resumo[chave]["alta"] += 1
        elif linha["classificacao_triagem"] == "media_prioridade":
            resumo[chave]["media"] += 1
        else:
            resumo[chave]["baixa"] += 1
        if "cooperativa" in linha.get("marcadores_triagem", ""):
            resumo[chave]["coop"] += 1
        if "associacao" in linha.get("marcadores_triagem", ""):
            resumo[chave]["assoc"] += 1

    saida = []
    for chave, valores in resumo.items():
        municipio, uf = chave.split("/")
        saida.append({
            "municipio": municipio,
            "uf": uf,
            "total_organizacoes_filtradas": str(valores["total"]),
            "alta_prioridade": str(valores["alta"]),
            "media_prioridade": str(valores["media"]),
            "baixa_prioridade": str(valores["baixa"]),
            "com_marcador_cooperativa": str(valores["coop"]),
            "com_marcador_associacao": str(valores["assoc"]),
            "fonte": "SRC_MAPA_OSC",
        })
    return saida


def gerar_evidencias_mapaosc(
    resumo: list[dict[str, str]],
    salvar_csv: Callable[[Path, list[dict[str, Any]], list[str] | None], None],
    normalizar_coluna: Callable[[str], str],
    arquivo_saida: Path = Path("data/evidence/evidence_mapaosc_triagem.csv"),
) -> list[dict[str, str]]:
    data = agora_utc_iso()
    evidencias = []
    for linha in resumo:
        evidencias.append({
            "id_evidencia": f"EVD_MAPAOSC_TRIAGEM_{normalizar_coluna(linha['municipio'])}_{linha['uf']}",
            "id_fonte": "SRC_MAPA_OSC",
            "id_indicador": "GAP_TERR_05; INT_BEN_05; RISK_OSC_01; MON_02",
            "tipo_evidencia": "base_publica_filtrada",
            "pergunta_ou_lacuna": "Quais OSCs, associações, cooperativas e organizações candidatas existem no município?",
            "url_ou_arquivo": "data/processed/organizacoes_candidatas_mapaosc.csv",
            "titulo_documento": "Triagem automatizada de OSCs — Mapa das OSCs/Ipea",
            "pagina_tabela_secao": "Base principal do Mapa das OSCs; coleta maio/2026; filtro municipal",
            "trecho_original_ou_descricao": f"{linha['municipio']}/{linha['uf']}: {linha['total_organizacoes_filtradas']} organizações filtradas; {linha['alta_prioridade']} alta prioridade; {linha['media_prioridade']} média prioridade.",
            "resumo_ptbr": "Evidência de triagem remota inicial para seleção de organizações executoras/parceiras.",
            "valor_extraido": linha["total_organizacoes_filtradas"],
            "unidade": "organizações",
            "periodo_referencia": "maio/2026",
            "territorio": f"{linha['municipio']}/{linha['uf']}",
            "metodo_extracao": "download da base principal do Mapa das OSCs e filtragem automatizada por município",
            "nivel_confianca": "médio",
            "data_coleta": data,
            "conferido_por": "workflow GitHub Actions",
            "status_conferencia": "pendente_verificacao_humana",
            "limitacoes": "Triagem remota; requer validação documental, contato, regularidade jurídica e avaliação de campo.",
            "uso_na_calculadora": "Linha de base de organizações candidatas e risco de capacidade executora.",
            "status_evidencia": "pendente",
        })
    salvar_csv(arquivo_saida, evidencias, None)
    return evidencias
