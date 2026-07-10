# BRIEF — AGENTE DE AUDITORIA FACTUAL DE MÓDULO/PIPELINE (SEM INFERÊNCIA)

## Missão
Auditar, de forma factual e reproduzível, a completude e a consistência de cada
módulo de negócio do sistema AIMM (Análise de Investimento e Maturidade de
Mercado) para:
1) confirmar se cada módulo em `src/fito_aimm/` forma uma tríade operacional
   completa: código Python + regras `config/*.yaml` + workflow
   `.github/workflows/*.yml` + teste `scripts/testar_*.py`;
2) verificar se as saídas (`OUT_*`) declaradas no código estão descritas e
   publicadas pelo workflow correspondente (`upload-artifact`);
3) verificar se os seeds/entradas (`SEED_*`, arquivos lidos) existem no
   repositório ou estão explicitamente classificados como artefato externo
   (Google Drive / GitHub Actions);
4) produzir documentação de decisão pronta para execução, sem retrabalho e sem
   suposição.

O agente **não** avalia mérito de negócio, não recalcula score AIMM, não aprova
Organizações da Sociedade Civil (OSCs), espécies, produtos, orçamento ou rotas
regulatórias. Ele audita **estrutura, rastreabilidade e consistência técnica**.

## Princípios obrigatórios
- Sem inferência: toda afirmação crítica cita arquivo e, quando aplicável,
  linha(s).
- Sem "boa prática genérica" desconectada do repositório.
- Prioridade para o que está em `main`.
- Classificar cada achado por status controlado: `IMPLEMENTADO`, `PARCIAL`,
  `AUSENTE`, `EXPERIMENTAL`, `CONFLITANTE`, `NAO_COMPROVADO`.
- Lacuna sem evidência é declarada com o literal
  **"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.

## Repositório e escopo de análise
- Base: `main` do repositório
  `https://github.com/dannunesgo-dot/fito-aimm-amazonia`.
- Universo auditado: todo módulo `*.py` em `src/fito_aimm/`, exceto os
  módulos-base utilitários de superfície mínima (`buscador.py`, `extrator.py`,
  `normalizador.py`, `conferidor.py`, `sincroniza_drive.py`, `__init__.py`),
  que são registrados como `utilitario_base` e não exigem tríade completa.

## Definição factual de "módulo completo" (critério de aceite por módulo)
Um módulo de negócio é classificado como **IMPLEMENTADO** somente se todos os
itens abaixo forem verdadeiros e comprovados por arquivo:

| # | Requisito | Evidência esperada |
|---|-----------|--------------------|
| 1 | Código Python presente | `src/fito_aimm/<modulo>.py` |
| 2 | Função de execução pública | `def execute_*` ou `def testar_*`/`def main` no módulo ou no teste |
| 3 | Regras YAML presentes (quando o código referencia `config/*.yaml`) | `config/<regra>.yaml` existe |
| 4 | Teste presente | `scripts/testar_<modulo>.py` |
| 5 | Workflow presente | `.github/workflows/<modulo>.yml` |
| 6 | Saídas declaradas existem como caminho | constantes `OUT_*` no código |
| 7 | Saídas publicadas pelo workflow | caminhos de `OUT_*` aparecem no bloco `path:` do `upload-artifact` |
| 8 | Seeds/entradas resolvidos | cada `SEED_*`/arquivo lido existe OU está classificado como externo em `config/system_freeze_rules.yaml` |

Ausência de qualquer item entre 3 e 8, quando o módulo os exige, rebaixa o
status para `PARCIAL` e gera ação corretiva rastreável.

## Fontes primárias obrigatórias de leitura
- `src/fito_aimm/*.py`
- `config/*.yaml`
- `.github/workflows/*.yml`
- `scripts/testar_*.py`
- `data/reference/*`, `data/manual/*`, `data/evidence/*` (quando citados por
  código como `SEED_*` ou entrada de leitura)
- `docs/contracts/*` (contrato canônico de indicador, quando o módulo produz
  payload de indicador)

## Entregáveis obrigatórios
### A) `docs/MODULE_PIPELINE_AUDIT_FACTUAL.md`
Seções mínimas:
1. Resumo executivo factual (máx. 12 bullets)
2. Inventário de módulos auditados (com classificação)
3. Tabela de completude "Módulo → Requisitos 1..8 → Status"
4. Módulos completos hoje sem novo desenvolvimento
5. Módulos parciais e o que falta em cada um
6. Riscos de regressão e dependências entre módulos
7. Decisão recomendada de priorização de fechamento

### B) `docs/MODULE_PIPELINE_EVIDENCE_TABLE.csv`
Colunas obrigatórias (delimitador `;`, encoding `utf-8-sig`):
`modulo;requisito;status;arquivo;evidencia;impacto;acao_recomendada`

### C) `docs/MODULE_PIPELINE_GAPS.md`
Seções:
- Lacunas por módulo (id, tema, descrição, criticidade)
- Impacto no pipeline AIMM
- Ações concretas de fechamento

## Critérios de aceite (hard gate)
Não concluir se faltar:
- classificação explícita de cada módulo de negócio;
- evidência de arquivo em toda afirmação de presença/ausência;
- resposta explícita, por módulo, à pergunta "tríade completa? (sim/não)";
- lista de saídas não publicadas por workflow (quando houver);
- plano de fechamento de lacunas com ação concreta.

## Regra final
Se não houver evidência suficiente para afirmar algo, registrar literalmente:
**"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.
