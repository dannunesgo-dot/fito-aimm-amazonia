# Auditoria de Funcionalidades — Fito+ Amazônia AIMM

**Data:** 2026-07-02  
**Escopo:** Análise de estrutura, modelos obsoletos, mal alocados e propostas de refatoração

---

## 📋 Sumário Executivo

O repositório está em **estado arquitetural de transição** entre prototipagem inicial e produção operacional. Há três classes de problemas:

1. **Módulos stub/obsoletos** (5 arquivos de interface não implementada)
2. **Desalinhamento estrutural** (modules duplicados, falta de organização em camadas)
3. **Lacunas funcionais críticas** (falta de tratamento de erros, logging, testes, documentação de API)

---

## 🔴 ARQUIVOS OBSOLETOS OU MAL ALOCADOS

### 1. **Módulos Stub Não Implementados**
| Arquivo | Problema | Gravidade | Recomendação |
|---------|----------|-----------|--------------|
| `src/fito_aimm/buscador.py` | Apenas interface vazia; conectores reais ausentes | **ALTA** | Remover ou mover para `docs/deprecated/`; usar coletores especializados |
| `src/fito_aimm/extrator.py` | Uma única função trivial; nunca usado | **MÉDIA** | Remover ou consolidar em `coletor_*.py` |
| `src/fito_aimm/conferidor.py` | Interface mínima; lógica real está em módulos específicos | **MÉDIA** | Remover ou expandir em `pre_diligencia_manual_validator.py` |
| `src/fito_aimm/normalizador.py` | Apenas 2 funções utilitárias; duplicadas em coletores | **BAIXA** | Mover para `src/fito_aimm/utils/normalization.py` |
| `src/fito_aimm/sincroniza_drive.py` | Placeholder com `NotImplementedError`; Drive API real em scripts | **ALTA** | Remover; implementar em `scripts/` ou novo módulo `drive_sync.py` |

---

### 2. **Desalinhamento de Arquitetura**

#### Problema: Lógica duplicada em coletores
- **`coletor_mapaosc.py`** (626 linhas) contém **toda** a lógica de normalização, triagem e pontuação
- Deveria delegar para módulos separados: `clasificador.py`, `normalizador.py`, `pontuador.py`
- **Impacto:** Difícil manutenção; lógica de business não reutilizável

#### Problema: Scripts de operação misturados
- `scripts/rodada_4_*.py` são **operacionais** (devem ser de teste/exemplo)
- `scripts/testar_*.py` são **testes**, mas sem pytest; sem fixtures; sem mocking
- **Estrutura ideal:**
  ```
  tests/
    ├─ unit/
    │   ├─ test_aimm_engine.py
    │   ├─ test_coletor_mapaosc.py
    │   └─ ...
    ├─ integration/
    │   └─ test_pipeline_end_to_end.py
    └─ conftest.py  (fixtures compartilhadas)
  
  scripts/
    ├─ examples/
    │   └─ rodada_4_32_exemplo.py
    └─ operational/
        ├─ sync_drive.py
        ├─ run_pipeline.py
        └─ ...
  ```

#### Problema: Configuração fragmentada
- YAML rules espalhados em `config/` (25 arquivos; confuso)
- Falta schema de validação
- Falta documentação de quais rules se aplicam a quais módulos
- **Solução:** Criar `src/fito_aimm/config_schema.py` + consolidar em `config/schema/`

---

## 🟡 PROBLEMAS FUNCIONAIS

### 1. **Módulo AIMM Engine (aimm_engine.py)**

#### ✅ Pontos fortes
- Validação estrutural clara (função `validate_inputs`)
- Cálculo de scores bem documentado
- Rastreabilidade de evidências

