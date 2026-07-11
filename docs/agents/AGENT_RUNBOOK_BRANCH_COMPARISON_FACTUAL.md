# AGENT RUNBOOK — BRANCH COMPARISON (AIMM)

## Objetivo operacional
Executar comparação factual reprodutível entre um branch-alvo e o `main`, sem
inferência, isolando ruído de conteúdo e destacando impacto no núcleo.

## Pré-condições
- Repositório com branches remotos disponíveis. Se o clone for raso ou
  single-branch, reconfigurar:
  `git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"`
  seguido de `git fetch --all --unshallow` (ou `--all`).
- Brief disponível: `docs/agents/BRIEF_BRANCH_COMPARISON_FACTUAL.md`.
- Nome do branch-alvo definido.

---

## Etapa 1 — Preparar
1. `git fetch --all --prune`.
2. Confirmar que `origin/<branch>` existe (`git branch -r`).
3. Registrar ahead/behind:
   `git rev-list --count origin/main..origin/<branch>` (ahead)
   `git rev-list --count origin/<branch>..origin/main` (behind).

## Etapa 2 — Diff classificado
1. `git diff --name-status origin/main...origin/<branch>`.
2. Para cada arquivo, classificar A/M/D e detectar ruído (padrões do Brief).
3. Separar contagem de conteúdo útil × ruído.

## Etapa 3 — Módulos Python novos
1. Filtrar arquivos `A` em `src/*.py` (não-ruído).
2. Para cada um, extrair classes e funções públicas via AST
   (`class`, `def execute_*/executar_*/coletar_*/main`).

## Etapa 4 — Impacto no núcleo
1. Verificar se há `M` em `aimm_engine.py`, `aimm_dashboard.py`,
   `aimm_communication.py` ou `app.py`.
2. Para cada, registrar magnitude (`git diff --stat`).
3. Responder explicitamente "impacto no núcleo? (sim/não)".

## Etapa 5 — Endpoints/APIs (se aplicável)
1. Se `app.py` foi modificado, comparar rotas Flask antes/depois.
2. Se coletores foram tocados, registrar mudança de URLs externas.

## Etapa 6 — Gerar entregáveis
1. `docs/BRANCH_COMPARISON_<branch>.md`.
2. Anexar linhas à `docs/BRANCH_COMPARISON_TABLE.csv`.

## Etapa 7 — Controle de qualidade (PDCA)
- [ ] ahead/behind registrado.
- [ ] Todo arquivo do diff classificado (A/M/D/RUIDO).
- [ ] Ruído isolado e quantificado.
- [ ] "Impacto no núcleo?" respondido.
- [ ] Módulos novos com classes/funções.
- [ ] Conflitos potenciais sinalizados quando houver.

## Resultado esperado
Comparação factual que permita decidir, com base em evidência, o que aproveitar
de um branch — sem fusão indiscriminada e sem confundir ruído com trabalho.
