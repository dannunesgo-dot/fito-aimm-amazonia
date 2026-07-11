# AGENT OUTPUT CONTRACT — BRANCH COMPARISON (AIMM)

## Princípio
A saída é auditável, rastreável e reexecutável. Cada afirmação remete a branch +
arquivo + tipo de mudança. Ruído é sempre isolado do conteúdo útil.

## Arquivos obrigatórios de saída

### 1) `docs/BRANCH_COMPARISON_<branch>.md` (um por branch comparado)
`<branch>` no nome do arquivo usa `_` no lugar de `/` (ex.:
`BRANCH_COMPARISON_refactor_phase2.md`).
Estrutura obrigatória:
1. Cabeçalho de rastreabilidade (branch, commit, ahead, behind, data).
2. Resumo factual (útil × ruído; impacto no núcleo sim/não).
3. Arquivos adicionados (não-ruído), por categoria.
4. Arquivos modificados; módulos do núcleo destacados com magnitude.
5. Arquivos removidos.
6. Módulos Python novos com classes/funções públicas.
7. Ruído isolado (contagem + amostra de até 5).
8. Conflitos potenciais (se houver) ou "nenhum identificado".

### 2) `docs/BRANCH_COMPARISON_TABLE.csv` (consolidada)
- Delimitador `;` · Encoding `utf-8-sig`.
- Colunas, nesta ordem:
  `branch;arquivo;tipo;categoria;impacto_nucleo;observacao`
- `tipo` ∈ {`ADICIONADO`, `REMOVIDO`, `MODIFICADO`, `RUIDO`}.
- `categoria` ∈ {`modulo_python`, `documento`, `config`, `workflow`, `dado`,
  `outro`}.
- `impacto_nucleo` ∈ {`sim`, `nao`}.

---

## Regras de evidência obrigatória
- Toda afirmação de mudança: branch + arquivo + tipo (A/M/D/RUIDO).
- Magnitude de modificação em módulo-núcleo: linhas +/- de `git diff --stat`.
- Ruído nunca é omitido nem contado como conteúdo — é isolado e quantificado.
- Sem evidência: literal **"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.

## Critérios de aceite da saída
Rejeitada se:
- faltar o `.md` do branch comparado ou a linha na tabela CSV;
- algum arquivo do diff ficar sem classificação;
- ruído não estiver isolado/quantificado;
- faltar resposta "impacto no núcleo? (sim/não)";
- faltar lista de módulos novos com classes/funções;
- ahead/behind não estiver registrado.

## Formato de linguagem
- Objetivo, técnico, sem adjetivação vaga.
- Siglas por extenso na primeira ocorrência.
- Sem juízo de mérito ("melhor", "pior") — o agente descreve o que muda, não
  recomenda o que fazer. A decisão de aproveitamento é do usuário.
