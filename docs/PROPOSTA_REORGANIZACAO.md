# Proposta de Reorganização de Pastas e Documentação — Fito+ Amazônia AIMM

**Data:** 2026-07-08  
**Autor:** GitHub Copilot Coding Agent  
**Status:** Proposta — aguarda revisão e aprovação

---

## Árvore atual resumida

```
fito-aimm-amazonia/
├── .env.example
├── .gitignore
├── app.py                              ← ponto de entrada Flask
├── requirements.txt
├── run-local.ps1                       ← orquestração local (oficial)
├── stop-local.ps1
├── status-local.ps1
├── run-tests-local.ps1
├── activate-api.ps1
├── deactivate-api.ps1
├── Iniciar-API.cmd                     ← fallback CMD
├── Parar-API.cmd                       ← fallback CMD
├── Caddyfile
├── Caddyfile.local
│
├── AUDIT_FUNCIONALIDADES.md            ← docs de governança na raiz
├── CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md
├── DASHBOARD_REFATORACAO.md
├── PHASE-CLOSE.md
├── README.md
├── README-local.md
├── README_operacional.md
├── REFATORACAO_RESUMO_EXECUTIVO.md
│
├── config/
│   └── *.yaml                          ← regras e configurações
│
├── data/
│   ├── reference/
│   └── evidence/
│
├── docs/                               ← (quase vazio antes desta PR)
│   ├── INDEX.md
│   ├── PLANO_REFATORACAO_PRS.md
│   └── PROPOSTA_REORGANIZACAO.md
│
├── scripts/
│   ├── check-consistency.ps1
│   ├── check_consistency.py
│   ├── test_api_integration.ps1
│   ├── validar_bases.py
│   └── rodada_*.py / testar_*.py       ← scripts operacionais de rodadas
│
├── src/
│   └── fito_aimm/                      ← módulos Python (domínio)
│
└── tmp/
    └── .gitkeep
```

---

## Árvore alvo proposta

```
fito-aimm-amazonia/
├── .env.example
├── .gitignore
├── app.py                              ← ponto de entrada Flask (mantido)
├── requirements.txt
│
├── run-local.ps1                       ← comando oficial (raiz — convenção do projeto)
├── stop-local.ps1
├── status-local.ps1
├── run-tests-local.ps1
├── activate-api.ps1
├── deactivate-api.ps1
├── Iniciar-API.cmd
├── Parar-API.cmd
├── Caddyfile
├── Caddyfile.local
│
├── README.md                           ← visão geral + checklist pré-execução
│
├── config/
│   └── *.yaml
│
├── data/
│   ├── reference/
│   └── evidence/
│
├── docs/
│   ├── INDEX.md                        ← catálogo de documentação
│   ├── PLANO_REFATORACAO_PRS.md        ← plano incremental de PRs
│   ├── PROPOSTA_REORGANIZACAO.md       ← este arquivo
│   │
│   ├── README-local.md                 ← movido da raiz
│   ├── README_operacional.md           ← movido da raiz
│   │
│   ├── AUDIT_FUNCIONALIDADES.md        ← movido da raiz
│   ├── CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md  ← movido da raiz
│   ├── DASHBOARD_REFATORACAO.md        ← movido da raiz
│   │
│   └── archive/
│       ├── PHASE-CLOSE.md              ← arquivado da raiz
│       └── REFATORACAO_RESUMO_EXECUTIVO.md  ← arquivado da raiz
│
├── scripts/
│   ├── check-consistency.ps1           ← verificação de consistência
│   ├── check_consistency.py            ← verificação de consistência (Python)
│   ├── common.psm1                     ← (futuro) funções comuns PowerShell
│   ├── test_api_integration.ps1
│   ├── validar_bases.py
│   └── rodada_*.py / testar_*.py
│
├── src/
│   └── fito_aimm/
│       ├── api/                        ← (futuro) rotas e handlers
│       ├── services/                   ← (futuro) lógica de negócio
│       ├── domain/                     ← (futuro) modelos de domínio
│       └── infra/                      ← (futuro) conectores externos
│
└── tmp/
    └── .gitkeep
```

---

## Estratégia incremental de migração

A migração deve seguir a sequência de PRs definida em `docs/PLANO_REFATORACAO_PRS.md`.

### Fase 1 — Higiene e docs (PR 1, esta PR)
- Criar `docs/INDEX.md`, `docs/PLANO_REFATORACAO_PRS.md`, `docs/PROPOSTA_REORGANIZACAO.md`.
- Limpar `tmp/` do versionamento.
- Reforçar `.gitignore`.
- Atualizar `README.md` com checklist de pré-execução e comando oficial.

### Fase 2 — Reorganizar documentação (PRs 2 e 3)
- Usar `git mv` para preservar histórico ao mover arquivos de governança para `docs/`.
- Arquivar históricos em `docs/archive/`.
- Atualizar `docs/INDEX.md` e quaisquer links cruzados.
- **Não mover scripts operacionais** nem `app.py` nesta fase.

### Fase 3 — Refatorar scripts PowerShell (PR 4)
- Extrair funções comuns para `scripts/common.psm1`.
- Atualizar `run-local.ps1`, `stop-local.ps1`, `status-local.ps1` para importar o módulo.
- Testar fluxo completo antes do merge.

### Fase 4 — Reestruturar src/ (PRs 5 e 6)
- Criar subpastas alvo em `src/fito_aimm/`.
- Mover módulos gradualmente, atualizando imports.
- Refatorar `app.py` para Application Factory.
- Executar testes a cada passo (`python -m pytest -q`).

---

## Rollback simples

Cada PR é atômica e reversível via `git revert <commit>` ou fechando a PR sem merge.

Para reverter qualquer fase de documentação:
```bash
git revert <commit-hash>
git push origin main
```

Para reverter reorganização de pastas (usando `git mv`):
```bash
git revert <merge-commit-hash>
# O git mv registra renomeações — o revert restaura a localização original.
```

Para emergências (reverter múltiplos commits de uma PR):
```bash
git revert --no-commit <oldest-commit>..<newest-commit>
git commit -m "revert: reverter PR <número>"
```

---

## Notas de decisão

- **Scripts PowerShell permanecem na raiz** em vez de ir para `scripts/` porque o padrão estabelecido no projeto é ter `run-local.ps1`, `stop-local.ps1` etc. na raiz para acesso imediato (`.\run-local.ps1`). Mover exigiria atualizar todos os documentos que referenciam esses caminhos — baixo impacto técnico, alto custo de atualização de docs. Adiar para PR posterior se o time decidir consolidar.
- **`app.py` permanece na raiz** — convenção Flask/Python padrão.
- **`README.md` permanece na raiz** — exigência do GitHub para exibição automática.

---

*Para o plano detalhado de PRs, veja `docs/PLANO_REFATORACAO_PRS.md`.*  
*Para o catálogo de documentação, veja `docs/INDEX.md`.*
