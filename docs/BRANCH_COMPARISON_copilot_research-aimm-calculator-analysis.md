# COMPARAÇÃO DE BRANCH — copilot/research-aimm-calculator-analysis vs main

## Cabeçalho de rastreabilidade
- Branch: `copilot/research-aimm-calculator-analysis` (commit `6af367f`)
- Referência: `main`
- Ahead: 14 commits · Behind: 45 commits
- Data: 2026-07-10
- Método: `git diff main...copilot/research-aimm-calculator-analysis` classificado + AST. Sem inferência.

## Resumo factual
- Arquivos úteis: 28 adicionados, 28 modificados, 0 removidos.
- Ruído de versionamento isolado: 0 arquivos (não contados como conteúdo).
- **Impacto no núcleo da cadeia AIMM: SIM**
  - `src/fito_aimm/aimm_engine.py` modificado (82+ 18-)

## Módulos Python novos (com classes/funções públicas)
- `src/fito_aimm/drive_sync.py` — class DriveUploadResult
- `src/fito_aimm/mapaosc/__init__.py` — (sem classe/função pública detectada)
- `src/fito_aimm/mapaosc/classifier.py` — (sem classe/função pública detectada)
- `src/fito_aimm/mapaosc/fetcher.py` — class ResultadoColeta
- `src/fito_aimm/mapaosc/normalizer.py` — (sem classe/função pública detectada)
- `src/fito_aimm/territorios.py` — (sem classe/função pública detectada)
- `src/fito_aimm/validators/__init__.py` — (sem classe/função pública detectada)
- `src/fito_aimm/validators/schema_validator.py` — class SchemaValidationIssue, class SchemaValidationResult, class AIMMIndicatorInputRow, class AIMMDimensionPolicyRow, class AIMMBlockerRow, class SchemaValidator

## Arquivos modificados
- `.github/workflows/aimm_engine.yml`
- `.github/workflows/area_densidade_ibge_geociencias.yml`
- `.github/workflows/baseline_ibge_sidra.yml`
- `.github/workflows/coleta_ibge_teste.yml`
- `.github/workflows/mapaosc_triagem.yml`
- `.github/workflows/rodada_4_31_drive_api_real_test.yml`
- `.github/workflows/rodada_4_31b_drive_api_oauth_real_test.yml`
- `.github/workflows/rodada_4_32_aimm_minimum_integrated_pipeline.yml`
- `.github/workflows/validar_bases.yml`
- `config/aimm_engine_rules.yaml`
- `docs/deprecated/buscador.py`
- `docs/deprecated/conferidor.py`
- `docs/deprecated/extrator.py`
- `docs/deprecated/sincroniza_drive.py`
- `requirements.txt`
- `scripts/rodada_4_31_drive_api_real_test.py`
- `scripts/rodada_4_31b_drive_api_oauth_real_test.py`
- `scripts/rodada_4_32_aimm_minimum_integrated_pipeline.py`
- `scripts/rodada_4_38_final_ifc_aimm_operational_package.py`
- `scripts/testar_area_densidade_ibge.py`
- `scripts/testar_baseline_ibge.py`
- `scripts/testar_coleta_ibge.py`
- `scripts/testar_mapaosc_triagem.py`
- `scripts/validar_bases.py`
- `src/fito_aimm/aimm_engine.py` **(NÚCLEO)**
- `src/fito_aimm/coletor_ibge.py`
- `src/fito_aimm/coletor_ibge_geociencias.py`
- `src/fito_aimm/coletor_mapaosc.py`
