# COMPARAÇÃO DE BRANCH — refactor/phase2 vs main

## Cabeçalho de rastreabilidade
- Branch: `refactor/phase2` (commit `c50f6a9`)
- Referência: `main`
- Ahead: 6 commits · Behind: 48 commits
- Data: 2026-07-10
- Método: `git diff main...refactor/phase2` classificado + AST. Sem inferência.

## Resumo factual
- Arquivos úteis: 14 adicionados, 1 modificados, 0 removidos.
- Ruído de versionamento isolado: 0 arquivos (não contados como conteúdo).
- **Impacto no núcleo da cadeia AIMM: SIM**
  - `src/fito_aimm/aimm_engine.py` modificado (14+ 1-)

## Módulos Python novos (com classes/funções públicas)
- `src/fito_aimm/models/__init__.py` — (sem classe/função pública detectada)
- `src/fito_aimm/models/aimm_models.py` — class NivelConfianca, class StatusProntidao, class Papel, class FaixaScore, class AIMMIndicator, class AIMMIndicatorScore, class AIMMDimensionPolicy, class AIMMDimensionScore, class AIMMOverallScore, class AIMMBlocker, class OSCClassificacao, class OSCOrganizacao, class Evidence, class ValidationResult, class Config, class Config
- `src/fito_aimm/utils/__init__.py` — (sem classe/função pública detectada)
- `src/fito_aimm/utils/normalization.py` — (sem classe/função pública detectada)
- `src/fito_aimm/validators/__init__.py` — (sem classe/função pública detectada)
- `src/fito_aimm/validators/aimm_validator.py` — class AIMMEngineValidator, class OSCTriagemValidator, class EvidenceValidator
- `src/fito_aimm/validators/base_validator.py` — class ValidationError, class BaseValidator, class SchemaValidator, class CSVValidator, class BusinessRuleValidator, class AggregateValidator

## Arquivos modificados
- `src/fito_aimm/aimm_engine.py` **(NÚCLEO)**
