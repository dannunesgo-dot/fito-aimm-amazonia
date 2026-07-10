# UI Visual Guidelines — Auditoria Factual AIMM

> **Data da auditoria:** 2026-07-10  
> **Branch base:** `main` (copilot/origincopilotresearch-aimm-calculator-analysis)  
> **Método:** leitura direta de código-fonte, configs e seeds — sem inferência.

---

## 1. Resumo executivo factual (bullets)

1. **Paleta oficial de cores AIMM: NÃO CONFIRMADA** como padrão oficial documentado. Existem cores definidas programaticamente no módulo `aimm_communication.py`, mas sem referência a um sistema de design ou guia de estilo publicado.
2. **Legendas oficiais de gráficos/mapas/tabelas: NÃO CONFIRMADAS** como sistema de legendas documentado. Valores de `faixa_score` (`muito_baixo` a `muito_alto`) existem no engine mas não há legenda visual vinculada.
3. O módulo `aimm_communication.py` gera HTML com CSS inline e SVG editável — único artefato com definição de cores no repositório.
4. Nenhum arquivo de design system, token CSS, Figma ou guia de estilo foi encontrado no repositório analisado.
5. Nenhuma variável CSS (`var(--*)`) ou arquivo de tokens de design foi encontrado.
6. A paleta de cores presente no HTML gerado é baseada em classes Tailwind-like (`#111827`, `#f9fafb`, `#fffbeb`, `#991b1b`, `#1d4ed8`, `#166534`, `#92400e`) definidas inline em `aimm_communication.py` linhas 119–135.
7. Semântica visual de status (erro/alerta/bloqueio) existe no HTML via classes CSS (`.risco`, `.bloqueio`, `.monitoramento`) mas não há documentação formal dessas classes como padrão visual AIMM.
8. Regras de confiabilidade e incerteza no visual: o engine (`aimm_engine.py` linha 58–64) define faixas de score (`muito_baixo` a `muito_alto`), mas **não há visualização diferenciada por nível de confiança na UI**.
9. Acessibilidade (contraste, rótulos, fallback): NÃO COMPROVADO NO REPOSITÓRIO ANALISADO — ausente declaração de requisitos de acessibilidade.
10. Os artefatos visuais (`outputs/visuals/aimm_dashboard_executivo.html`, `aimm_dashboard_cards.svg`, `aimm_dashboard_flow.mmd`) são gerados por código, mas o status de revisão humana é `pendente` em todos os itens da checklist (`data/reference/aimm_visual_review_checklist_seed.csv`).
11. O seed `data/reference/aimm_visual_layout_seed.csv` documenta 5 formatos de saída (HTML, SVG, Mermaid, Markdown, JSON), mas não define paleta, tokens ou sistema de legendas.
12. A trava metodológica ("Score preliminar, não usar como decisão final") aparece nos artefatos HTML e SVG, conforme exigido pelas regras de visualização em `config/aimm_communication_rules.yaml` linhas `regras_visualizacao`.

---

## 2. Inventário de guias visuais encontrados

| Artefato | Arquivo de origem | Status | Observação |
|---|---|---|---|
| HTML executivo | `outputs/visuals/aimm_dashboard_executivo.html` | PARCIAL | Gerado por código; revisão humana pendente |
| SVG cards | `outputs/visuals/aimm_dashboard_cards.svg` | PARCIAL | Gerado por código; revisão humana pendente |
| Mermaid flow | `outputs/visuals/aimm_dashboard_flow.mmd` | PARCIAL | Gerado por código; editável |
| Briefing MD | `outputs/reports/aimm_communication_brief.md` | PARCIAL | Gerado por código |
| Seed visual layout | `data/reference/aimm_visual_layout_seed.csv` | IMPLEMENTADO | Define apenas formatos de saída, não paleta |
| Visual review checklist | `data/reference/aimm_visual_review_checklist_seed.csv` | PARCIAL | Checklist com status `pendente` em todos os itens |
| Regras de comunicação | `config/aimm_communication_rules.yaml` | IMPLEMENTADO | Regras de visualização textuais, sem tokens de cor |

Nenhum design system, style guide, CSS file independente ou arquivo de tokens foi encontrado no repositório.

---

## 3. Paleta oficial — **NÃO CONFIRMADA**

**Status: NÃO CONFIRMADA como padrão oficial documentado.**

A única definição de cores no repositório está em `src/fito_aimm/aimm_communication.py`, linhas 119–135, embutidas como CSS inline no HTML gerado:

| Classe/uso | Valor hex | Contexto |
|---|---|---|
| body color / texto geral | `#111827` | linhas 119, 188 |
| background body | `#ffffff` | linha 119 |
| card background | `#f9fafb` | linha 124 |
| warning background | `#fffbeb` | linha 122 |
| warning border | `#92400e` | linhas 122, 129, 196 |
| card border | `#374151` | linhas 124, 212 |
| `.score` border-left | `#1f2937` | linha 126 |
| `.risco` border-left | `#991b1b` | linha 127 |
| `.monitoramento` border-left | `#1d4ed8` | linha 128 |
| `.bloqueio` border-left | `#92400e` | linha 129 |
| `.processo` border-left | `#166534` | linha 130 |
| th background | `#e5e7eb` | linha 133 |
| dim row background | `#f3f4f6` | linha 223 |
| table border | `#9ca3af` | linha 132 |
| message border | `#d1d5db` | linha 134 |
| code background | `#f3f4f6` | linha 135 |

