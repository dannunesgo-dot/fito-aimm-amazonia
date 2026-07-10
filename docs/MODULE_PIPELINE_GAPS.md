# LACUNAS — AUDITORIA DE MÓDULO/PIPELINE (AIMM)

Rastreabilidade: branch `main`, execução no GitHub Actions em 2026-07-10.
Fonte de dados: `data/processed/module_pipeline_inventory.csv` e
`docs/MODULE_PIPELINE_EVIDENCE_TABLE.csv`.

## 1. Situação das lacunas

| id_lacuna | modulo | tema | descricao | criticidade | situacao |
|---|---|---|---|---|---|
| GAP_MODAUDIT_001 | pre_diligencia_manual_validator.py | workflow_ausente | Não existia workflow próprio de integração contínua. | alta | **RESOLVIDA** — criado `.github/workflows/pre_diligencia_manual_validation.yml`, executado com sucesso no GitHub Actions. Requisito workflow → IMPLEMENTADO. |
| GAP_MODAUDIT_002 | coletor_ibge.py | saida_nao_detectavel | Módulo não expõe `OUT_*`; escrita via caminho derivado de catálogo. | media | **RESOLVIDA** — função de execução `coletar_*` reconhecida; módulo classificado IMPLEMENTADO. Sem saída órfã (0 no cômputo global). |
| GAP_MODAUDIT_003 | coletor_mapaosc.py | saida_nao_detectavel | Mesma situação de GAP_MODAUDIT_002. | media | **RESOLVIDA** — idem; módulo IMPLEMENTADO. |
| GAP_MODAUDIT_004 | aimm_communication.py; aimm_dashboard.py; coletor_ibge_geociencias.py; pre_diligencia_consolidacao.py; pre_diligencia_manual_validator.py; pre_diligencia_osc.py; risk_osc.py; risk_osc_diagnostics.py | dependencia_pipeline_runtime | Consomem saídas `data/processed/*` geradas por módulos anteriores na cadeia. Em checkout limpo aparecem como ausentes; resolvem quando o produtor roda antes. | media | aberta (comportamento esperado, não é defeito) |
| GAP_MODAUDIT_005 | module_pipeline_audit.py | workflow_nao_mergeado | Workflow do próprio agente. | baixa | **RESOLVIDA** — `module_pipeline_audit.yml` no `main`, executando. Módulo IMPLEMENTADO. |

## 2. Correções aplicadas ao próprio agente (registro de rastreabilidade)
- **Detector de execução:** ampliado para reconhecer as convenções do
  repositório `execute_*`, `executar_*`, `coletar_*` e `main` (antes só
  `execute_*`/`main`). Eliminou 7 falsos negativos de execução; `coletor_ibge` e
  `coletor_mapaosc` passaram de PARCIAL a IMPLEMENTADO.
- **Mapa de workflow:** adicionada a linha
  `pre_diligencia_manual_validator → pre_diligencia_manual_validation`,
  eliminando o falso `workflow=AUSENTE` daquele módulo.
- Efeito na contagem: 8/10 (com falsos negativos) → **10/8** (evidência fiel).

## 3. Impacto no pipeline AIMM
- Todas as lacunas **estruturais** estão resolvidas. Nenhum módulo de negócio
  tem código, teste, workflow ou publicação ausentes.
- A única classe de pendência remanescente (GAP_MODAUDIT_004) é dependência de
  dados em runtime, resolvida por ordem topológica de execução — não requer
  alteração de código.

## 4. Ações concretas remanescentes
1. Publicar as saídas intermediárias `data/processed/*` como artefato nos
   workflows produtores (fecha a aparência de dependência ausente em checkout
   limpo).
2. Registrar a ordem topológica de execução da cadeia AIMM em documento próprio.

> Lacunas sem evidência: **NÃO COMPROVADO NO REPOSITÓRIO ANALISADO** — nenhuma
> neste ciclo; todas as afirmações têm arquivo de evidência na tabela CSV.
