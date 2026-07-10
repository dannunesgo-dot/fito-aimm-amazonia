# AUDITORIA FACTUAL DE MÓDULO/PIPELINE — AIMM

## Cabeçalho de rastreabilidade
- Repositório: `https://github.com/dannunesgo-dot/fito-aimm-amazonia`
- Branch: `main`
- Data da última execução no GitHub Actions: 2026-07-10
- Agente: `module_pipeline_audit` (workflow `module-pipeline-audit`, execução real)
- Método: análise de sintaxe (AST) do código-fonte + checagem cruzada com
  workflows e sistema de arquivos. Sem inferência.

> **Nota sobre o ambiente de execução:** em execução via GitHub Actions com o
> checkout do `main`, saídas intermediárias em `data/processed/` e
> `data/evidence/` geradas em runtime por outro módulo podem não estar
> presentes se a cadeia produtora não rodou antes. Esses casos aparecem como
> `PARCIAL` (dependência de pipeline), não como falha estrutural.

## 1. Resumo executivo factual
- Universo: 24 arquivos `*.py` em `src/fito_aimm/`; 18 módulos de negócio e 6
  utilitários-base (`__init__.py`, `buscador.py`, `extrator.py`,
  `normalizador.py`, `conferidor.py`, `sincroniza_drive.py`).
- Módulos de negócio **IMPLEMENTADO** (tríade completa): **10** — `aimm_engine`,
  `benchmark_proxy`, `budget_components`, `calculator_architecture`,
  `coletor_ibge`, `coletor_mapaosc`, `module_pipeline_audit`, `product_pathway`,
  `species_selection`, `system_freeze_index`.
- Módulos de negócio **PARCIAL**: **8** — `aimm_communication`, `aimm_dashboard`,
  `coletor_ibge_geociencias`, `pre_diligencia_consolidacao`,
  `pre_diligencia_manual_validator`, `pre_diligencia_osc`, `risk_osc`,
  `risk_osc_diagnostics`.
- Módulos **CONFLITANTE**: **0**.
- Saídas escritas por código e não publicadas por nenhum workflow: **0**.
- Todos os 18 módulos de negócio possuem função pública de execução
  (convenções reconhecidas: `execute_*`, `executar_*`, `coletar_*`, `main`) e
  teste correspondente em `scripts/testar_*`.
- Causa única de todos os 8 status `PARCIAL`: dependência de pipeline
  (`data/processed/*` consumida de outro módulo) ausente no checkout — não seed
  de entrada faltante, não lacuna estrutural.
- Nenhum módulo de negócio permanece com workflow ausente. A lacuna estrutural
  histórica (`pre_diligencia_manual_validator` sem workflow) foi resolvida com a
  criação de `.github/workflows/pre_diligencia_manual_validation.yml`.
- Tabela de evidência gerada: 110 linhas rastreáveis (uma afirmação → um
  arquivo).

## 2. Inventário de módulos auditados
Classificação completa em `data/processed/module_pipeline_inventory.csv`.

| Classe | Quantidade |
|---|---|
| Negócio | 18 |
| Utilitário-base | 6 |

## 3. Tabela de completude — Módulo → Status
(`OK` = IMPLEMENTADO · `NA` = não aplicável · `P` = PARCIAL)

| Módulo | codigo | execucao | regras_yaml | teste | workflow | saidas_decl | saidas_pub | seeds | Status |
|---|---|---|---|---|---|---|---|---|---|
| aimm_engine | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| benchmark_proxy | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| budget_components | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| calculator_architecture | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| coletor_ibge | OK | OK | NA | OK | OK | NA | NA | NA | **IMPLEMENTADO** |
| coletor_mapaosc | OK | OK | NA | OK | OK | NA | NA | NA | **IMPLEMENTADO** |
| module_pipeline_audit | OK | OK | OK | OK | OK | OK | OK | NA | **IMPLEMENTADO** |
| product_pathway | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| species_selection | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| system_freeze_index | OK | OK | OK | OK | OK | OK | OK | OK | **IMPLEMENTADO** |
| aimm_communication | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |
| aimm_dashboard | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |
| coletor_ibge_geociencias | OK | OK | NA | OK | OK | NA | NA | P | PARCIAL |
| pre_diligencia_consolidacao | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |
| pre_diligencia_manual_validator | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |
| pre_diligencia_osc | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |
| risk_osc | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |
| risk_osc_diagnostics | OK | OK | OK | OK | OK | OK | OK | P | PARCIAL |

## 4. Módulos completos hoje (sem novo desenvolvimento)
Os 10 módulos IMPLEMENTADO possuem código + (regras quando aplicável) + teste +
workflow + saídas declaradas + saídas publicadas + seeds resolvidos, todos
comprovados por arquivo. São a base confiável para novas tarefas de análise.

## 5. Módulos parciais e o que falta
Os 8 módulos PARCIAL diferem dos completos por um único requisito: `seeds`
(dependência de pipeline em runtime). Nenhum tem lacuna de código, workflow,
teste ou publicação. Ação para elevá-los a IMPLEMENTADO em auditoria: executar a
cadeia produtora antes (ordem topológica) ou publicar as saídas intermediárias
`data/processed/*` como artefato.

## 6. Riscos de regressão e dependências
- Cadeia confirmada: `aimm_dashboard` e `aimm_communication` consomem saídas de
  `aimm_engine`; módulos de pré-diligência consomem saídas de
  `risk_osc`/`coletor_mapaosc`. Alterar um produtor sem reexecutar consumidores
  quebra a cadeia. Recomenda-se ordem topológica de execução.

## 7. Decisão recomendada de priorização
1. Documentar/publicar as saídas intermediárias `data/processed/*` como
   artefato nos workflows produtores, para que auditoria em checkout limpo deixe
   de marcá-las como dependência ausente.
2. Registrar a ordem topológica de execução da cadeia AIMM.
3. Manter o agente `module-pipeline-audit` como gate recorrente (já dispara a
   cada push que toque seus arquivos).
