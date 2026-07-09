# Plano de Conferência e Alinhamento Total (AIMM ↔ World Bank) — v1.0

## 1. Objetivo
Conferir e alinhar integralmente os indicadores AIMM com indicadores oficiais da World Bank API, com rastreabilidade, qualidade metodológica e governança de atualização.

## 2. Escopo
- Cobrir 20 categorias de trabalho AIMM (com referência temática WB para apoio de classificação).
- Classificar cada mapeamento como **Direto**, **Proxy** ou **Contexto**.
- Validar metadados oficiais de cada indicador WB antes de aprovação.

## 3. Fontes Oficiais e Evidências
### 3.1 Fonte primária
- Portal WB Indicators: https://data.worldbank.org/indicator

### 3.2 Endpoints de conferência
- Indicador por código: `https://api.worldbank.org/v2/indicator/{CODE}?format=json`
- Tópicos: `https://api.worldbank.org/v2/topic?format=json`
- Indicadores por tópico: `https://api.worldbank.org/v2/topic/{TOPIC_ID}/indicator?format=json`
- Indicadores WDI (source 2): `https://api.worldbank.org/v2/source/2/indicator/{CODE}?format=json`

### 3.3 Evidências já recebidas
- `topic.json`: válido (retorna 21 tópicos WB).
- `indicator.json` e `{CODE}.json`: inválidos por placeholder `{CODE}` não substituído (erro id=120).

## 4. Regras de Mapeamento
- **Direto**: conceito AIMM e WB equivalentes (definição/unidade/interpretação).
- **Proxy**: aproximação parcial com justificativa técnica.
- **Contexto**: indicador de ambiente, sem equivalência direta ao conceito AIMM.

## 5. Critérios de Qualidade
Cada linha da matriz deve conter:
- definição AIMM explícita
- código WB válido
- nome oficial WB
- unidade e periodicidade
- tópico WB
- confiabilidade: **Alta/Média/Baixa**
- status: **Aprovado/Revisar/Lacuna**

## 6. Fluxo Operacional por Indicador
1. Confirmar definição AIMM.
2. Buscar candidato(s) WB.
3. Validar código e metadados no endpoint oficial.
4. Avaliar aderência conceitual e unidade.
5. Classificar (Direto/Proxy/Contexto) e confiabilidade.
6. Registrar decisão e evidência na matriz.

## 7. Execução em Ondas (20 categorias)
- Onda 1: categorias 1–5
- Onda 2: categorias 6–10
- Onda 3: categorias 11–15
- Onda 4: categorias 16–20
- Fechamento: auditoria cruzada + consolidação v1.0

## 8. Entregáveis
- `docs/INTERFACE_INTEGRATION_PLAN.md`
- `docs/AIMM_WB_MAPPING_MATRIX_TEMPLATE.csv` (template)
- `docs/AIMM_WB_MAPPING_MATRIX.csv` (preenchida)
- `docs/AIMM_WB_GAPS.md`
- `docs/AIMM_WB_DECISION_LOG.md`

## 9. Governança e Versionamento
- Revisão: trimestral.
- Mudanças exigem registro no `AIMM_WB_DECISION_LOG.md`.
- Versões: v1.0, v1.1, v1.2...

## 10. Riscos conhecidos no início
- Indicadores AIMM sem equivalente WB direto.
- Diferença de granularidade (local AIMM vs nacional WB).
- Uso excessivo de proxy sem justificativa.