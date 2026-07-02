"""
DEPRECATED — Removido em refactor/phase1 (2026-07-02)

Módulo inicial de extração.
Extrai metadados e valores de respostas já baixadas.

RAZÃO DA REMOÇÃO:
- Função trivial nunca utilizada
- Lógica de extração distribuída em módulos específicos:
  * src/fito_aimm/coletor_mapaosc.py → padronizar_linhas()
  * src/fito_aimm/coletor_ibge.py → extração de séries
  * src/fito_aimm/aimm_engine.py → cálculo de scores

NOTA:
Se precisar de extração genérica, criar em Fase 2:
  src/fito_aimm/extractors/base_extractor.py
"""

def extrair_valor_simples(registro: dict, campo: str):
    return registro.get(campo)
