# Fito+ Amazônia — Calculadora AIMM Adaptada

Este repositório consolida módulos, dados e automações para a Calculadora AIMM Adaptada aplicada a cadeias de valor de plantas medicinais, fitoterápicos e produtos herbais em saúde.

## 1) Escopo atual do repositório (factual)

Com base no inventário real de arquivos (`git ls-files` + listagem local), o projeto contém:

- Backend Python (`app.py`) com execução local via scripts PowerShell/CMD
- Gateway local com Caddy (`Caddyfile`, `Caddyfile.local`)
- Módulos de negócio em `src/fito_aimm/`
- Catálogos e seeds em `data/reference/`
- Evidências e insumos manuais em `data/evidence/` e `data/manual/`
- Artefatos processados e relatórios em `data/processed/wb/` e `docs/`
- Pipelines e validações em `scripts/` (incluindo suíte `scripts/wb/`)
- Workflows GitHub Actions extensivos em `.github/workflows/`
- Documentação operacional e técnica em múltiplos `.md` no root e em `docs/`

## 2) Estrutura principal (confirmada)

```text
.
├─ .github/workflows/
├─ config/
├─ data/
│  ├─ evidence/
│  ├─ manual/
│  │  ├─ aimm/
│  │  └─ gis/
│  ├─ processed/
│  │  └─ wb/
│  ├─ raw/
│  │  └─ gis/
│  └─ reference/
├─ docs/
├─ logs/
├─ scripts/
│  └─ wb/
├─ src/
│  └─ fito_aimm/
├─ tmp/
├─ app.py
├─ Caddyfile
├─ Caddyfile.local
├─ README.md
├─ README-local.md
├─ README_operacional.md
├─ run-local.ps1
├─ run-tests-local.ps1
├─ status-local.ps1
└─ stop-local.ps1
```

## 3) Componentes e arquitetura operacional

### 3.1 Fluxo local
1. Cliente faz requisição HTTP
2. Gateway Caddy recebe na porta `8080`
3. Gateway encaminha para backend Python/Flask na porta `8000`
4. Backend processa módulos AIMM e integrações externas conforme configuração

### 3.2 Arquivos-chave de runtime
- `app.py`
- `Caddyfile`
- `Caddyfile.local`
- `run-local.ps1`
- `status-local.ps1`
- `stop-local.ps1`
- `run-tests-local.ps1`
- `Iniciar-API.cmd`
- `Parar-API.cmd`

## 4) Módulos Python (confirmados em `src/fito_aimm/`)

- `aimm_communication.py`
- `aimm_dashboard.py`
- `aimm_engine.py`
- `benchmark_proxy.py`
- `budget_components.py`
- `calculator_architecture.py`
- `coletor_ibge.py`
- `coletor_ibge_geociencias.py`
- `coletor_mapaosc.py`
- `pre_diligencia_consolidacao.py`
- `pre_diligencia_manual_validator.py`
- `pre_diligencia_osc.py`
- `product_pathway.py`
- `risk_osc.py`
- `risk_osc_diagnostics.py`
- `species_selection.py`
- `system_freeze_index.py`
- `sincroniza_drive.py`
- além de módulos-base: `buscador.py`, `extrator.py`, `normalizador.py`, `conferidor.py`

## 5) Dados e catálogos (confirmados)

### 5.1 Referência e governança de dados
- `data/reference/source_registry.csv`
- `data/reference/dicionario_indicadores.csv`
- `data/reference/query_plan.csv`
- `data/reference/sidra_query_catalog.csv`
- `data/reference/geociencias_query_catalog.csv`
- `data/reference/mapaosc_query_catalog.csv`
- dezenas de seeds de dimensão, scoring, species, benchmark, risco, trilha operacional

### 5.2 Evidências e insumos
- `data/evidence/evidence_registry.csv`
- `data/manual/aimm/*.csv`
- `data/manual/gis/*.csv`
- `data/raw/gis/municipio_manaus_1302603.gpkg`

