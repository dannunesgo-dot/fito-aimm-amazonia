# ESTADO DO SISTEMA — TRAVAMENTO PARA RETOMADA (Camada 2)

## Cabeçalho
- Repositório: `https://github.com/dannunesgo-dot/fito-aimm-amazonia`
- Commit de fechamento da Camada 1: `4d4de7f`
- Data: 2026-07-11
- Propósito: registrar o que está APROVADO, o que está PENDENTE e o que foi
  ARQUIVADO, para retomada progressiva sem perda de progresso.

> **Regra de retomada:** ao iniciar a próxima sessão, leia este documento antes
> de qualquer produção. Ele é a fonte de verdade sobre onde o sistema está.

---

## 1. TRAVADO E APROVADO (não refazer, não reabrir)

### 1.1 Decisões metodológicas travadas
| Decisão | Valor travado | Origem |
|---|---|---|
| Metodologia de cálculo | AIMM oficial IFC (Guidance Note, março 2026) | Norma IFC |
| Conversão rating→pontos | Very Strong 50 / Strong 30 / Moderate 12 / Marginal 4 | Tabela 6 da norma |
| Ajuste de risco | Unqualified 1,00 / Qualified 0,75 (binário) | Norma |
| Arredondamento | Cada eixo ao múltiplo de 2 mais próximo | Norma |
| Faixas de score | Excellent 72 / **Good 43** / Satisfactory 22 / Low 8 | Decisão do usuário: Tabela 6 |
| Ajuste clima/inclusão | +10 pontos (critério estrito) | Norma |
| Nome do motor | `fitomais_aimm_engine` | Decisão do usuário |
| Motor antigo | Aposentado, preservado em `docs/deprecated/` | Decisão do usuário |
| Dashboard mostra | Dois eixos + score final | Decisão do usuário |

### 1.2 Escopo temático travado — "Fito+" ≠ fitoterápicos
O escopo Fito+ é **multi-produto**, por diversificação estratégica (produtos,
mercados, clientes, fornecedores). Cinco eixos:
- **a) Medicamentos:** fitoterápicos (medicamentos fitoterápicos e tradicionais
  fitoterápicos), homeopáticos, substâncias isoladas de origem vegetal,
  substâncias isoladas modificadas por semissíntese, insumos ativos vegetais
  associados a não vegetais, excipientes e adjuvantes de origem vegetal.
- **b) Cosméticos:** grau I (sem indicação), grau II (com indicação),
  artesanais, não orgânicos, orgânicos.
- **c) Suplementos alimentares e alimentos.**
- **d) Alimentos para fins especiais:** infantis (fórmulas, transição, base de
  cereais), fórmulas para nutrição enteral, fórmulas dietoterápicas para erros
  inatos do metabolismo.
- **e) Cadeia de suprimentos:** matérias-primas vegetais, insumos farmacêuticos
  vegetais (ativos, adjuvantes, excipientes), ingredientes, moléculas isoladas/
  modificadas/purificadas, máquinas/equipamentos/estruturas, áreas preparadas.

### 1.3 Camada 1 — FECHADA E VALIDADA
- **Motor:** `src/fito_aimm/fitomais_aimm_engine.py` — implementa a mecânica
  oficial. Validado por **7 casos de teste** derivados da norma, incluindo o
  exemplo oficial "Strong-UQ + Strong-Q = 52 (Good)".
- **Dashboard:** `src/fito_aimm/aimm_dashboard.py` — religado ao motor oficial.
  Mostra os dois eixos (Project Outcome, Market Outcome), o score final, a faixa
  e a memória de cálculo.
- **Comunicação:** `src/fito_aimm/aimm_communication.py` — religado; consome a
  visão por eixo.
- **Cadeia validada ponta a ponta:** motor → dashboard → comunicação, 0 erros.
- **Workflow ativo:** `fitomais_aimm_engine.yml` (valida os 7 casos no Actions).

### 1.4 Agentes de diagnóstico (construídos e validados no Actions)
| Agente | Função | Estado |
|---|---|---|
| `module_pipeline_audit` | Completude estrutural dos módulos | 18 módulos: 10 IMPLEMENTADO, 8 PARCIAL |
| `architecture_analysis` | Arquitetura, APIs, condições técnicas | 19 módulos, 6 APIs, 6 endpoints, 9 arestas |
| `branch_comparison` | Compara qualquer branch com main | 4 branches comparados |

---

## 2. ARQUIVADO (obsoleto/errado — preservado, não usar)

