\# Contract Change Policy — AIMM Canonical Indicator Payload



\## Escopo

Esta política governa alterações do contrato canônico:

\- `docs/contracts/indicator\_canonical.schema.json`

\- `docs/contracts/indicator\_examples.json`



\## Objetivo

Evitar quebra de integração entre:

\- backend (APIs),

\- UI da calculadora AIMM,

\- pipelines de ingestão,

\- relatórios e visualizações.



\---



\## Versionamento

Usar SemVer:

\- \*\*MAJOR\*\*: quebra compatibilidade (remove/renomeia campo obrigatório)

\- \*\*MINOR\*\*: adiciona campo opcional ou enum sem quebra

\- \*\*PATCH\*\*: correção documental/exemplo sem alterar estrutura



Versão vigente inicial: \*\*v1.0.0\*\*



\---



\## Regras obrigatórias para mudança

1\. Toda alteração de schema exige PR dedicado (`scope: contracts`).

2\. PR deve atualizar:

&#x20;  - schema

&#x20;  - exemplos

&#x20;  - changelog no próprio PR

3\. PR deve declarar impacto em endpoints:

&#x20;  - `/api/indicators`

&#x20;  - `/api/indicators/{id}`

&#x20;  - `/api/indicators/{id}/series`

&#x20;  - `/api/export`

4\. Campos obrigatórios não podem ser removidos sem versão MAJOR.

5\. Enum novo só entra com descrição de mapeamento em adapters de fonte.

6\. Mudança de formato de data/período exige migração documentada.



\---



\## Checklist de aprovação (gate)

\- \[ ] Schema válido (JSON Schema draft 2020-12)

\- \[ ] Exemplos válidos contra schema

\- \[ ] Compatibilidade retroativa validada

\- \[ ] Impacto em UI mapeado

\- \[ ] Impacto em relatórios mapeado

\- \[ ] Revisão de domínio AIMM aprovada

\- \[ ] Revisão técnica aprovada



\---



\## Regras de verdade operacional

\- Fonte visual (cores/legendas) \*\*não\*\* pertence ao schema canônico.

\- Regras de visualização devem ser definidas em documento separado validado por guia AIMM.

\- Contrato canônico é agnóstico à paleta e tema visual.



\---



\## Campos mínimos mandatórios (não remover)

`id, nome, dimensao, componente, papel, valor, unidade, periodo, territorio, territorio\_tipo, territorio\_codigo, fonte, fonte\_url, confiabilidade, metodologia\_ref, origem\_api, status\_dado, versao\_metodologia, ultima\_atualizacao`



\---



\## Extensibilidade

\- Novas APIs (futuras) devem implementar adapter para o contrato canônico.

\- Dados não padronizados entram em `metadata` (opcional) até normalização formal.



\---



\## Governança

Owner recomendado:

\- Produto AIMM + Arquitetura Técnica + Operação de Dados



Periodicidade de revisão:

\- quinzenal durante MVP

\- mensal após estabilização

