# Índice de Documentação — Fito+ Amazônia AIMM

**Gerado em:** 2026-07-08  
**Objetivo:** Inventário de todos os arquivos `.md` no repositório, com status de validade e recomendação de ação.

> **Política:** Nenhum arquivo foi removido nesta etapa — apenas catalogado e sinalizado.
> Para remover ou arquivar, consulte `docs/PROPOSTA_REORGANIZACAO.md`.

---

## Legenda

| Status | Descrição |
|--------|-----------|
| `ativo` | Documento vigente, referenciado no fluxo operacional atual |
| `histórico` | Registro válido de decisões passadas; útil para rastreabilidade |
| `revisar` | Conteúdo possivelmente desatualizado; precisa de verificação |
| `obsoleto` | Substituído ou irrelevante; candidato a arquivamento |

| Recomendação | Descrição |
|--------------|-----------|
| manter | Manter no local atual sem alteração |
| consolidar | Fundir com outro documento para evitar duplicação |
| mover | Mover para pasta mais adequada (ex.: `docs/`) |
| arquivar | Mover para `docs/archive/` e retirar do fluxo principal |

---

## Inventário

### Documentação operacional (raiz)

| Arquivo | Objetivo | Status | Recomendação |
|---------|----------|--------|--------------|
| `README.md` | Visão geral do projeto, arquitetura, setup rápido e checklist de pré-execução | `ativo` | manter |
| `README-local.md` | Guia detalhado de execução local (Flask + Caddy), configuração de `.env`, troubleshooting | `ativo` | mover → `docs/README-local.md` (longo prazo) |
| `README_operacional.md` | Estado operacional do projeto, política GitHub × Drive, trava decisória sobre OSCs | `ativo` | mover → `docs/README_operacional.md` (longo prazo) |
| `PHASE-CLOSE.md` | Registro de encerramento da fase de estabilização do ambiente local (Flask + Caddy) | `histórico` | mover → `docs/archive/PHASE-CLOSE.md` |

### Documentação de governança/auditoria (raiz)

| Arquivo | Objetivo | Status | Recomendação |
|---------|----------|--------|--------------|
| `AUDIT_FUNCIONALIDADES.md` | Auditoria de funcionalidades: estrutura, modelos obsoletos e propostas de refatoração (data: 2026-07-02) | `revisar` | mover → `docs/AUDIT_FUNCIONALIDADES.md` |
| `CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md` | Diagnóstico de capacidades implementadas vs. pendentes na calculadora AIMM (data: 2026-07-03) | `revisar` | mover → `docs/CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md` |
| `DASHBOARD_REFATORACAO.md` | Dashboard de acompanhamento do progresso de refatoração (data: 2026-07-03) | `revisar` | mover → `docs/DASHBOARD_REFATORACAO.md` |
| `REFATORACAO_RESUMO_EXECUTIVO.md` | Resumo executivo das fases 1 e 2 de refatoração (data: 2026-07-03) | `histórico` | mover → `docs/archive/REFATORACAO_RESUMO_EXECUTIVO.md` |

### Novos documentos (esta PR — pasta `docs/`)

| Arquivo | Objetivo | Status | Recomendação |
|---------|----------|--------|--------------|
| `docs/INDEX.md` | Este arquivo — inventário e catálogo de documentação | `ativo` | manter |
| `docs/PLANO_REFATORACAO_PRS.md` | Plano de refatoração em PRs pequenos com sequência, risco e critérios de aceite | `ativo` | manter |
| `docs/PROPOSTA_REORGANIZACAO.md` | Proposta de reorganização de pastas e documentação com estratégia incremental e rollback | `ativo` | manter |

---

## Prioridade de ação recomendada

1. **Imediato (esta PR):** Nenhuma remoção — apenas adição de `docs/INDEX.md`, `docs/PLANO_REFATORACAO_PRS.md` e `docs/PROPOSTA_REORGANIZACAO.md`.
2. **Próxima PR (doc/organize-governance):** Mover docs de governança da raiz para `docs/` conforme tabela acima.
3. **PR seguinte (doc/archive-historical):** Arquivar `PHASE-CLOSE.md`, `REFATORACAO_RESUMO_EXECUTIVO.md` em `docs/archive/`.
4. **Validação contínua:** Revisar status de `AUDIT_FUNCIONALIDADES.md`, `CALCULADORA_O_QUE_FAZ_E_O_QUE_FALTA.md`, `DASHBOARD_REFATORACAO.md` após revisão de conteúdo.

---

*Para detalhes da reorganização de pastas, veja `docs/PROPOSTA_REORGANIZACAO.md`.*  
*Para o plano de PRs incrementais, veja `docs/PLANO_REFATORACAO_PRS.md`.*
