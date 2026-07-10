\# Feature Status by Branch (Factual Verification)



\## Dados de entrada

\- Fontes: `.pipeline/branch\_diff\_summary.csv`, `.pipeline/implementation\_grep.txt`

\- Data verificação: 2026-07-10

\- Método: grep + análise de branches + teste de rota



\---



\## Resumo executivo

| Branch | Divergência vs main | Feature principal | Status |

|---|---:|---|---|

| origin/main | 0 | API WB, dashboard, GIS baseline | ✅ PRODUÇÃO |

| origin/copilot/research-aimm-calculator-analysis | 56 | análise crítica calculadora | 🔬 RESEARCH |

| origin/copilot/analise-critica-calculadora-aimm | 55 | análise crítica detalhada | 🔬 RESEARCH |

| origin/copilot/research-interface-calculadora-aimm-fito | 51 | interface UI/ingestão/PDF | 🔬 EXPERIMENTAL |

| origin/copilot/research-data-ingestion-analysis | 23 | ingestão arquivo validação | 🔬 EXPERIMENTAL |

| origin/refactor/phase2 | 15 | refatoração arquitetura | 🔄 PENDING |

| origin/refactor/phase1 | 9 | refatoração camadas | 🔄 PENDING |



\---



\## Detalhamento por feature



\### 1) API World Bank (origin/main — ATIVO PRODUÇÃO)

\*\*Status:\*\* ✅ IMPLEMENTADO E TESTADO  

\*\*Evidência:\*\*

\- Arquivo: `app.py`, linhas 28, 46, 77-256

\- 3 rotas GET: `/worldbank/countries`, `/worldbank/indicators`, `/worldbank/data/{country}/{indicator}`

\- Teste: `run-local.ps1` linhas 166-178; `status-local.ps1` linhas 188-202

\- Autenticação: Bearer token via Caddy gateway

\- Output: JSON



\*\*Limitação:\*\* apenas GET; compatível com benchmark mas não ingere novos dados.



\---



\### 2) Dashboard AIMM (origin/main — ATIVO PRODUÇÃO)

\*\*Status:\*\* ✅ IMPLEMENTADO E GERADO  

\*\*Evidência:\*\*

\- Módulo: `src/fito\_aimm/aimm\_dashboard.py`

\- Workflow: `.github/workflows/aimm\_dashboard.yml`

\- Outputs:

&#x20; - `data/processed/aimm\_dashboard\_cards.csv`

&#x20; - `data/processed/aimm\_dashboard\_dimension\_view.csv`

&#x20; - `outputs/reports/aimm\_executive\_summary.md`

&#x20; - `outputs/reports/aimm\_dashboard\_payload.json`

\- Comunicação: `src/fito\_aimm/aimm\_communication.py` gera HTML/SVG/Mermaid editáveis



\*\*Limitação:\*\* painel estático, não interativo; scores preliminares apenas.



\---



\### 3) Ingestão de arquivos (branches copilot/research-data-ingestion-analysis — EXPERIMENTAL)

\*\*Status:\*\* 🔬 EXPERIMENTAL — Manifesto controlado (não upload web)  

\*\*Evidência:\*\*

\- Script: `scripts/rodada\_4\_28\_file\_ingestion\_validator.py`

\- Workflow: `.github/workflows/rodada\_4\_28\_file\_ingestion\_validator.yml`

\- Formato aceito: CSV (via manifesto `data/manual/aimm\_file\_ingestion\_manifest\_seed.csv`)

\- PDF: ✅ suporte detectado (linhas 47, 266-291, `from pypdf import PdfReader`)

\- Output: validação + registry



\*\*Limitação:\*\* ingestão por manifesto e validação local, não upload direto via navegador; PDF apenas para extração de texto.



\---



\### 4) Mapeamento de indicadores WB (docs/AIMM\_WB\_MAPPING\_MATRIX.csv — PARCIAL)

\*\*Status:\*\* 🟡 PARCIAL — Matriz de decisão, não pipeline automático  

\*\*Evidência:\*\*

\- Arquivo: `docs/AIMM\_WB\_MAPPING\_MATRIX.csv` (template + log de decisão)

\- Colunas: categoria\_aimm, id\_aimm, codigo\_wb, status (Revisar/Mapeado/Rejeitado)

\- Workflow suportado: manual + decisão log



\*\*Limitação:\*\* sem normalização automática; decisões manuais por revisor.



\---



\### 5) GIS Manaus baseline (origin/main — ATIVO, origin/refactor/phase2 — PARCIAL)

\*\*Status:\*\* ✅ BASELINE VALIDADO (main); 🟡 EXPERIMENTAL refactor  

\*\*Evidência:\*\*

\- GeoPackage: `data/raw/gis/municipio\_manaus\_1302603.gpkg`

\- Workflow validação: `rodada\_4\_22\_b2\_gis\_manaus\_isolated\_validate.py`

\- Join visual QGIS: confirmado em 4.22-D

\- Output: `data/processed/gis/gis\_\*.csv` + relatórios



\*\*Limitação:\*\* Manaus apenas; join visual fora do pipeline automático (QGIS manual).



\---



\### 6. Relatórios e visualizações (origin/main — ATIVO PRODUÇÃO)

\*\*Status:\*\* ✅ IMPLEMENTADO  

\*\*Outputs obrigatórios em `outputs/reports/`:\*\*

\- `RELATORIO\_EXECUTIVO\_AIMM\_4\_35.md` (score preliminar)

\- `RELATORIO\_TECNICO\_PROFISSIONAL\_AIMM\_4\_37.md` (técnico)

\- `RELATORIO\_TECNICO\_PROFISSIONAL\_IFC\_AIMM\_4\_38.md` (final IFC)

\- `GUIA\_USO\_FINAL\_IFC\_AIMM\_4\_38.md` (operacional)



\*\*Visualizações editáveis em `outputs/visuals/`:\*\*

\- `aimm\_dashboard\_executivo.html` (painel HTML autocontido)

\- `aimm\_dashboard\_cards.svg` (cards SVG editável)

\- `aimm\_dashboard\_flow.mmd` (fluxo Mermaid)



\---



\## Gaps críticos de operabilidade para MVP



| Gap | Severidade | Ação recomendada |

|---|---:|---|

| Sem endpoint GET `/api/indicators?filtro=` | Alta | criar em branch feature/api-indicators |

| Sem endpoint POST `/api/upload` (web) | Alta | criar widget em 4.37/4.38 + drag-drop |

| Sem normalização automática WB↔AIMM | Média | automatizar rodada\_4\_29 |

| Sem painel interativo (web) | Média | começar com Plotly/Dash em refactor/phase3 |

| GIS além de Manaus | Média | criar template genérico em rodada futura |



\---



\## Conclusão

\- \*\*Produção:\*\* API WB, dashboard, relatórios, baseline GIS Manaus

\- \*\*Experimental:\*\* ingestão arquivo (manifesto), mapeamento WB (decisão log)

\- \*\*Ausente:\*\* interface web interativa, upload drag-drop, normalização automática

