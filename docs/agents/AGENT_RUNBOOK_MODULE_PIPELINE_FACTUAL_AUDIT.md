# AGENT RUNBOOK — MODULE/PIPELINE FACTUAL AUDIT (AIMM)

## Objetivo operacional
Executar auditoria factual reprodutível da completude e consistência dos módulos
de negócio do sistema AIMM, sem inferência, gerando um pacote rastreável e
reexecutável.

## Pré-condições
- Repositório clonado e `main` atualizada (`git fetch --all --prune`).
- Brief disponível: `docs/agents/BRIEF_MODULE_PIPELINE_FACTUAL_AUDIT.md`.
- Python 3.12 e dependências de `requirements.txt` instaladas.

---

## Etapa 1 — Preparar contexto de análise
1. Atualizar refs: `git fetch --all --prune`.
2. Confirmar presença dos diretórios: `src/fito_aimm/`, `config/`,
   `.github/workflows/`, `scripts/`.
3. Registrar o commit auditado (`git rev-parse HEAD`) no relatório.

## Etapa 2 — Enumerar universo de módulos
1. Listar `src/fito_aimm/*.py`.
2. Separar módulos-base utilitários (superfície mínima) dos módulos de negócio,
   conforme o Brief.
3. Para cada módulo de negócio, registrar linha de contagem (`wc -l`).

## Etapa 3 — Extração factual por módulo (requisitos 1..8)
Para cada módulo de negócio:
1. Confirmar existência do `.py` (requisito 1).
2. Localizar função de execução pública `execute_*` / `main` (requisito 2).
3. Extrair referências a `config/*.yaml` no código; confirmar existência de cada
   arquivo de regra (requisito 3).
4. Confirmar `scripts/testar_<modulo>.py` (requisito 4).
5. Confirmar `.github/workflows/<modulo>.yml` (requisito 5). Quando o nome do
   workflow divergir do nome do módulo, registrar o mapeamento explícito.
6. Extrair constantes `OUT_*` e demais caminhos de escrita (requisito 6).
7. Abrir o workflow correspondente e confirmar se cada caminho `OUT_*` aparece
   no bloco `path:` do passo `upload-artifact` (requisito 7).
8. Extrair `SEED_*` e arquivos de leitura; para cada um, confirmar existência no
   repositório OU classificação como artefato externo em
   `config/system_freeze_rules.yaml` (requisito 8).

Registrar, por requisito: arquivo, evidência objetiva e status
(`IMPLEMENTADO`/`PARCIAL`/`AUSENTE`/`NAO_COMPROVADO`).

## Etapa 4 — Classificação do módulo
- Todos os requisitos aplicáveis atendidos → `IMPLEMENTADO`.
- Requisito 1, 2 e 4 atendidos, mas falha em 3, 5, 6, 7 ou 8 → `PARCIAL`.
- Código presente sem teste e sem workflow → `EXPERIMENTAL`.
- Divergência entre o que o código escreve e o que o workflow publica →
  `CONFLITANTE` (registrar os dois lados).
- Sem evidência para decidir → `NAO_COMPROVADO`.

## Etapa 5 — Consolidação de saídas não publicadas
1. Cruzar a união de todos os `OUT_*` do código com a união de todos os
   `path:` dos workflows.
2. Listar explicitamente as saídas escritas por algum módulo que **não** são
   publicadas por nenhum workflow.

## Etapa 6 — Gerar entregáveis
Gerar obrigatoriamente:
1. `docs/MODULE_PIPELINE_AUDIT_FACTUAL.md`
2. `docs/MODULE_PIPELINE_EVIDENCE_TABLE.csv`
3. `docs/MODULE_PIPELINE_GAPS.md`

O módulo executável `src/fito_aimm/module_pipeline_audit.py` (acompanhado de
`scripts/testar_module_pipeline_audit.py`) automatiza as Etapas 2 a 5 e emite os
insumos factuais das tabelas.

## Etapa 7 — Controle de qualidade final (PDCA)
Checklist:
- [ ] Todo módulo de negócio classificado.
- [ ] Toda afirmação de presença/ausência com arquivo.
- [ ] Pergunta "tríade completa?" respondida por módulo (sim/não).
- [ ] Lista de saídas não publicadas por workflow gerada.
- [ ] Lacunas com ação concreta.
- [ ] Sem inferência não comprovada; lacunas marcadas com o literal exigido.
- [ ] Commit auditado registrado no relatório.

## Resultado esperado
Pacote factual que permita fechar lacunas de completude e consistência dos
módulos AIMM sem retrabalho e sem decisões baseadas em suposição.
