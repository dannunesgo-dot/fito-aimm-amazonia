
---

## aimm_dashboard.py (versão antiga) — DESCONTINUADO em 2026-07-11
**Substituído por:** a nova versão de `src/fito_aimm/aimm_dashboard.py`, religada
ao motor oficial.

### Motivo
O dashboard antigo consumia as saídas do `aimm_engine.py` descontinuado e
apresentava **scores por dimensão e por indicador** — conceitos que não existem
na metodologia oficial do AIMM. O dashboard novo apresenta a estrutura correta:
os dois eixos (Project Outcome e Market Outcome), o score final e a faixa.

### O que mudou nas saídas
- REMOVIDO: `aimm_dashboard_dimension_view.csv` (visão por dimensão).
- ADICIONADO: `aimm_dashboard_axes_view.csv` (visão por eixo).
- Demais saídas mantiveram os nomes, para não quebrar o `aimm_communication`.

## testar_aimm_engine.py — DESCONTINUADO
Testava o motor antigo. O motor oficial é validado por
`scripts/testar_fitomais_aimm_engine.py` (7 casos derivados da norma IFC).
