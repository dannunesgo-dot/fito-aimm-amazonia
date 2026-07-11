# COMPARAÇÃO DE BRANCH — copilot/research-data-ingestion-analysis vs main

## Cabeçalho de rastreabilidade
- Branch: `copilot/research-data-ingestion-analysis` (commit `b69b99c`)
- Referência: `main`
- Ahead: 4 commits · Behind: 45 commits
- Data: 2026-07-10
- Método: `git diff main...copilot/research-data-ingestion-analysis` classificado + AST. Sem inferência.

## Resumo factual
- Arquivos úteis: 5 adicionados, 5 modificados, 0 removidos.
- Ruído de versionamento isolado: 13 arquivos (não contados como conteúdo).
- **Impacto no núcleo da cadeia AIMM: NAO**

## Módulos Python novos (com classes/funções públicas)
- `src/fito_aimm/gis_processor.py` — (sem classe/função pública detectada)
- `src/fito_aimm/ingestor.py` — class ResultadoIngestao
- `src/fito_aimm/pipeline_metrics.py` — class MetricaEtapa, class ColetorMetricas
- `src/fito_aimm/storage.py` — class Storage

## Arquivos modificados
- `requirements.txt`
- `src/fito_aimm/buscador.py`
- `src/fito_aimm/coletor_ibge.py`
- `src/fito_aimm/coletor_mapaosc.py`
- `src/fito_aimm/sincroniza_drive.py`

## Ruído isolado (13 arquivos — amostra)
- `=1.0`
- `=1.1`
- `=23.0.1`
- `=6.0`
- `src/fito_aimm/__pycache__/__init__.cpython-312.pyc`
> Ruído não é conteúdo útil; inflaria a contagem de mudanças se não isolado.
