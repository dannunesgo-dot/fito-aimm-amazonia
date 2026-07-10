# UI Architecture Alignment — Auditoria Factual AIMM

> **Data da auditoria:** 2026-07-10  
> **Branch base:** `main`  
> **Método:** leitura direta de código-fonte, configs e seeds — sem inferência.

---

## 1. Tabela "Bloco UI → Endpoint → Status → Evidência"

| Bloco UI | Endpoint / Mecanismo | Status | Arquivo | Linhas | Observação |
|---|---|---|---|---|---|
| **Busca/Filtros — países** | `GET /worldbank/countries` | IMPLEMENTADO | `app.py` | 158–190 | Paginação; ****** obrigatório |
| **Busca/Filtros — indicadores WB** | `GET /worldbank/indicators?search=` | IMPLEMENTADO | `app.py` | 191–227 | Filtro por nome; retorna top-10 |
| **Série temporal** | `GET /worldbank/data/{country}/{indicator}` | IMPLEMENTADO | `app.py` | 230–320 | Série temporal com filtro de data |
| **Tabela de indicadores AIMM** | Arquivo `data/processed/aimm_indicator_scores.csv` | PARCIAL | `aimm_engine.py` | 1–200 | Gerado por pipeline; não exposto via endpoint HTTP |
| **Tabela de dimensões AIMM** | Arquivo `data/processed/aimm_dimension_scores.csv` | PARCIAL | `aimm_dashboard.py` | 1–300 | Gerado por pipeline; não exposto via endpoint HTTP |
| **Cards do dashboard** | Arquivo `data/processed/aimm_dashboard_cards.csv` + JSON | PARCIAL | `aimm_dashboard.py` | 1–300 | Payload JSON em `outputs/reports/aimm_dashboard_payload.json` |
| **Detalhes por indicador** | Nenhum endpoint `/api/indicators/{id}` | AUSENTE | — | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |
| **Visualização: série temporal** | `outputs/visuals/aimm_dashboard_executivo.html` (estático) | PARCIAL | `aimm_communication.py` | 116–160 | HTML gerado; sem interatividade |
| **Visualização: comparativo dimensional** | Tabela HTML no dashboard executivo | PARCIAL | `aimm_communication.py` | 138–160 | Tabela, não gráfico interativo |
| **Visualização: mapa** | `data/raw/gis/municipio_manaus_1302603.gpkg` (Manaus apenas) | PARCIAL | `data/raw/gis/` | — | QGIS manual; sem endpoint de mapa web |
| **Visualização: export** | SVG, Mermaid, JSON, Markdown | PARCIAL | `aimm_communication.py` | 235–320 | Exportação por pipeline; sem botão de export na UI web |
| **Upload de arquivo** | Nenhum endpoint `POST /api/upload` | AUSENTE | `docs/FEATURE_STATUS_BY_BRANCH.md` | — | Experimental em `origin/copilot/research-data-ingestion-analysis` |
| **Health check** | `GET /health` | IMPLEMENTADO | `app.py` | 147–156 | Sem autenticação |
| **Autenticação** | ****** via Caddy gateway | IMPLEMENTADO | `app.py` + `Caddyfile` | `app.py:80–107`, `Caddyfile:10` | Token validado em formato; não em valor |
| **Resumo executivo** | `outputs/reports/aimm_executive_summary.md` + JSON | IMPLEMENTADO | `aimm_dashboard.py` | 145–175 | Gerado por pipeline |

---

## 2. Componentes já operacionais (sem novo desenvolvimento)

Os seguintes componentes funcionam no estado atual de `main`, a partir dos seeds e pipeline já versionados:

1. **API World Bank** (`app.py` linhas 158–320): 3 endpoints GET funcionais com autenticação Bearer.
   - `GET /worldbank/countries` — `app.py:158`
   - `GET /worldbank/indicators` — `app.py:191`
   - `GET /worldbank/data/{country}/{indicator}` — `app.py:230`

2. **Motor AIMM** (`src/fito_aimm/aimm_engine.py`): calcula scores de indicadores, dimensões e resultado global a partir de seeds CSV. Produz 5 arquivos de saída em `data/processed/`.

3. **Dashboard AIMM** (`src/fito_aimm/aimm_dashboard.py`): gera resumo executivo, cards, dimension view, next actions. Produz CSV + JSON + Markdown.

4. **Pacote de comunicação** (`src/fito_aimm/aimm_communication.py`): gera HTML, SVG, Mermaid, Markdown e JSON a partir do dashboard. Artefatos em `outputs/visuals/` e `outputs/reports/`.

5. **Health check** (`GET /health`, `app.py:147`): endpoint de status sem autenticação.

