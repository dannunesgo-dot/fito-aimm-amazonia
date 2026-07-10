\# AGENT RUNBOOK — UI FACTUAL AUDIT (AIMM)



\## Objetivo operacional

Executar auditoria factual reprodutível da UI AIMM e integração com sistema real, sem inferência.



\## Pré-condições

\- Branch base sincronizada (`main` atualizada)

\- Arquivo de brief disponível:

&#x20; - `docs/agents/BRIEF\_UI\_FACTUAL\_AUDIT.md`

\- Artefatos de auditoria prévia disponíveis quando houver:

&#x20; - `.pipeline/branches\_inventory.txt`

&#x20; - `.pipeline/branch\_diff\_summary.csv`

&#x20; - `.pipeline/implementation\_grep.txt`



\---



\## Etapa 1 — Preparar contexto de análise

1\. Atualizar refs:

&#x20;  - `git fetch --all --prune`

2\. Confirmar branches alvo do brief.

3\. Confirmar existência dos arquivos primários no `main`.



\## Etapa 2 — Extração factual

1\. Ler fontes obrigatórias:

&#x20;  - `app.py`, `Caddyfile`, `run-local.ps1`, `status-local.ps1`

&#x20;  - `src/fito\_aimm/\*.py`

&#x20;  - `docs/\*.md`

&#x20;  - `.github/workflows/\*.yml`

&#x20;  - `config/\*.yaml`

&#x20;  - `data/reference/\*`

2\. Registrar evidência por item:

&#x20;  - arquivo

&#x20;  - linhas

&#x20;  - descrição objetiva

&#x20;  - status (IMPLEMENTADO/PARCIAL/AUSENTE/CONFLITANTE)



\## Etapa 3 — Verificação visual (sem inferência)

1\. Buscar paleta oficial explicitamente em código/docs.

2\. Buscar legendas oficiais de gráficos/mapas/tabelas.

3\. Se não encontrar, registrar “NÃO COMPROVADO”.

4\. Não propor cores finais sem evidência implementada.



\## Etapa 4 — Aderência da arquitetura UI proposta

Mapear blocos:

\- Busca/Filtros

\- Tabela

\- Detalhes

\- Visualizações

\- Exportação



Para cada bloco:

\- endpoint existente?

\- payload disponível?

\- artefato produtor?

\- gap de implementação?



\## Etapa 5 — Cobertura municipal mínima

Verificar cobertura factual para:

\- Manaus (1302603)

\- Benjamin Constant (1300607)

\- Belém (1501402)

\- Santarém (1506807)



Listar campos disponíveis/faltantes e impacto na UI.



\## Etapa 6 — Gerar entregáveis

Gerar obrigatoriamente:

1\. `docs/UI\_VISUAL\_GUIDELINES\_FACTUAL.md`

2\. `docs/UI\_ARCHITECTURE\_ALIGNMENT\_FACTUAL.md`

3\. `docs/UI\_VISUAL\_EVIDENCE\_TABLE.csv`

4\. `docs/UI\_MUNICIPAL\_COVERAGE\_GAPS.md`



\## Etapa 7 — Controle de qualidade final

Checklist:

\- \[ ] Toda afirmação com arquivo + linha

\- \[ ] Paleta oficial: status explícito (confirmada/não confirmada)

\- \[ ] Legendas oficiais: status explícito

\- \[ ] Gaps por bloco da UI

\- \[ ] Gaps municipais com ação concreta

\- \[ ] Sem inferência não comprovada



\## Resultado esperado

Pacote factual que permita execução do roadmap UI sem retrabalho e sem decisões baseadas em suposição.

