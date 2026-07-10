# BRIEF — AGENTE DE AUDITORIA FACTUAL UI AIMM (SEM INFERÊNCIA)

## Missão
Auditar o sistema AIMM de forma factual para:
1) validar guias visuais existentes;
2) confirmar paleta/legendas oficiais realmente implementadas;
3) avaliar aderência da proposta de arquitetura de interface ao estado real do sistema;
4) produzir documentação de decisão pronta para execução sem retrabalho.

## Princípios obrigatórios
- Sem inferência: toda afirmação deve citar arquivo e linha.
- Sem “boa prática genérica” desconectada do repositório.
- Prioridade para o que está em `main`, com comparação em branches críticos.
- Classificar evidência por status: `IMPLEMENTADO`, `PARCIAL`, `EXPERIMENTAL`, `AUSENTE`, `CONFLITANTE`.

## Repositório e branches de análise
- Base: `main`
- Comparação obrigatória:
  - `origin/copilot/research-aimm-calculator-analysis`
  - `origin/copilot/analise-critica-calculadora-aimm`
  - `origin/copilot/research-interface-calculadora-aimm-fito`
  - `origin/copilot/research-data-ingestion-analysis`
  - `origin/refactor/phase2`
  - `origin/refactor/phase1`
  - `origin/chore/pipeline-audit-artifacts`

## Escopo factual obrigatório

### 1) Visual guidelines implementados
Verificar presença real de:
- paleta (cores, tokens, CSS variables, config de chart)
- legendas de gráficos/mapas/tabelas
- semântica visual de status (erro/alerta/sucesso/bloqueio)
- regras de confiabilidade e incerteza no visual
- regras de acessibilidade aplicadas (contraste, rótulos, fallback)

### 2) Arquitetura de interface (proposta vs realidade)
Para cada bloco da proposta UI:
- Busca/Filtros
- Tabela de indicadores
- Detalhes
- Visualizações (série, comparativo, mapa, export)
Mapear:
- endpoint real disponível
- payload atual
- módulo produtor do dado
- lacunas de integração

### 3) Integração com calculadora AIMM
Confirmar cadeia real:
- engine (`aimm_engine.py`)
- dashboard (`aimm_dashboard.py`)
- comunicação visual (`aimm_communication.py`)
- relatórios/artefatos produzidos
- limitações operacionais (ex.: validação humana, dependência manual)

### 4) Cobertura territorial mínima (obrigatória)
Validar condição de dados/campos para:
- Manaus (1302603)
- Benjamin Constant (1300607)
- Belém (1501402)
- Santarém (1506807)

### 5) Contrato canônico x implementação
Cruzar com:
- `docs/contracts/indicator_canonical.schema.json`
- `docs/contracts/indicator_examples.json`
Verificar se endpoints atuais conseguem preencher campos obrigatórios.

## Fontes primárias obrigatórias de leitura
- `app.py`, `Caddyfile`, `run-local.ps1`, `status-local.ps1`
- `src/fito_aimm/*.py`
- `docs/*.md` (incluindo `FEATURE_STATUS_BY_BRANCH.md`, `WB_INTEGRATION_FACTS.md`)
- `docs/contracts/*`
- `.github/workflows/*.yml`
- `config/*.yaml`
- `data/reference/*` e `data/processed/*` (quando citado por código)

## Entregáveis obrigatórios

### A) docs/UI_VISUAL_GUIDELINES_FACTUAL.md
Seções mínimas:
1. Resumo executivo factual (10 bullets)
2. Paleta oficial (confirmada ou não confirmada)
3. Legendas oficiais (confirmadas ou não confirmadas)
4. Regras visuais por estado (com evidência)
5. Conflitos entre branches
6. Decisão recomendada para padrão visual MVP
7. Riscos de regressão

### B) docs/UI_ARCHITECTURE_ALIGNMENT_FACTUAL.md
Seções mínimas:
1. Tabela “Bloco UI -> Endpoint -> Status -> Evidência”
2. O que funciona hoje sem novo desenvolvimento
3. O que exige desenvolvimento novo
4. Ordem de implementação sem retrabalho (2 semanas)
5. Dependências críticas e gates de release

### C) docs/UI_VISUAL_EVIDENCE_TABLE.csv
Colunas:
`tema,status,branch,arquivo,linhas,evidencia,impacto_ui,acao_recomendada`

### D) docs/UI_MUNICIPAL_COVERAGE_GAPS.md
Seções:
- situação por município
- campos disponíveis/faltantes
- ações concretas para fechamento de lacunas

## Critérios de aceite (hard gate)
Não concluir se faltar:
- evidência de arquivo/linha em qualquer afirmação crítica
- resposta explícita: paleta oficial confirmada? (sim/não)
- resposta explícita: legendas oficiais confirmadas? (sim/não)
- mapa de aderência arquitetura proposta vs sistema real
- plano de fechamento de gaps territoriais mínimos

## Regra final
Se não houver evidência suficiente para afirmar algo, registrar:
“**NÃO COMPROVADO NO REPOSITÓRIO ANALISADO**”.