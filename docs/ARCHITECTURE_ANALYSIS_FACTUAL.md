# ANÁLISE DE ARQUITETURA E CONDIÇÕES TÉCNICAS — AIMM

## Cabeçalho de rastreabilidade
- Repositório: `https://github.com/dannunesgo-dot/fito-aimm-amazonia`
- Branch: `main`
- Data da análise: 2026-07-10
- Agente: `architecture_analysis` (workflow `architecture-analysis`)
- Método: análise de sintaxe (AST) do código + leitura direta de arquivos de
  configuração. Sem inferência. Eixos Objetivo e Funcionalidades por leitura
  interpretativa com trecho verbatim e citação de arquivo.

## 1. Resumo executivo factual
- Arquitetura em camadas: cliente → gateway Caddy (porta 8080) → backend
  Flask (porta 8000) → módulos de negócio → dados. Fonte: `app.py`, `Caddyfile`.
- 19 módulos de negócio em `src/fito_aimm/` (mais utilitários-base).
- 6 endpoints HTTP internos (Flask), dos quais 4 exigem autenticação Bearer.
- 4 hosts de API externa consumidos (6 URLs distintas): IBGE SIDRA, IBGE
  servicodados, IBGE geoftp, MapaOSC/IPEA. Fonte: código dos coletores.
- World Bank API consumida diretamente pelo backend (`app.py`), não pelos
  módulos.
- Cadeia de dependência confirmada por código: `aimm_engine` → `aimm_dashboard`
  → `aimm_communication` (9 arestas de dependência mapeadas).
- Stack: 9 dependências Python (`requirements.txt`); Python 3.12 nos workflows.
- 3 variáveis de ambiente esperadas (`.env.example`): `API_URL`, `AUTH_PATH`,
  `API_TOKEN`.
- Governança de dados em duas camadas (GitHub × Google Drive), regida por
  `config/system_freeze_rules.yaml`.
- 0 saídas de código órfãs (não publicadas por workflow), conforme agente
  `module_pipeline_audit`.

## 2. Eixo Arquitetura

### 2.1 Camadas e portas (evidência: `app.py`, `Caddyfile`)
| Camada | Componente | Porta | Papel |
|---|---|---|---|
| Gateway | Caddy | 8080 | Recebe requisição, encaminha ao backend |
| Backend | Flask (`app.py`) | 8000 | Processa rotas, chama World Bank, valida Bearer |
| Negócio | `src/fito_aimm/*.py` | — | Motor AIMM, coletores, pré-diligência, risco |
| Dados | `data/` | — | Referência (seeds), processados, evidências |

Fluxo: cliente → `:8080` (Caddy) → `:8000` (Flask) → módulo/integração → resposta.

### 2.2 Grafo de dependência entre módulos (evidência: constantes `OUT_*` × leituras)
Fonte completa: `data/processed/architecture_dependency_graph.csv`.
- `aimm_dashboard` depende de `aimm_engine` (via `aimm_overall_score.csv`,
  `aimm_dimension_scores.csv`, `aimm_indicator_scores.csv`,
  `aimm_blockers_report.csv`, `aimm_engine_validation_report.csv`).
- `aimm_communication` depende de `aimm_dashboard` (via `aimm_dashboard_cards.csv`,
  `aimm_dashboard_dimension_view.csv`, `aimm_executive_summary.csv`,
  `aimm_next_actions.csv`).

Implicação: ordem topológica obrigatória — `aimm_engine` antes de
`aimm_dashboard` antes de `aimm_communication`.

## 3. Eixo Objetivo do sistema
Trecho verbatim (`README.md`, linha 3):
> "Este repositório consolida módulos, dados e automações para a Calculadora
> AIMM Adaptada aplicada a cadeias de valor de plantas medicinais,
> fitoterápicos e produtos herbais em saúde."

Contexto do projeto (`config/projeto_fito_amazonia.yaml`):
- Territórios: Manaus/AM, Benjamin Constant/AM, Belém/PA, Santarém/PA.
- Bioma: Amazônia. Investimento total: R$ 80.000.000,00.
- Horizonte: implantação 3 anos, avaliação 5 anos, impacto 10 anos.

## 4. Eixo APIs