Esses valores correspondem à paleta do Tailwind CSS (`gray-*`, `red-800`, `blue-700`, `green-800`, `amber-800`), mas **não há referência explícita ao Tailwind nem declaração de que esses valores constituem a paleta oficial AIMM** em nenhum arquivo de configuração, design doc ou README.

**Paleta oficial confirmada?** **NÃO**

---

## 4. Legendas oficiais — **NÃO CONFIRMADAS**

**Status: NÃO CONFIRMADAS como sistema de legendas documentado.**

### 4.1 Faixas de score (parcialmente implementadas no engine)

O arquivo `src/fito_aimm/aimm_engine.py` linhas 58–64 define faixas de score:

| Faixa | Valor |
|---|---|
| `muito_baixo` | ≤ 20 |
| `baixo` | 21–40 |
| `medio` | 41–60 |
| `alto` | 61–80 |
| `muito_alto` | > 80 |

Mesma função replicada em `species_selection.py` linhas 68–76 e `product_pathway.py` linhas 70–78.

Entretanto, **não há mapeamento dessas faixas a cores ou ícones visuais** em nenhum arquivo do repositório. O HTML gerado não exibe cores diferenciadas por faixa de score.

### 4.2 Status de cards

Os cards do dashboard (`aimm_dashboard.py` linha `"status": "preliminar"`) exibem status como texto, sem legenda visual por status.

### 4.3 Legendas de mapas

NÃO COMPROVADO NO REPOSITÓRIO ANALISADO — não há arquivos de legenda de mapa, nenhum sistema de simbologia GIS documentado além do GeoPackage de Manaus (`data/raw/gis/municipio_manaus_1302603.gpkg`).

**Legendas oficiais confirmadas?** **NÃO**

---

## 5. Regras visuais por estado

| Estado | Regra documentada | Arquivo/linha | Status |
|---|---|---|---|
| Score preliminar | Trava textual obrigatória em todos os artefatos | `config/aimm_communication_rules.yaml:regras_visualizacao[0]` | IMPLEMENTADO |
| Bloqueio/lacuna | Destaque visual `.bloqueio` (border `#92400e`) | `aimm_communication.py:129` | PARCIAL |
| Risco | Destaque visual `.risco` (border `#991b1b`) | `aimm_communication.py:127` | PARCIAL |
| Monitoramento | Destaque visual `.monitoramento` (border `#1d4ed8`) | `aimm_communication.py:128` | PARCIAL |
| Erro (validação) | Mensagem textual; sem estilo visual dedicado | `aimm_engine.py:validate_inputs` | PARCIAL |
| Confiabilidade no visual | Nenhuma diferenciação visual por nível de confiança | — | AUSENTE |
| Acessibilidade | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO | — | AUSENTE |
| Fallback visual | NÃO COMPROVADO NO REPOSITÓRIO ANALISADO | — | AUSENTE |

---

## 6. Conflitos por branch

| Branch | Conflito identificado | Evidência |
|---|---|---|
| `main` | Cores embutidas em código Python (não externalizáveis sem mudança de código) | `aimm_communication.py:119–135` |
| `origin/copilot/research-interface-calculadora-aimm-fito` | Branch de pesquisa (EXPERIMENTAL); propõe interface web sem implementação de paleta | `docs/FEATURE_STATUS_BY_BRANCH.md` |
| `origin/refactor/phase2` | Refatoração arquitetura (PENDING); nenhuma mudança de guia visual documentada | `docs/FEATURE_STATUS_BY_BRANCH.md` |
| `origin/refactor/phase1` | Refatoração camadas (PENDING); sem guia visual | `docs/FEATURE_STATUS_BY_BRANCH.md` |
| `origin/copilot/research-data-ingestion-analysis` | EXPERIMENTAL; sem definições visuais | `docs/FEATURE_STATUS_BY_BRANCH.md` |

Não há conflito direto entre branches sobre paleta ou legendas — pois nenhuma branch define padrão visual explícito.

---

## 7. Decisão recomendada para MVP

1. **Formalizar as cores existentes** em `aimm_communication.py:119–135` como paleta oficial AIMM v1.0 em arquivo `docs/UI_DESIGN_TOKENS.md` (não existe; precisa ser criado).
2. **Criar mapeamento faixa-de-score → cor** em arquivo de config separado (hoje a função `score_band` não tem cor associada).
3. **Externalizar CSS** do HTML gerado para arquivo standalone, permitindo edição sem alterar código Python.
4. **Definir legendas formais** para gráficos de dimensão AIMM, mapa territorial e tabela de indicadores — hoje NÃO COMPROVADO NO REPOSITÓRIO ANALISADO.
5. **Cheklist de acessibilidade**: verificar contraste das cores existentes — `#111827` sobre `#f9fafb` passa em WCAG AA, mas não foi declarado formalmente.

---

## 8. Riscos e pendências

| Risco | Severidade | Ação |
|---|---|---|
| Paleta embutida em código Python — difícil de manter sem refatoração | Alta | Externalizar para config ou CSS |
| Sem legenda de mapa para municípios além de Manaus | Alta | Criar template de simbologia GIS |
| Revisão humana de todos os artefatos visuais: status `pendente` | Alta | Concluir revisão per `aimm_visual_review_checklist_seed.csv` |
| Sem padrão de acessibilidade declarado | Média | Declarar requisitos mínimos WCAG AA |
| Faixas de score sem cor associada na UI | Média | Criar mapeamento faixa→cor em config |