### 5.3 Processados e relatórios WB (confirmados localmente)
- `data/processed/wb/indicator_metadata.csv`
- `data/processed/wb/reports/*.log`
- `data/processed/wb/reports/MAPPING_CHECK_REPORT.md`
- backups em `data/processed/wb/backups/`

## 6) Scripts e automações (confirmados)

### 6.1 Scripts de pipeline/rodadas
- série `scripts/rodada_4_19_*` até `scripts/rodada_4_38_*`

### 6.2 Testes e validações por módulo
- `scripts/testar_*.py` (múltiplos domínios)
- `scripts/validar_bases.py`
- `scripts/test_api_integration.ps1`
- `scripts/teste_funcional_query_plan.py`

### 6.3 Suíte WB (PowerShell)
- `scripts/wb/preflight.ps1`
- `scripts/wb/fetch-indicator-metadata.ps1`
- `scripts/wb/run-mapping-pipeline.ps1`
- `scripts/wb/build-mapping-check-report.ps1`
- `scripts/wb/rotate-artifacts.ps1`
- `scripts/wb/validate-indicator-code.ps1`

## 7) GitHub Actions (confirmados)

Há workflows por domínio em `.github/workflows/`, incluindo:

- motores AIMM (`aimm_engine.yml`, `aimm_dashboard.yml`, etc.)
- módulos de risco, due diligence e pathway
- workflows de rodadas 4.19 a 4.38
- validação de bases (`validar_bases.yml`)
- integração com Drive (`validate-drive-access.yml`, `validate-drive-secrets.yml`)
- publicação Pages (`pages.yml`)

## 8) Execução local (comando oficial)

> Comando oficial de execução local: `.\run-local.ps1`

```powershell
.\run-local.ps1
.\status-local.ps1
.\run-tests-local.ps1
.\stop-local.ps1
```

Fallbacks disponíveis:
- `python app.py`
- `Iniciar-API.cmd` / `Parar-API.cmd`

## 9) Checklist de pré-execução (operacional)

- [ ] Python instalado e ambiente virtual pronto
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] `.env` criado a partir de `.env.example`
- [ ] Portas 8000/8080 livres
- [ ] Caddy disponível no PATH (`caddy version`)
- [ ] Health endpoint respondendo após subida do ambiente

## 10) Documentação existente (factual)

Arquivos confirmados no repositório:
- `README-local.md`
- `README_operacional.md`
- `AUDIT_FUNCIONALIDADES.md`
- `CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md`
- `DASHBOARD_REFATORACAO.md`
- `REFATORACAO_RESUMO_EXECUTIVO.md`
- `PHASE-CLOSE.md`
- em `docs/`:  
  `AIMM_WB_DECISION_LOG.md`, `AIMM_WB_GAPS.md`,  
  `INTERFACE_INTEGRATION_PLAN.md`, `ROOT_JSON_CLEANUP_REPORT_2026-07-07_22-16-17.md`,  
  `AIMM_WB_MAPPING_MATRIX.csv`, `AIMM_WB_MAPPING_MATRIX_TEMPLATE.csv`, `index.html`

## 11) Observações de consistência (factual do inventário fornecido)

- `tmp/teste-api.txt` aparece no inventário local e versionado.
- Existem artefatos locais não versionados no `git ls-files` (ex.: `.env`, `.venv/`, `logs/`, zips, processados WB) — úteis em runtime, mas devem seguir política de `.gitignore`.
- O README deve ser mantido alinhado ao inventário real (sem links para arquivos inexistentes).

## 12) Próximos passos recomendados

1. Consolidar referência documental (índice único em `docs/`)
2. Publicar política formal de governança de checks/workflows
3. Revisar `.gitignore` para artefatos locais e logs
4. Manter README como “mapa factual” do estado atual do repositório