### 4.1 APIs externas consumidas (evidência: código dos coletores)
| Host | URL | Módulo consumidor | Estado |
|---|---|---|---|
| IBGE SIDRA | apisidra.ibge.gov.br/values | coletor_ibge, coletor_ibge_geociencias | NÃO VERIFICADA¹ |
| IBGE servicodados | servicodados.ibge.gov.br/api/v1/localidades | coletor_ibge | NÃO VERIFICADA¹ |
| IBGE geoftp | geoftp.ibge.gov.br/.../AR_BR_...2025.xls | coletor_ibge_geociencias | NÃO VERIFICADA¹ |
| MapaOSC/IPEA | mapaosc.ipea.gov.br/download/...baseDivulgacao.csv | coletor_mapaosc | NÃO VERIFICADA¹ |
| MapaOSC/IPEA | mapaosc.ipea.gov.br/.../dicionario-...xlsx | coletor_mapaosc | NÃO VERIFICADA¹ |
| World Bank | api.worldbank.org/v2 | app.py (backend) | REQUER verificação² |

¹ Estado não verificado por este agente em modo estático; verificar em runtime
com rede.
² World Bank é consumida pelo backend Flask, não pelos módulos; ver endpoints.

### 4.2 Endpoints internos Flask (evidência: `app.py`)
| Rota | Método | Autenticação Bearer |
|---|---|---|
| `/` | GET | não |
| `/health` | GET | não |
| `/worldbank/countries` | GET | sim |
| `/worldbank/indicators` | GET | sim |
| `/worldbank/data/<country>/<indicator>` | GET | sim |
| `/test` | GET | sim |

## 5. Eixo Funcionalidades (por módulo de negócio)
Descrição da capacidade real, cruzada com `module_pipeline_inventory.csv`:
- **aimm_engine** — motor de cálculo AIMM: produz scores por dimensão/indicador,
  relatório de bloqueadores e validação. Produtor primário da cadeia.
- **aimm_dashboard** — consome scores do engine; gera cartões, visão por
  dimensão, resumo executivo e próximas ações.
- **aimm_communication** — consome saídas do dashboard; camada de comunicação
  visual/executiva.
- **coletor_ibge / coletor_ibge_geociencias** — coleta populacional e territorial
  do IBGE (SIDRA, servicodados, geoftp).
- **coletor_mapaosc** — coleta e triagem de Organizações da Sociedade Civil
  (OSCs) da base MapaOSC/IPEA.
- **pre_diligencia_osc / _consolidacao / _manual_validator** — cadeia de
  pré-diligência de OSCs: fila de contato, consolidação, validação manual.
- **risk_osc / risk_osc_diagnostics** — triagem e diagnóstico de risco de OSCs.
- **species_selection** — seleção de espécies.
- **product_pathway** — trilha de produto.
- **budget_components** — componentes de orçamento.
- **benchmark_proxy** — proxy de benchmark.
- **calculator_architecture** — arquitetura da calculadora.
- **system_freeze_index** — congelamento técnico e índice mestre de artefatos.
- **module_pipeline_audit** — auditoria de completude dos módulos.
- **architecture_analysis** — este agente.

## 6. Eixo Condições técnicas e estruturais

### 6.1 Stack (evidência: `requirements.txt`)
requests, pydantic, python-dotenv, PyYAML, beautifulsoup4, lxml, pandas, xlrd,
openpyxl. Python 3.12 nos workflows.

### 6.2 Requisitos de execução
- Portas 8000 (backend) e 8080 (gateway) livres.
- Caddy disponível no PATH.
- Variáveis de ambiente (`.env.example`): `API_URL`, `AUTH_PATH`, `API_TOKEN`.
- Execução local: `run-local.ps1`; fallback `python app.py`.

### 6.3 Governança de dados (evidência: `config/system_freeze_rules.yaml`)
- GitHub: código Python, workflows, YAML, schemas/CSV leves, README.
- Google Drive: ZIPs integrais, bases brutas/processadas, evidências, logs.
- Registro de fontes: `data/reference/source_registry.csv`.

## 7. Riscos técnicos e pendências
- Dependência de artefato manual em parte da pré-diligência (validação humana).
- Cadeia de pipeline exige ordem topológica; quebra se produtor não roda antes.
- Estado das APIs externas não verificado em modo estático — recomenda-se
  verificação periódica em runtime (as URLs do IBGE/MapaOSC podem mudar por
  atualização de base, ex.: a base MapaOSC traz data no nome do arquivo).
- Backend expõe World Bank; integração das demais APIs ocorre nos módulos, não
  via endpoint HTTP — arquitetura híbrida (API HTTP + pipelines batch).
