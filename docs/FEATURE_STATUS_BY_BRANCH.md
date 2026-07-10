# Feature Status by Branch (Factual Verification)

## Dados de entrada
- Fontes: `.pipeline/branch_diff_summary.csv`, `.pipeline/implementation_grep.txt`
- Data verificação: 2026-07-10
- Método: grep + análise de branches + teste de rota

---

## Resumo executivo
| Branch | Divergência vs main | Feature principal | Status |
|---|---:|---|---|
| origin/main | 0 | API WB, dashboard, GIS baseline | ✅ PRODUÇÃO |
| origin/copilot/research-aimm-calculator-analysis | 56 | análise crítica calculadora | 🔬 RESEARCH |
| origin/copilot/analise-critica-calculadora-aimm | 55 | análise crítica detalhada | 🔬 RESEARCH |
| origin/copilot/research-interface-calculadora-aimm-fito | 51 | interface UI/ingestão/PDF | 🔬 EXPERIMENTAL |
| origin/copilot/research-data-ingestion-analysis | 23 | ingestão arquivo validação | 🔬 EXPERIMENTAL |
| origin/refactor/phase2 | 15 | refatoração arquitetura | 🔄 PENDING |
| origin/refactor/phase1 | 9 | refatoração camadas | 🔄 PENDING |

---

## Detalhamento por feature

### 1) API World Bank (origin/main — ATIVO PRODUÇÃO)
**Status:** ✅ IMPLEMENTADO E TESTADO  
**Evidência:**
- Arquivo: `app.py`, linhas 28, 46, 77-256
- 3 rotas GET: `/worldbank/countries`, `/worldbank/indicators`, `/worldbank/data/{country}/{indicator}`
- Teste: `run-local.ps1` linhas 166-178; `status-local.ps1` linhas 188-202
- Autenticação: Bearer token via Caddy gateway
- Output: JSON

**Limitação:** apenas GET; compatível com benchmark mas não ingere novos dados.

---

### 2) Dashboard AIMM (origin/main — ATIVO PRODUÇÃO)
**Status:** ✅ IMPLEMENTADO E GERADO  
**Evidência:**
- Módulo: `src/fito_aimm/aimm_dashboard.py`
- Workflow: `.github/workflows/aimm_dashboard.yml`
- Outputs:
  - `data/processed/aimm_dashboard_cards.csv`
  - `data/processed/aimm_dashboard_dimension_view.csv`
  - `outputs/reports/aimm_executive_summary.md`
  - `outputs/reports/aimm_dashboard_payload.json`
- Comunicação: `src/fito_aimm/aimm_communication.py` gera HTML/SVG/Mermaid editáveis

**Limitação:** painel estático, não interativo; scores preliminares apenas.

---

### 3) Ingestão de arquivos (branches copilot/research-data-ingestion-analysis — EXPERIMENTAL)
**Status:** 🔬 EXPERIMENTAL — Manifesto controlado (não upload web)  
**Evidência:**
- Script: `scripts/rodada_4_28_file_ingestion_validator.py`
- Workflow: `.github/workflows/rodada_4_28_file_ingestion_validator.yml`
- Formato aceito: CSV (via manifesto `data/manual/aimm_file_ingestion_manifest_seed.csv`)
- PDF: ✅ suporte detectado (linhas 47, 266-291, `from pypdf import PdfReader`)
- Output: validação + registry

**Limitação:** ingestão por manifesto e validação local, não upload direto via navegador; PDF apenas para extração de texto.

---

### 4) Mapeamento de indicadores WB (docs/AIMM_WB_MAPPING_MATRIX.csv — PARCIAL)
**Status:** 🟡 PARCIAL — Matriz de decisão, não pipeline automático  
**Evidência:**
- Arquivo: `docs/AIMM_WB_MAPPING_MATRIX.csv` (template + log de decisão)
- Colunas: categoria_aimm, id_aimm, codigo_wb, status (Revisar/Mapeado/Rejeitado)
- Workflow suportado: manual + decisão log

**Limitação:** sem normalização automática; decisões manuais por revisor.

---

### 5) GIS Manaus baseline (origin/main — ATIVO, origin/refactor/phase2 — PARCIAL)
**Status:** ✅ BASELINE VALIDADO (main); 🟡 EXPERIMENTAL refactor  
**Evidência:**
- GeoPackage: `data/raw/gis/municipio_manaus_1302603.gpkg`
- Workflow validação: `rodada_4_22_b2_gis_manaus_isolated_validate.py`
- Join visual QGIS: confirmado em 4.22-D
- Output: `data/processed/gis/gis_*.csv` + relatórios

**Limitação:** Manaus apenas; join visual fora do pipeline automático (QGIS manual).

---

### 6. Relatórios e visualizações (origin/main — ATIVO PRODUÇÃO)
**Status:** ✅ IMPLEMENTADO  
**Outputs obrigatórios em `outputs/reports/`:**
- `RELATORIO_EXECUTIVO_AIMM_4_35.md` (score preliminar)
- `RELATORIO_TECNICO_PROFISSIONAL_AIMM_4_37.md` (técnico)
- `RELATORIO_TECNICO_PROFISSIONAL_IFC_AIMM_4_38.md` (final IFC)
- `GUIA_USO_FINAL_IFC_AIMM_4_38.md` (operacional)

**Visualizações editáveis em `outputs/visuals/`:**
- `aimm_dashboard_executivo.html` (painel HTML autocontido)
- `aimm_dashboard_cards.svg` (cards SVG editável)
- `aimm_dashboard_flow.mmd` (fluxo Mermaid)

---

## Gaps críticos de operabilidade para MVP

| Gap | Severidade | Ação recomendada |
|---|---:|---|
| Sem endpoint GET `/api/indicators?filtro=` | Alta | criar em branch feature/api-indicators |
| Sem endpoint POST `/api/upload` (web) | Alta | criar widget em 4.37/4.38 + drag-drop |
| Sem normalização automática WB↔AIMM | Média | automatizar rodada_4_29 |
| Sem painel interativo (web) | Média | começar com Plotly/Dash em refactor/phase3 |
| GIS além de Manaus | Média | criar template genérico em rodada futura |

---

## Conclusão
- **Produção:** API WB, dashboard, relatórios, baseline GIS Manaus
- **Experimental:** ingestão arquivo (manifesto), mapeamento WB (decisão log)
- **Ausente:** interface web interativa, upload drag-drop, normalização automática