#### ⚠️ Deficiências
| Problema | Localização | Impacto | Solução |
|----------|-------------|--------|---------|
| **Linha 250:** Trecho truncado em f-string | `generate_evidence()` | Produz CSV inválida | Truncar string dinamicamente ou usar `textwrap` |
| **Sem tratamento de divisão por zero** | `calculate_dimension_scores()` L155 | Crash silencioso se `members` vazio | Adicionar `else: avg = 0.0` (já feito em L152, mas não testado) |
| **Score final bloqueado em hardcoded** | L197-198 | Nunca libera score mesmo em sucesso | Fazer `pode_ser_usado_como_score_final` dinâmico |
| **Falta de logging** | Todo | Difícil debugging em produção | Adicionar `logging` em cada função crítica |
| **Sem testes** | N/A | Não há garantia de correção | Criar `tests/unit/test_aimm_engine.py` |

---

### 2. **Módulo Coletor MapaOSC (coletor_mapaosc.py)**

#### ✅ Pontos fortes
- Retry com backoff exponencial (linhas 125-178)
- Detecção automática de encoding/delimitador
- Classificação inteligente com scoring

#### ⚠️ Deficiências
| Problema | Localização | Impacto | Solução |
|----------|-------------|--------|---------|
| **Monolítica (626 linhas)** | Toda | Difícil testar partes isoladas | Dividir em `clasificador.py`, `normalizer.py`, `fetcher.py` |
| **Função `classificar_organizacao()` está em 40+ linhas** | L284-327 | Lógica de negócio enterrada | Extrair para `src/fito_aimm/scoring/osc_classifier.py` |
| **Hard-coded MUNICIPIOS_PROJETO** | L28-33 | Não escalável a outros territórios | Mover para `config/territorios.yaml` + loader |
| **Linha 464:** Trecho truncado | `gerar_evidencias_mapaosc()` | CSV truncada | Usar `textwrap.fill()` |
| **Sem tratamento de arquivo corrompido** | L512-530 | Pode falhar silenciosamente | Adicionar validação pós-leitura |

---

### 3. **Falta de Camada de Validação**

Não existe validador genérico de schemas. Cada módulo reinventa a roda:

```python
# Atualmente
def validate_inputs(inputs, dim_policy, blockers, rules):
    if policy_dims != valid_dims:
        errors.append(...)

# Deveria ser
from src.fito_aimm.validators import SchemaValidator

validator = SchemaValidator(schema_file="config/schemas/aimm_inputs.json")
errors = validator.validate(inputs)
```

---

## 🟢 PROPOSTAS DE REFATORAÇÃO

### **FASE 1: Limpeza Imediata (1-2 semanas)**

#### 1.1 Remover/Arquivar módulos obsoletos
```bash
# Criar pasta de deprecated
mkdir -p docs/deprecated

# Mover
mv src/fito_aimm/buscador.py docs/deprecated/
mv src/fito_aimm/extrator.py docs/deprecated/
mv src/fito_aimm/conferidor.py docs/deprecated/
mv src/fito_aimm/sincroniza_drive.py docs/deprecated/

# Atualizar src/fito_aimm/__init__.py para remover imports
```

#### 1.2 Consolidar normalizadores
```python
# src/fito_aimm/utils/normalization.py
def por_milhao(valor: float, investimento: float) -> float:
    """Calcula proporção por milhão."""
    if investimento <= 0:
        raise ValueError("Investimento deve ser > 0")
    return valor / (investimento / 1_000_000)

def percentual(parte: float, total: float) -> float:
    """Calcula percentual com proteção contra divisão por zero."""
    if total == 0:
        return 0.0
    return parte / total

def normalizar_texto(texto: str, remover_acentos: bool = True) -> str:
    """Normaliza texto para comparação."""
    import unicodedata
    import re
    texto = str(texto or "").lower().strip()
    if remover_acentos:
        texto = "".join(
            c for c in unicodedata.normalize("NFKD", texto)
            if not unicodedata.combining(c)
        )
    return re.sub(r"\s+", " ", texto)
```

