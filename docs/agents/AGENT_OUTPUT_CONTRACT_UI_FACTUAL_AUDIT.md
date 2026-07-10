\# AGENT OUTPUT CONTRACT — UI FACTUAL AUDIT (AIMM)



\## Princípio

A saída do agente deve ser auditável, rastreável e reexecutável.



\## Arquivos obrigatórios de saída



\### 1) docs/UI\_VISUAL\_GUIDELINES\_FACTUAL.md

Estrutura obrigatória:

1\. Resumo executivo factual (máx. 12 bullets)

2\. Inventário de guias visuais encontrados

3\. Paleta oficial (confirmada / não confirmada)

4\. Legendas oficiais (confirmadas / não confirmadas)

5\. Regras visuais por estado (erro, alerta, bloqueio, confiabilidade)

6\. Conflitos por branch

7\. Decisão recomendada para MVP

8\. Riscos e pendências



\### 2) docs/UI\_ARCHITECTURE\_ALIGNMENT\_FACTUAL.md

Estrutura obrigatória:

1\. Tabela “Bloco UI -> Endpoint -> Status -> Evidência”

2\. Componentes já operacionais

3\. Lacunas para MVP

4\. Sequência de implementação (2 semanas)

5\. Gates de release



\### 3) docs/UI\_VISUAL\_EVIDENCE\_TABLE.csv

Colunas obrigatórias:

\- `tema`

\- `status`

\- `branch`

\- `arquivo`

\- `linhas`

\- `evidencia`

\- `impacto\_ui`

\- `acao\_recomendada`



Valores permitidos para `status`:

\- `IMPLEMENTADO`

\- `PARCIAL`

\- `AUSENTE`

\- `EXPERIMENTAL`

\- `CONFLITANTE`

\- `NAO\_COMPROVADO`



\### 4) docs/UI\_MUNICIPAL\_COVERAGE\_GAPS.md

Seções obrigatórias:

1\. Situação por município (Manaus, Benjamin Constant, Belém, Santarém)

2\. Campos presentes

3\. Campos ausentes

4\. Impacto na interface

5\. Ações para fechar lacunas



\---



\## Regras de evidência obrigatória

\- Toda afirmação crítica deve ter:

&#x20; - arquivo

&#x20; - linha(s)

&#x20; - trecho descritivo

\- Se não houver evidência: usar literal

&#x20; - `NÃO COMPROVADO NO REPOSITÓRIO ANALISADO`



\## Critérios de aceite da saída

A saída é rejeitada se:

\- faltar qualquer arquivo obrigatório;

\- houver afirmações sem rastreabilidade;

\- não houver status explícito de paleta e legendas;

\- não houver mapeamento UI x endpoints;

\- não houver diagnóstico municipal mínimo.



\## Formato de linguagem

\- Objetivo, técnico, sem adjetivação vaga.

\- Sem “melhores práticas” genéricas sem vínculo factual.

