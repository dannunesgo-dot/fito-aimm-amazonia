from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "rodada_4_38_final_ifc_aimm_operational_package.py"
    spec = importlib.util.spec_from_file_location("rodada_4_38_final_ifc_aimm_operational_package", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _rows_for_dimension(module, confianca: str) -> list[dict[str, str]]:
    rows = []
    for dim in module.DIMENSIONS:
        if dim["dimensao"] == "territorial_gis":
            continue
        rows.extend(
            [
                {
                    "dimensao_aimm_predominante": dim["dimensao"],
                    "status_extracao": "texto_extraido",
                    "tipo_documento": "pdf",
                    "classificacao_confianca": confianca,
                },
                {
                    "dimensao_aimm_predominante": dim["dimensao"],
                    "status_extracao": "pdf_extraido",
                    "tipo_documento": "pdf",
                    "classificacao_confianca": confianca,
                },
            ]
        )
    return rows


def test_classify_aplica_confianca_media_quando_margem_e_pequena():
    modulo = _load_module()
    triagem = modulo.classify("nota_tecnica.txt", "text/plain", "mercado demanda risco")
    assert triagem["classificacao_confianca"] == "media"
    assert triagem["margem_pontuacao"] == 1


def test_classify_aplica_hint_por_tipo_documento():
    modulo = _load_module()
    triagem = modulo.classify("relatorio_geral.csv", "text/csv", "mercado custo")
    assert triagem["tipo_documento"] == "planilha"
    assert triagem["dimensao_aimm_predominante"] == "financeiro_operacional"


def test_build_scores_penaliza_score_quando_baixa_confianca_predomina():
    modulo = _load_module()
    sem_penalidade = _rows_for_dimension(modulo, "alta")
    com_penalidade = _rows_for_dimension(modulo, "baixa")

    _, score_sem_penalidade, classe_sem_penalidade = modulo.build_scores(sem_penalidade, "1302603", "nao")
    _, score_com_penalidade, classe_com_penalidade = modulo.build_scores(com_penalidade, "1302603", "nao")

    assert score_sem_penalidade == 88.0
    assert score_com_penalidade == 79.2
    assert score_com_penalidade < score_sem_penalidade
    assert classe_sem_penalidade == "apto_para_relatorio_profissional_com_revisao_humana"
    assert classe_com_penalidade == "apto_com_lacunas_para_complementacao"
