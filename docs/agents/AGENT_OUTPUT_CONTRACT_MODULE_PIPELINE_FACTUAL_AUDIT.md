# AGENT OUTPUT CONTRACT — MODULE/PIPELINE FACTUAL AUDIT (AIMM)

## Princípio
A saída do agente deve ser auditável, rastreável e reexecutável. Cada afirmação
crítica remete a um arquivo do repositório.

## Arquivos obrigatórios de saída

### 1) `docs/MODULE_PIPELINE_AUDIT_FACTUAL.md`
Estrutura obrigatória:
1. Cabeçalho de rastreabilidade (repositório, commit auditado, data).
2. Resumo executivo factual (máx. 12 bullets).
3. Inventário de módulos auditados (negócio × utilitário-base).
4. Tabela de completude "Módulo → Requisitos 1..8 → Status".
5. Módulos completos hoje (sem novo desenvolvimento).
6. Módulos parciais e o que falta em cada um.
7. Saídas escritas por código e não publicadas por workflow.
8. Riscos de regressão e dependências entre módulos.
9. Decisão recomendada de priorização.

### 2) `docs/MODULE_PIPELINE_EVIDENCE_TABLE.csv`
- Delimitador: `;`  · Encoding: `utf-8-sig`.
- Colunas obrigatórias, nesta ordem:
  `modulo;requisito;status;arquivo;evidencia;impacto;acao_recomendada`
- Valores permitidos para `status`:
  `IMPLEMENTADO`, `PARCIAL`, `AUSENTE`, `EXPERIMENTAL`, `CONFLITANTE`,
  `NAO_COMPROVADO`.
- Valores permitidos para `requisito` (chave curta):
  `codigo`, `execucao`, `regras_yaml`, `teste`, `workflow`, `saidas_declaradas`,
  `saidas_publicadas`, `seeds_entradas`.

### 3) `docs/MODULE_PIPELINE_GAPS.md`
Seções obrigatórias:
1. Lacunas por módulo (`id_lacuna`, `tema`, `descricao`, `criticidade`).
2. Impacto no pipeline AIMM.
3. Ações concretas de fechamento.
- `criticidade` ∈ {`alta`, `media`, `baixa`}.
- `id_lacuna` no padrão `GAP_MODAUDIT_NNN`.

---

## Regras de evidência obrigatória
- Toda afirmação crítica deve conter: arquivo, evidência descritiva e, quando
  aplicável, linha(s).
- Se não houver evidência, usar o literal:
  **"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.
- É proibido afirmar presença de workflow/teste/saída sem citar o caminho.

## Critérios de aceite da saída
A saída é rejeitada se:
- faltar qualquer arquivo obrigatório;
- houver afirmação de presença/ausência sem arquivo;
- não houver status explícito por módulo;
- não houver a lista de saídas não publicadas por workflow;
- não houver diagnóstico de lacunas com ação concreta;
- o commit auditado não estiver registrado.

## Formato de linguagem
- Objetivo, técnico, sem adjetivação vaga.
- Siglas por extenso na primeira ocorrência (ex.: Organização da Sociedade Civil
  — OSC; Análise de Investimento e Maturidade de Mercado — AIMM).
- Sem "melhores práticas" genéricas sem vínculo factual ao repositório.
