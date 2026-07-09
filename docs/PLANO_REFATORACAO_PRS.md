# Plano de Refatoração em PRs Pequenos — Fito+ Amazônia AIMM

**Data:** 2026-07-08  
**Autor:** GitHub Copilot Coding Agent  
**Status:** Proposta — aguarda revisão e aprovação

---

## Princípios

- Cada PR deve ser **focado**, **reversível** e **não quebrar execução local** na branch `main`.
- Nenhuma PR de refatoração deve tocar no core funcional da API sem testes validados.
- PRs de documentação e higiene não exigem aprovação técnica pesada, mas devem ser revisados.

---

## Sequência de PRs sugerida

### PR 1 — `docs/improve-documentation-and-organization` ✅ (esta PR)

| Campo | Valor |
|-------|-------|
| **Objetivo** | Organização operacional e documentação: comando oficial, INDEX.md, limpeza de tmp/, checklist de pré-execução, scripts de consistência, plano de refatoração e proposta de reorganização |
| **Risco** | Muito baixo — apenas docs e higiene de versionamento |
| **Impacto** | Positivo: onboarding mais rápido, rastreabilidade clara |
| **Critérios de aceite** | `docs/INDEX.md` criado; README.md com checklist de pré-execução; `tmp/` com apenas `.gitkeep`; `.gitignore` atualizado; scripts de verificação funcionando |

---

### PR 2 — `doc/organize-governance`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Mover arquivos de governança/auditoria da raiz (`AUDIT_FUNCIONALIDADES.md`, `CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md`, `DASHBOARD_REFATORACAO.md`) para `docs/` |
| **Risco** | Baixo — mudança de localização de arquivos; qualquer link interno precisa ser atualizado |
| **Impacto** | Raiz do repositório mais limpa; mais fácil de navegar |
| **Critérios de aceite** | Arquivos movidos com `git mv` (preservando histórico); `docs/INDEX.md` atualizado; nenhum link quebrado em outros docs |

---

### PR 3 — `doc/archive-historical`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Arquivar documentos históricos (`PHASE-CLOSE.md`, `REFATORACAO_RESUMO_EXECUTIVO.md`) em `docs/archive/` |
| **Risco** | Muito baixo — sem impacto funcional |
| **Impacto** | Separação clara entre docs operacionais e registros históricos |
| **Critérios de aceite** | Pasta `docs/archive/` criada; arquivos movidos com `git mv`; `docs/INDEX.md` atualizado; README.md não faz referência direta a esses arquivos |

---

### PR 4 — `ops/refactor-scripts-common`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Fatorar funções comuns entre `run-local.ps1`, `stop-local.ps1`, `status-local.ps1` em módulo PowerShell compartilhado (`scripts/common.psm1`) |
| **Risco** | Médio — mudança em scripts de operação; testar cuidadosamente antes de merge |
| **Impacto** | Reduz duplicação; facilita manutenção de comportamento (ex.: Load-DotEnv, Get-PidsListeningOnPort) |
| **Critérios de aceite** | Fluxo `run-local.ps1` → `stop-local.ps1` → `status-local.ps1` funcionando sem regressão; funções comuns importadas via `Import-Module` |

---

### PR 5 — `refactor/src-structure`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Definir estrutura-alvo para `src/` (ex.: `src/api/`, `src/services/`, `src/domain/`, `src/infra/`) e reorganizar módulos existentes |
| **Risco** | Alto — pode afetar imports e rotas no `app.py`; exige testes completos |
| **Impacto** | Arquitetura mais legível e escalável; facilita adição de novos endpoints |
| **Critérios de aceite** | Todos os testes existentes passam (`python -m pytest -q`); `app.py` funcional; `GET /health` retorna 200; estrutura documentada em `docs/ARCHITECTURE.md` |

---

### PR 6 — `refactor/app-factory`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Refatorar `app.py` para padrão Application Factory (`create_app()`), separando bootstrap, rotas e handlers |
| **Risco** | Alto — ponto de entrada central; exige testes de smoke + integração |
| **Impacto** | Testabilidade melhorada; base para adicionar múltiplos ambientes (test, staging, prod) |
| **Critérios de aceite** | `create_app()` funciona; testes passam; `GET /health` → 200; documentação de arquitetura atualizada |

---

### PR 7 — `ci/add-basic-workflow`

| Campo | Valor |
|-------|-------|
| **Objetivo** | Adicionar workflow GitHub Actions para lint + testes em PRs (`python -m pytest -q`) |
| **Risco** | Baixo — não altera código funcional |
| **Impacto** | Regressões detectadas automaticamente; base para CI/CD |
| **Critérios de aceite** | Workflow passa na branch; falha de testes bloqueia merge |

---

## Ordem de execução recomendada

```
PR 1 (esta PR) → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 → PR 7
```

PRs 2 e 3 podem ser executadas em paralelo após PR 1.  
PRs 5 e 6 só devem começar após PR 4 estar concluída e testada.  
PR 7 pode ser feita a qualquer momento após PR 1.

---

*Para proposta de reorganização de pastas, veja `docs/PROPOSTA_REORGANIZACAO.md`.*