#### 1.3 Consertar strings truncadas
```python
# aimm_engine.py L250 — ANTES
"trecho_original_ou_descricao": f"Indicadores processados: {len(indicator_scores)}; dimensões: {len(dimension_scores)}; bloqueios: {len(blockers)}; score estrutural preliminar: {overall.[...]

# DEPOIS
"trecho_original_ou_descricao": (
    f"Indicadores processados: {len(indicator_scores)}; "
    f"dimensões: {len(dimension_scores)}; "
    f"bloqueios: {len(blockers)}; "
    f"score estrutural preliminar: {overall.get('score_estrutural_preliminar', 'N/A')}"
)
```

---

### **FASE 2: Refatoração Arquitetural (2-3 semanas)**

#### 2.1 Criar camadas de validação e esquema
```
src/fito_aimm/
├── validators/
│   ├── __init__.py
│   ├── schema_validator.py      # Validador genérico JSON/Pydantic
│   ├── aimm_validator.py        # Regras específicas AIMM
│   └── csv_validator.py         # Validação de CSVs
├── models/
│   ├── __init__.py
│   ├── aimm_models.py           # Pydantic models para indicadores, dimensões
│   ├── osc_models.py            # Modelos de OSC/organizações
│   └── evidence_models.py       # Modelo genérico de evidência
└── config/
    ├── __init__.py
    └── config_loader.py         # Carrega e valida YAML
```

#### 2.2 Dividir módulos monolíticos
```
src/fito_aimm/
├── scoring/
│   ├── __init__.py
│   ├── osc_classifier.py        # Classificação e pontuação de OSCs
│   ├── dimension_aggregator.py  # Agregação de dimensões
│   └── overall_calculator.py    # Cálculo de score final
├── fetchers/
│   ├── __init__.py
│   ├── base_fetcher.py          # Classe base para coletores
│   ├── mapaosc_fetcher.py       # Refactor de coletor_mapaosc.py
│   ├── ibge_fetcher.py
│   └── gis_fetcher.py
└── normalizers/
    ├── __init__.py
    ├── text_normalizer.py
    ├── encoding_detector.py
    └── delimiter_detector.py
```

#### 2.3 Estruturar testes apropriadamente
```
tests/
├── conftest.py                  # Fixtures pytest
├── unit/
│   ├── test_validators.py
│   ├── test_aimm_engine.py
│   ├── test_osc_classifier.py
│   ├── test_normalizers.py
│   └── test_fetchers.py
├── integration/
│   ├── test_pipeline_e2e.py
│   └── test_drive_integration.py
├── fixtures/
│   ├── sample_inputs.csv
│   ├── sample_mapaosc.csv
│   └── sample_rules.yaml
└── README_TESTS.md
```

---

### **FASE 3: Integração e Documentação (1-2 semanas)**

#### 3.1 Criar arquivo de mapeamento modular

**`ARCHITECTURE.md`**
```markdown
# Arquitetura Fito+ Amazônia AIMM

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                      │
├──────────────────┬─────────────────┬───────────────────────┤
│ MapaOSC Fetcher  │  IBGE Fetcher   │   GIS Fetcher        │
│ coletor_mapaosc  │  coletor_ibge   │   (gis processing)   │
└────────┬─────────┴────────┬────────┴───────────┬───────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   NORMALIZATION LAYER                        │
│  (encoding detection, delimiter detection, text normalizing) │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                  VALIDATION LAYER                            │
│ (SchemaValidator, CSVValidator, BusinessRuleValidator)      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                ENRICHMENT LAYER                              │
│  (Risk scoring, classification, feature extraction)         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                 CALCULATION LAYER (AIMM Engine)             │
│  (Indicator scoring, dimension aggregation, overall score)  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│               OUTPUT / EVIDENCE LAYER                        │
│  (CSV export, evidence recording, report generation)        │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│            SYNCHRONIZATION LAYER (Drive + GitHub)           │
│  (OAuth upload, webhook notifications)                      │
└─────────────────────────────────────────────────────────────┘
```

## Módulos Recomendados Após Refatoração