Em `docs/deprecated/`:
| Arquivo | Motivo |
|---|---|
| `aimm_engine.py` | Motor metodologicamente ERRADO (média ponderada 0–100; a norma usa conversão de ratings). Não usar. |
| `aimm_dashboard.py` | Versão antiga; mostrava scores por dimensão (conceito inexistente na norma). |
| `testar_aimm_engine.py` | Teste do motor errado. |
| `README.md` | Explica cada descontinuação. |

**Removidos do código ativo:** `src/fito_aimm/aimm_engine.py`,
`scripts/testar_aimm_engine.py`, `.github/workflows/aimm_engine.yml`.
Verificado: **nenhuma referência ao motor antigo em código ativo**.

---

## 3. PENDENTE — o que a Camada 2 precisa resolver

### 3.1 A dependência crítica (o motivo da Camada 2 existir)
O motor calcula o score **a partir dos ratings**. Ele NÃO deriva os ratings.
Hoje, os ratings vêm de `data/reference/aimm_ratings_input_seed.csv`, com valores
marcados **`PROVISORIO_EXEMPLO`** — e todo o sistema propaga o alerta
`provisorio_nao_validado`. O score atual (16, Low) é um exemplo mecânico, **não
é avaliação real do projeto Fito+ Amazônia**.

A Camada 2 deve produzir os ratings reais, o que exige, conforme a norma IFC:
- **Project Outcome rating** = combinação de *development gap* (contexto do país/
  território) + *project intensity* (ambição do projeto). Ambos precisam de
  indicadores com benchmark.
- **Market Outcome rating** = combinação de *market stage* (estágio do mercado
  Fito+) + *catalytic effects* (inovação × escalabilidade).
- **Risco** de cada eixo: Unqualified ou Qualified.

### 3.2 Fontes de dados mapeadas (Camada 3, a construir depois)
- Comércio exterior: Comtrade, Comexstat, Siscomex, Comex 360.
- Sector frameworks do IFC: busca direcionada (proxies para o framework Fito+).
- World Bank Data: contexto internacional e benchmark de gap
  (ver `docs/WORLDBANK_DATA_ACCESS_ANALYSIS.md`).
- IBGE (SIDRA, localidades, geoftp) e MapaOSC/IPEA: já integrados.
- GIS: contorno territorial.
- Ingestão documental: normas sanitárias, legislação, normas ambientais,
  programas de governo e de Estado.

### 3.3 Dívida técnica pré-existente (NÃO criada por nós; registrada)
- ~26 scripts `rodada_4_XX_*` dependem de `google.oauth2` / `googleapiclient`
  (integração Google Drive), que **não constam do `requirements.txt`**. Eles
  falham em ambiente limpo por dependência ausente. Não afetam a cadeia AIMM.
  **Verificado:** nenhum deles referencia o motor antigo; a Camada 1 não os
  quebrou.
- 55 workflows ativos, muitos de rodadas históricas. Não quebrados, mas é volume
  alto. Decisão de arquivamento **pendente do usuário** — não foi feita
  autonomamente.

### 3.4 Branches com trabalho não aproveitado (ver `docs/BRANCH_COMPARISON_SUMMARY.md`)
- `refactor/phase2`: modelos Pydantic + validators (0 ruído; engine 14+/1-).
  Pode ser útil na Camada 2 (tipagem dos indicadores).
- `copilot/research-aimm-calculator`: modularização do MapaOSC (engine 82+/18-).
- Sobreposição conflitante de validators entre os dois: exige escolher UM.
- Todos 45–48 commits atrás do main.

---

## 4. PROTOCOLO DE RETOMADA (Camada 2)

1. **Ler este documento** antes de qualquer produção.
2. **Não reabrir** o que está na Seção 1 (travado).
3. **Não usar** o que está na Seção 2 (arquivado).
4. Começar pela pergunta central da Camada 2:
   *"Quais indicadores, com quais benchmarks, determinam que um projeto Fito+
   tem gap Large e intensidade Above Average?"*
5. Estruturar o framework por **eixo de escopo Fito+** (Seção 1.2), não por
   "fitoterápicos".
6. Manter a fronteira: o sistema **carrega** o julgamento; o julgamento
   (quando é Strong, quando é Moderate) é do especialista.

## 5. TESTE DE SANIDADE (rodar ao retomar)
```bash
# Deve dar 7/7 aprovados:
python scripts/testar_fitomais_aimm_engine.py
# Deve rodar sem erro e alertar "provisorio_nao_validado":
python scripts/testar_aimm_dashboard.py
```
Se algum falhar, algo regrediu — investigar antes de avançar.
