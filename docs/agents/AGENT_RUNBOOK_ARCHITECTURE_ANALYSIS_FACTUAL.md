# AGENT RUNBOOK — ARCHITECTURE & TECHNICAL ANALYSIS (AIMM)

## Objetivo operacional
Executar análise factual reprodutível da arquitetura, objetivo, APIs,
funcionalidades e condições técnicas do sistema AIMM, sem inferência, gerando um
pacote rastreável.

## Pré-condições
- Repositório clonado e `main` atualizada (`git fetch --all --prune`).
- Brief disponível: `docs/agents/BRIEF_ARCHITECTURE_ANALYSIS_FACTUAL.md`.
- Acesso de rede para verificação de estado das APIs externas (opcional, mas
  recomendado; sem rede, marcar APIs como `NAO_VERIFICADA`).

---

## Etapa 1 — Preparar contexto
1. `git fetch --all --prune`; registrar commit auditado (`git rev-parse HEAD`).
2. Confirmar presença de: `app.py`, `requirements.txt`, `Caddyfile`,
   `src/fito_aimm/`, `config/`, `.github/workflows/`, `docs/`.

## Etapa 2 — Eixo Arquitetura
1. Ler `app.py` e `Caddyfile`/`Caddyfile.local`: extrair camadas, portas,
   fluxo requisição→resposta.
2. Para cada módulo `src/fito_aimm/*.py`: extrair via AST as constantes de
   entrada (`SEED_*`, leituras `data/*`) e saída (`OUT_*`).
3. Construir o grafo de dependência: um módulo A depende de B se A lê uma saída
   `data/processed/*` que B escreve. Registrar arestas com evidência.

## Etapa 3 — Eixo Objetivo
1. Extrair a finalidade declarada de `README.md`, `README_operacional.md`,
   `config/projeto_fito_amazonia.yaml` e cabeçalhos de módulos.
2. Registrar trecho verbatim (idêntico ao fonte) + arquivo.
3. Se fontes divergirem, listar as versões e sinalizar.

## Etapa 4 — Eixo APIs
1. Extrair todas as URLs externas do código (`grep`/AST).
2. Para cada API externa: identificar módulo consumidor (arquivo/linha), formato
   esperado, tratamento de timeout/erro.
3. Verificar estado da URL quando houver rede (requisição HEAD/GET leve);
   classificar `ATIVA`/`INATIVA`/`NAO_VERIFICADA`.
4. Ler `app.py`: listar cada rota Flask, método, autenticação (`verify_bearer_token`)
   e payload de retorno. Classificar `REQUER_AUTENTICACAO` quando aplicável.

## Etapa 5 — Eixo Funcionalidades
1. Para cada módulo de negócio, descrever o que a função pública de execução faz
   (entrada → processamento → saída), com base no código.
2. Marcar comentários, `TODO`, `pass`, ou blocos não alcançáveis como
   `DECLARADO_NAO_IMPLEMENTADO`.
3. Cruzar com `data/processed/module_pipeline_inventory.csv` (saída do agente
   `module_pipeline_audit`) quando presente, para status de completude.

## Etapa 6 — Eixo Condições técnicas
1. Stack e versões: `requirements.txt` + versão Python nos workflows.
2. Requisitos de execução: portas (Caddy/Flask), variáveis de `.env.example`,
   dependências de sistema (Caddy no PATH).
3. Governança de dados: política GitHub × Drive de
   `config/system_freeze_rules.yaml`; `data/reference/source_registry.csv`.
4. Riscos: dependência de artefato manual, dados sensíveis, cadeia de pipeline.

## Etapa 7 — Gerar entregáveis
1. `docs/ARCHITECTURE_ANALYSIS_FACTUAL.md`
2. `docs/ARCHITECTURE_API_TABLE.csv`
3. `docs/ARCHITECTURE_EVIDENCE_TABLE.csv`

## Etapa 8 — Controle de qualidade final (PDCA)
Checklist:
- [ ] Commit auditado registrado.
- [ ] Objetivo com trecho verbatim e fonte.
- [ ] Toda API externa com estado classificado.
- [ ] Todo endpoint interno com método e autenticação.
- [ ] Grafo de dependência entre módulos presente.
- [ ] Funcionalidade descrita por módulo de negócio.
- [ ] Condições técnicas com stack, portas e variáveis de ambiente.
- [ ] Sem inferência não comprovada; lacunas com o literal exigido.

## Resultado esperado
Retrato técnico completo que permita decisões de arquitetura, integração e
evolução do sistema sem suposição.