### Tier 1: Core (nunca muda)
- `src/fito_aimm/models/` — Pydantic models
- `src/fito_aimm/validators/` — Regras de validação
- `src/fito_aimm/config/` — Carregamento de configuração

### Tier 2: Business Logic (muda por iteração)
- `src/fito_aimm/scoring/` — Lógica de cálculo
- `src/fito_aimm/enrichment/` — Processamento de dados
- `src/fito_aimm/fetchers/` — Coletores de dados

### Tier 3: Infrastructure (pode trocar)
- `src/fito_aimm/drive_sync/` — Sincronização com Drive
- `src/fito_aimm/github_integration/` — Integração GitHub
- `src/fito_aimm/logging/` — Logging e observabilidade

### Tier 4: Scripts (apenas exemplos/operação)
- `scripts/examples/` — Exemplos de uso
- `scripts/operational/` — Scripts de operação manual
```

#### 3.2 Adicionar documentação de API

**`src/fito_aimm/README.md`**
```markdown
# Módulos Fito+ Amazônia

## Uso Rápido

```python
from src.fito_aimm.fetchers import MapaOSCFetcher
from src.fito_aimm.validators import SchemaValidator
from src.fito_aimm.aimm_engine import execute_aimm_engine

# Buscar dados
fetcher = MapaOSCFetcher()
result = fetcher.fetch_municipios()

# Validar
validator = SchemaValidator("config/schemas/organizacoes.json")
errors = validator.validate(result)

# Calcular
score = execute_aimm_engine()
```

## Modelos Disponíveis

- `AIMMIndicator` — Indicador AIMM
- `AIMMDimension` — Dimensão AIMM
- `OSCOrganizacao` — Organização (OSC/cooperativa/associação)
- `Evidence` — Registro de evidência
```

---

## 📊 Checklist de Implementação

### FASE 1 (Semana 1)
- [ ] Remover 5 módulos obsoletos → `docs/deprecated/`
- [ ] Consolidar `normalizador.py` em `utils/`
- [ ] Consertar strings truncadas em `aimm_engine.py` e `coletor_mapaosc.py`
- [ ] Adicionar `__init__.py` se falta em `src/fito_aimm/`
- [ ] Criar branch `refactor/architecture` para PR

### FASE 2 (Semanas 2-3)
- [ ] Criar `src/fito_aimm/validators/` + `SchemaValidator`
- [ ] Criar `src/fito_aimm/models/` com Pydantic models
- [ ] Dividir `coletor_mapaosc.py` em 3 módulos
- [ ] Criar `tests/` com estrutura pytest
- [ ] Adicionar `conftest.py` com fixtures

### FASE 3 (Semana 4)
- [ ] Documentar em `ARCHITECTURE.md`
- [ ] Documentar em `src/fito_aimm/README.md`
- [ ] Atualizar `requirements.txt` se necessário (adicionar `pytest`, `pydantic`)
- [ ] Criar exemplos em `scripts/examples/`
- [ ] Atualizar `.github/workflows/` para rodar testes

---

## 🚨 Riscos de Não Fazer Refatoração

| Risco | Impacto | Mitigação |
|-------|--------|-----------|
| Duplicação de código | Bugs corrigidos em um lugar mas não outro | Extrair para módulos compartilhados |
| Falta de testes | Regressões silenciosas em produção | Adicionar pytest + CI/CD |
| Configuração fragmentada | Inconsistência entre ambientes | Schema validation + carregamento centralizado |
| Módulos mortos | Poluição do codebase; confusão | Arquivar ou remover |
| String truncadas | Dados inválidos em CSVs de saída | Testes de integração |

---

## 📝 Próximos Passos

1. **Validar proposta** com stakeholders (2 dias)
2. **Priorizar FASE 1** (3-4 dias de implementação)
3. **Criar branch de refatoração** e PR incremental
4. **Adicionar CI/CD checks** (lint, type check, test coverage)
5. **Documentar decisões** em ADR (Architecture Decision Record)

---

**Autor:** GitHub Copilot  
**Status:** Pronto para implementação
