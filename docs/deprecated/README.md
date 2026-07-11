# Módulos descontinuados (deprecated)

## aimm_engine.py — DESCONTINUADO em 2026-07-11
**Substituído por:** `src/fito_aimm/fitomais_aimm_engine.py`

### Motivo da descontinuação
O `aimm_engine.py` implementava uma mecânica de cálculo que **não corresponde à
metodologia oficial do AIMM** (IFC Guidance Note, março 2026). Usava média
ponderada de notas 0–100 por dimensão, com penalização de risco proporcional e
fator de confiança multiplicativo.

A norma oficial do IFC usa:
- ratings qualitativos (Marginal/Moderate/Strong/Very Strong) convertidos em
  pontos fixos (4/12/30/50);
- ajuste de risco binário (fator 1,00 ou 0,75);
- soma dos eixos Project + Market, cada um arredondado ao múltiplo de 2;
- faixas Excellent 72 / Good 43 / Satisfactory 22 / Low 8.

O diagnóstico completo do descompasso está em
`docs/AIMM_ENGINE_METHODOLOGY_GAP.md`.

### Nota
O próprio `aimm_engine.py` se declarava "preliminar" e "não representa AIMM final
validado" — foi um protótipo consciente. O motor definitivo
(`fitomais_aimm_engine.py`) implementa a mecânica oficial e é validado por 7
casos de teste derivados da norma, incluindo o exemplo oficial "52 = Good".

Preservado aqui para rastreabilidade e histórico. Não deve ser usado em produção.
