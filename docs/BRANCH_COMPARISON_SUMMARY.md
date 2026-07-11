# SÍNTESE DAS COMPARAÇÕES DE BRANCHES — fito-aimm-amazonia

## Cabeçalho
- Referência: `main` · Data: 2026-07-10
- Fonte: agente `branch_comparison` (execução real contra o repositório).
- Branches comparados nesta rodada: `refactor/phase1`, `refactor/phase2`,
  `copilot/research-aimm-calculator-analysis`,
  `copilot/research-data-ingestion-analysis`.

## Quadro comparativo factual

| Branch | Ahead | Behind | Úteis (A+M) | Ruído | Impacto núcleo | Conteúdo principal |
|---|---|---|---|---|---|---|
| refactor/phase2 | 6 | 48 | 15 | 0 | SIM (engine 14+/1-) | Modelos Pydantic + camadas de validação |
| refactor/phase1 | 4 | 48 | 9 | 0 | SIM (engine) | Limpeza de módulos-base; utils/normalization |
| copilot/research-aimm-calculator | 14 | 45 | 56 | 0 | SIM (engine 82+/18-) | Modularização MapaOSC + validators + workflows |
| copilot/research-data-ingestion | 4 | 45 | 10 | 13 | NÃO | Ingestão/GIS (gis_processor, ingestor, storage) |

## Leitura factual (sem juízo de mérito)

### Sobre limpeza (branches limpos vs sujos)
- `refactor/phase1`, `refactor/phase2` e `copilot/research-aimm-calculator`:
  **0 ruído**. Prontos para leitura de conteúdo sem filtragem.
- `copilot/research-data-ingestion`: **13 arquivos de ruído** (13 vs 10 úteis) —
  `__pycache__`, `.pyc` e arquivos `=1.0`/`=6.0` (erros de `pip install`).
  Requer limpeza antes de qualquer aproveitamento.

### Sobre impacto no núcleo (magnitude da modificação em aimm_engine.py)
- `refactor/phase2`: **14+/1-** — modificação mínima (provável import dos novos
  modelos). Menor risco de conflito.
- `copilot/research-aimm-calculator`: **82+/18-** — reescrita substancial do
  engine. Maior risco de conflito com o `main` atual.
- `refactor/phase1`: modifica engine (magnitude registrada no `.md` do branch).
- `copilot/research-data-ingestion`: **não toca o núcleo** — mais isolado,
  adição de camada nova de ingestão.

### Sobre sobreposição
- `refactor/phase2` e `copilot/research-aimm-calculator` propõem ambos uma
  **camada de validators**, com abordagens diferentes (phase2: classes
  `BaseValidator`/`SchemaValidator`/`CSVValidator`; research-calculator:
  `validators/schema_validator.py`). São **conflitantes** — aproveitar os dois
  exige escolher uma abordagem.
- Modularização do `coletor_mapaosc.py` (620 linhas) aparece apenas em
  `copilot/research-aimm-calculator` (pacote `mapaosc/` com fetcher/classifier/
  normalizer).

## Observações para decisão (a decisão é do usuário)
1. Todos os branches de conteúdo estão 45–48 commits atrás do `main`. Qualquer
   aproveitamento exige rebase/merge cuidadoso.
2. Branch mais limpo e de menor risco no núcleo: `refactor/phase2`.
3. Branch com mais conteúdo mas maior risco no núcleo:
   `copilot/research-aimm-calculator` (reescreve engine, mexe em 9 workflows).
4. Sobreposição de validators entre os dois acima exige escolha de abordagem
   única.
5. `copilot/research-data-ingestion` precisa de limpeza de ruído antes de leitura.

> Este documento descreve o que muda. NÃO recomenda merge. A avaliação de
> qualidade e a decisão de aproveitamento exigem leitura de código pelo usuário.
