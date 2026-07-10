# UI Municipal Coverage Gaps — Auditoria Factual AIMM

> **Data da auditoria:** 2026-07-10  
> **Branch base:** `main`  
> **Municípios auditados:** Manaus (1302603), Benjamin Constant (1300607), Belém (1501402), Santarém (1506807)  
> **Método:** leitura direta de código-fonte, configs, seeds e arquivos de dados — sem inferência.

---

## 1. Situação por município

### 1.1 Manaus (IBGE: 1302603 — AM)

| Categoria | Status | Arquivo / Linha | Observação |
|---|---|---|---|
| Código IBGE registrado no projeto | IMPLEMENTADO | `src/fito_aimm/coletor_ibge.py:18` | `"1302603": {"municipio": "Manaus", "uf": "AM"}` |
| GeoPackage municipal | IMPLEMENTADO | `data/raw/gis/municipio_manaus_1302603.gpkg` | Arquivo presente e validado em Rodada 4.22-B2 |
| Join visual QGIS | IMPLEMENTADO | `docs/FEATURE_STATUS_BY_BRANCH.md` (seção GIS Manaus) | Validado manualmente; fora do pipeline automático |
| Coleta IBGE SIDRA (população) | PARCIAL | `src/fito_aimm/coletor_ibge.py:115–120` | URL parametrizada; execução depende de workflow ativo |
| Coleta IBGE localidades | PARCIAL | `src/fito_aimm/coletor_ibge.py:279–310` | Endpoint configurado; execução depende de workflow ativo |
| Contrato canônico — exemplo de payload | IMPLEMENTADO | `docs/contracts/indicator_examples.json:10–35` | Exemplo `IBGE_POP_1302603` presente com série histórica |
| GIS baseline (camadas adicionais) | PARCIAL | `data/reference/gis_baseline_control_seed.csv:MUN_001` | Status `pendente_gis` para camadas além do polígono municipal |
| Score AIMM territorial | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO — score por município não implementado |

### 1.2 Benjamin Constant (IBGE: 1300607 — AM)

| Categoria | Status | Arquivo / Linha | Observação |
|---|---|---|---|
| Código IBGE registrado no projeto | IMPLEMENTADO | `src/fito_aimm/coletor_ibge.py:19` | `"1300607": {"municipio": "Benjamin Constant", "uf": "AM"}` |
| GeoPackage municipal | AUSENTE | `data/raw/gis/` | Nenhum arquivo `.gpkg` para Benjamin Constant encontrado |
| Join visual QGIS | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |
| Coleta IBGE SIDRA (população) | PARCIAL | `src/fito_aimm/coletor_ibge.py:115–120` | Código IBGE incluído no loop; arquivo de saída não confirmado |
| Coleta IBGE localidades | PARCIAL | `src/fito_aimm/coletor_ibge.py:279–310` | Código IBGE incluído no loop; arquivo de saída não confirmado |
| Contrato canônico — exemplo de payload | IMPLEMENTADO | `docs/contracts/indicator_examples.json:85–105` | Exemplo `IBGE_MUN_1300607` presente (dados de limites IBGE) |
| GIS baseline (camadas adicionais) | AUSENTE | `data/reference/gis_baseline_control_seed.csv:MUN_002` | Status `pendente_gis`; observação: "município preparado sem processamento real" |
| Score AIMM territorial | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |

### 1.3 Belém (IBGE: 1501402 — PA)

| Categoria | Status | Arquivo / Linha | Observação |
|---|---|---|---|
| Código IBGE registrado no projeto | IMPLEMENTADO | `src/fito_aimm/coletor_ibge.py:20` | `"1501402": {"municipio": "Belém", "uf": "PA"}` |
| GeoPackage municipal | AUSENTE | `data/raw/gis/` | Nenhum arquivo `.gpkg` para Belém encontrado |
| Join visual QGIS | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |
| Coleta IBGE SIDRA (população) | PARCIAL | `src/fito_aimm/coletor_ibge.py:115–120` | Código IBGE incluído no loop; arquivo de saída não confirmado |
| Coleta IBGE localidades | PARCIAL | `src/fito_aimm/coletor_ibge.py:279–310` | Código IBGE incluído no loop; arquivo de saída não confirmado |
| Contrato canônico — exemplo de payload | IMPLEMENTADO | `docs/contracts/indicator_examples.json:107–125` | Exemplo `IBGE_MUN_1501402` presente (dados de limites IBGE) |
| GIS baseline (camadas adicionais) | AUSENTE | `data/reference/gis_baseline_control_seed.csv:MUN_003` | Status `pendente_gis`; observação: "município preparado sem processamento real" |
| Score AIMM territorial | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |

### 1.4 Santarém (IBGE: 1506807 — PA)

| Categoria | Status | Arquivo / Linha | Observação |
|---|---|---|---|
| Código IBGE registrado no projeto | IMPLEMENTADO | `src/fito_aimm/coletor_ibge.py:21` | `"1506807": {"municipio": "Santarém", "uf": "PA"}` |
| GeoPackage municipal | AUSENTE | `data/raw/gis/` | Nenhum arquivo `.gpkg` para Santarém encontrado |
| Join visual QGIS | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |
| Coleta IBGE SIDRA (população) | PARCIAL | `src/fito_aimm/coletor_ibge.py:115–120` | Código IBGE incluído no loop; arquivo de saída não confirmado |
| Coleta IBGE localidades | PARCIAL | `src/fito_aimm/coletor_ibge.py:279–310` | Código IBGE incluído no loop; arquivo de saída não confirmado |
| Contrato canônico — exemplo de payload | IMPLEMENTADO | `docs/contracts/indicator_examples.json:128–148` | Exemplo `IBGE_MUN_1506807` presente (dados de limites IBGE) |
| GIS baseline (camadas adicionais) | AUSENTE | `data/reference/gis_baseline_control_seed.csv:MUN_004` | Status `pendente_gis`; observação: "município preparado sem processamento real" |
| Score AIMM territorial | AUSENTE | — | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |

---

## 2. Campos presentes (por município)

### Campos presentes para todos os 4 municípios

| Campo | Fonte no repositório | Arquivo / Linha |
|---|---|---|
| `codigo_ibge` | `MUNICIPIOS_PROJETO` dict | `coletor_ibge.py:18–21` |
| `municipio` (nome) | `MUNICIPIOS_PROJETO` dict | `coletor_ibge.py:18–21` |
| `uf` | `MUNICIPIOS_PROJETO` dict | `coletor_ibge.py:18–21` |
| `bioma` | `config/gis_territory_rules.yaml:territorios_alvo` | `gis_territory_rules.yaml:8–18` |
| Exemplo de payload canônico | `docs/contracts/indicator_examples.json` | linhas 85–148 |
| URLs IBGE SIDRA configuradas | `coletor_ibge.py:115–120` | Template de URL com código do município |
| Entrada no seed de baseline GIS | `data/reference/gis_baseline_control_seed.csv` | MUN_001 a MUN_004 |

### Campos presentes apenas para Manaus

| Campo | Fonte no repositório | Arquivo / Linha |
|---|---|---|
| GeoPackage com polígono municipal | `data/raw/gis/municipio_manaus_1302603.gpkg` | — |
| Join visual QGIS validado | `docs/FEATURE_STATUS_BY_BRANCH.md:seção GIS Manaus` | — |
| `gis_readiness_report` processado | `docs/FEATURE_STATUS_BY_BRANCH.md` | — |

---

## 3. Campos ausentes (por município)

### Ausentes para Benjamin Constant, Belém e Santarém

| Campo ausente | Impacto | Arquivo de referência |
|---|---|---|
| GeoPackage municipal (`*.gpkg`) | Impossibilita processamento GIS: buffers, interseções, centroide, área | `data/reference/gis_baseline_control_seed.csv:GIS_REQ_001` |
| `area_km2` validada | Impede cálculo de densidade populacional e indicador GIS_IND_003 | `gis_baseline_control_seed.csv:GIS_REQ_004` |
| `centroide_lat` / `centroide_lon` | Impede cálculo de distâncias (ICTs, Farmácias Vivas) | `gis_baseline_control_seed.csv:GIS_REQ_004` |
| CRS métrico declarado | Impede cálculos de área, distância e buffer | `config/gis_territory_rules.yaml:crs` |
| Dados de coleta IBGE executados e validados | Payload de população e localidades não confirmado | `coletor_ibge.py:115–120` |
| Camadas OSCs, cooperativas, ICTs, Farmácias Vivas | Impede indicadores de gap institucional e saúde | `gis_indicator_registry_seed.csv:GIS_IND_005–008` |
| Score AIMM territorial por município | Impossibilita comparação territorial entre municípios | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO |

### Ausentes para todos os 4 municípios

| Campo ausente | Impacto | Arquivo de referência |
|---|---|---|
| Dados de cobertura de uso e solo por município | Indicador GIS ambiental ausente | `gis_territory_rules.yaml:camadas_obrigatorias` |
| Hidrografia | Indicador logístico/ambiental ausente | `gis_territory_rules.yaml:camadas_obrigatorias` |
| Vias e logística | Indicador de acesso ausente | `gis_territory_rules.yaml:camadas_obrigatorias` |
| Portos/aeroportos | Indicador logístico ausente | `gis_territory_rules.yaml:camadas_obrigatorias` |
| Unidades de conservação e terras indígenas | Indicador de risco de sobreposição (GIS_IND_009) ausente | `gis_indicator_registry_seed.csv:GIS_IND_009` |
| Endpoint HTTP para dados territoriais | Dados municipais não acessíveis via API | `docs/INTERFACE_ENDPOINTS_TRUTH_TABLE.csv` |

---

## 4. Impacto na interface

| Impacto | Municípios afetados | Severidade |
|---|---|---|
| Mapa interativo impossível para 3 dos 4 municípios | Benjamin Constant, Belém, Santarém | Alta |
| Sem comparação territorial entre municípios no painel | Todos os 4 | Alta |
| Cards de dimensão GIS exibiriam valores nulos ou proxies sem comprovação | Benjamin Constant, Belém, Santarém | Alta |
| Score AIMM territorial bloqueado para todos | Todos os 4 | Alta |
| Tabela de indicadores AIMM não exibirá dados por município específico | Todos os 4 | Média |
| Endpoint de dados territoriais ausente → UI não tem API para consumir | Todos os 4 | Alta |

---

## 5. Ações para fechar lacunas

### Prioridade Alta (bloqueante para MVP)

1. **Baixar GeoPackages de Benjamin Constant, Belém e Santarém**  
   - Fonte: malha municipal IBGE 2023 (download em https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/)  
   - Destino: `data/raw/gis/municipio_benjamin_constant_1300607.gpkg`, `data/raw/gis/municipio_belem_1501402.gpkg`, `data/raw/gis/municipio_santarem_1506807.gpkg`  
   - Gate: arquivo presente, CRS EPSG:4674 confirmado, campo `codigo_ibge` presente  
   - Referência: `data/reference/gis_baseline_control_seed.csv:GIS_REQ_001`

2. **Executar pipeline de coleta IBGE e confirmar arquivos de saída**  
   - Módulo: `src/fito_aimm/coletor_ibge.py`  
   - Saída esperada: `data/raw/ibge/populacao_estimada_municipios.csv`, `data/raw/ibge/localidades_municipios.csv`  
   - Verificar status de todos os 4 municípios nos arquivos de saída  
   - Referência: `coletor_ibge.py:165–180` e `coletor_ibge.py:279–310`

3. **Criar endpoint HTTP para dados municipais**  
   - Criar `GET /api/municipios/{codigo_ibge}` em `app.py` retornando payload canônico por município  
   - Referência: `docs/contracts/indicator_canonical.schema.json`

### Prioridade Média (importante para operabilidade)

4. **Calcular e registrar área, centroide e CRS métrico para cada município**  
   - Após obtenção dos GeoPackages, executar cálculos geométricos  
   - Registrar resultados em `data/reference/gis_baseline_control_seed.csv` campos `campos_obrigatorios`  
   - Referência: `gis_indicator_registry_seed.csv:GIS_IND_002–004`

5. **Levantar camadas complementares para todos os 4 municípios**  
   - Camadas obrigatórias per `config/gis_territory_rules.yaml:camadas_obrigatorias`  
   - Priorizar: `pontos_oscs_cooperativas`, `farmacias_vivas`, `laboratorios_icts`  

### Prioridade Baixa (pós-MVP)

6. **Implementar score AIMM territorial por município**  
   - Hoje apenas score global está implementado (`aimm_engine.py`)  
   - Desagregação territorial requer definição metodológica adicional  
   - NÃO COMPROVADO NO REPOSITÓRIO ANALISADO como requisito já especificado

NÃO COMPROVADO NO REPOSITÓRIO ANALISADO: prazo ou sprint alvo para fechamento das lacunas dos municípios.