6. **GIS baseline Manaus** (`data/raw/gis/municipio_manaus_1302603.gpkg`): GeoPackage validado. Join visual via QGIS manual (confirmado em Rodada 4.22-D, evidência em `docs/FEATURE_STATUS_BY_BRANCH.md`).

7. **Contrato canônico de indicadores** (`docs/contracts/indicator_canonical.schema.json`): schema JSON definido com campos obrigatórios e exemplos (`docs/contracts/indicator_examples.json`).

---

## 3. Lacunas para MVP

| Lacuna | Severidade | Branch relacionado |
|---|---|---|
| Sem endpoint `GET /api/indicators?filtro=` (indicadores AIMM internos) | Alta | NÃO_COMPROVADO em nenhuma branch |
| Sem endpoint `POST /api/upload` (ingestão via web) | Alta | EXPERIMENTAL em `origin/copilot/research-data-ingestion-analysis` |
| Sem endpoint `GET /api/indicators/{id}` (detalhes por indicador) | Alta | AUSENTE |
| Sem painel web interativo (Plotly, Dash, etc.) | Média | AUSENTE — referenciado em `docs/FEATURE_STATUS_BY_BRANCH.md` como futuro refactor/phase3 |
| GIS apenas para Manaus; Benjamin Constant, Belém, Santarém sem GeoPackage processado | Alta | `data/reference/gis_baseline_control_seed.csv` — status `pendente_gis` para MUN_002–004 |
| Normalização automática WB ↔ AIMM | Média | EXPERIMENTAL em `origin/copilot/research-aimm-calculator-analysis` |
| Validação de token ****** valor (apenas formato validado hoje) | Média | `app.py:80–107` |
| Score final AIMM bloqueado (apenas score estrutural preliminar) | Alta | `aimm_engine.py` — `pode_ser_usado_como_score_final: "não"` |

---

## 4. Sequência de implementação (2 semanas) — sem retrabalho

Baseada exclusivamente no estado atual do repositório e nos gaps identificados.

### Semana 1

| Dia | Ação | Arquivo-alvo | Gate |
|---|---|---|---|
| 1–2 | Criar endpoint `GET /api/indicators` em `app.py` expondo `data/processed/aimm_indicator_scores.csv` | `app.py` | Teste `GET /api/indicators` retorna JSON com schema canônico |
| 2–3 | Criar endpoint `GET /api/indicators/{id}` retornando payload canônico (`docs/contracts/indicator_canonical.schema.json`) | `app.py` | Payload validado contra schema |
| 3–4 | Criar endpoint `GET /api/dashboard` expondo `data/processed/aimm_dashboard_payload.json` | `app.py` | Payload existente servido via HTTP |
| 4–5 | Baixar e registrar GeoPackages de Benjamin Constant (1300607), Belém (1501402) e Santarém (1506807) em `data/raw/gis/` | `data/raw/gis/` | Presença dos 3 arquivos `.gpkg` confirmada |

### Semana 2

| Dia | Ação | Arquivo-alvo | Gate |
|---|---|---|---|
| 6–7 | Externalizar CSS do HTML para `config/ui_styles.css`; referenciar em `aimm_communication.py` | `aimm_communication.py` | CSS editável sem alterar Python |
| 7–8 | Criar mapeamento `faixa_score → cor` em `config/aimm_communication_rules.yaml` | config | Paleta formal documentada |
| 8–9 | Implementar endpoint `POST /api/upload` básico (validação de manifesto CSV, sem persistência complexa) | `app.py` | Upload de CSV retorna validação estrutural |
| 9–10 | Concluir revisão humana de artefatos visuais per `data/reference/aimm_visual_review_checklist_seed.csv` | outputs | Checklist com todos itens `aprovado` |

---

## 5. Gates de release

| Gate | Condição | Evidência de bloqueio atual |
|---|---|---|
| Score AIMM final | `pode_ser_usado_como_score_final == "sim"` | `aimm_engine.py` — valor atual: `"não"` |
| GIS completo | GeoPackages de todos os 4 municípios validados | Apenas Manaus disponível (`data/raw/gis/`) |
| Endpoints AIMM internos | `GET /api/indicators`, `GET /api/dashboard` operacionais | AUSENTE em `app.py` |
| Revisão visual humana | Checklist `aimm_visual_review_checklist_seed.csv` com 100% `aprovado` | Todos itens `pendente` |
| Paleta oficial | Paleta documentada em arquivo de design tokens | AUSENTE |
| Validação de token | Token validado por valor (não apenas formato) | `app.py:80–107` valida apenas formato |

NÃO COMPROVADO NO REPOSITÓRIO ANALISADO: critério de aceitação para release MVP além dos itens listados acima.
