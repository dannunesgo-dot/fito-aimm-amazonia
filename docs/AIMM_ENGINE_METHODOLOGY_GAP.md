# DESCOMPASSO METODOLÓGICO DO MOTOR AIMM — Diagnóstico e Especificação

## Para quem lê este documento
Este documento compara o motor de cálculo atual do sistema (`aimm_engine.py`)
com a metodologia oficial do IFC (International Finance Corporation — Corporação
Financeira Internacional, do Grupo Banco Mundial). É escrito para ser
compreensível por especialista em políticas públicas, não apenas por programador:
a parte a validar é a **lógica de negócio** (a metodologia faz sentido?), não a
implementação.

## Fonte oficial (verbatim)
- Documento: "AIMM Guidance Note", IFC, março de 2026.
- URL: https://www.ifc.org/content/dam/ifc/doc/latest/aimm-general-guidance-note.pdf
- Trechos citados abaixo são idênticos ao original (em inglês, como na fonte).

---

## 1. Resumo executivo (o essencial em 6 pontos)
1. O motor atual **não** implementa a mecânica de cálculo do AIMM oficial.
2. O motor atual usa **média ponderada de notas 0–100** por dimensão, com
   penalização de risco proporcional. A norma oficial usa **conversão de ratings
   qualitativos em pontos fixos**, somados.
3. O próprio código atual se declara "preliminar" e "não representa AIMM final
   validado" (`aimm_engine.py`, campo `interpretacao`) — foi construído como
   protótipo consciente, não como motor definitivo.
4. Corrigir isto é a **fundação** de todo o sistema: o score alimenta relatórios,
   que alimentam a interface. Erro na fundação propaga-se a tudo.
5. O motor correto é **pequeno e determinístico**: 6 ratings, uma tabela de
   conversão, um fator de risco binário, uma soma, um arredondamento. É
   blindável contra bug e testável contra exemplos da própria nota do IFC.
6. Este documento serve a três usos: especificação para construir o motor
   correto; registro rastreável da correção; e evidência, para o IFC, de que o
   sistema segue a norma.

---

## 2. Como o AIMM oficial calcula (a mecânica correta)

### 2.1 A estrutura de avaliação (não são "centenas de indicadores")
A avaliação tem **dois eixos**, cada um com componentes:
- **Project Outcomes** (resultados do projeto): stakeholder effects,
  economy-wide effects, environmental and social effects.
- **Market Outcomes** (resultados de mercado): competitiveness, resilience,
  sustainability.

Os indicadores (as suas "20 categorias / centenas de indicadores") **não são
somados no cálculo**. Eles fundamentam os *ratings qualitativos*, e vivem nos
**sector frameworks**. Citação oficial:
> "To guide assessments and ensure objectivity across projects, IFC has
> developed detailed sector frameworks that lay out the various indicators
> (qualitative and quantitative) that could be used to assess the development
> challenge, the project's intensity in addressing it, the stage of market
> development, and the expected catalytic effects."

Ou seja: os indicadores → ratings qualitativos → pontos → score. Não há soma
direta de indicadores.

### 2.2 O cálculo do score (a mecânica exata)
**Passo 1 — Rating qualitativo.** Cada outcome recebe um de quatro ratings:
Marginal, Moderate, Strong, Very Strong.

**Passo 2 — Conversão em pontos** (Tabela 6 da nota, verbatim dos valores):
- Very Strong = 50
- Strong = 30
- Moderate = 12
- Marginal = 4

**Passo 3 — Ajuste de risco** (dois níveis apenas):
> "The AIMM system employs a two-tier risk assessment mechanism that assigns an
> 'Unqualified' (UQ) rating to low-risk dimensional assessments (no discount)
> while high-risk dimensional assessments get a 'Qualified' (Q) rating (with a
> discount of 0.25)."
- Unqualified → fator 1,00
- Qualified → fator 0,75

**Passo 4 — Soma e arredondamento.** Citação oficial:
> "The final score is the sum of the risk-adjusted points for project and market
> outcomes, individually rounded to the nearest multiple of 2."

**Passo 5 — Faixa final** (Tabela 6):
- Excellent: 72–100
- Good: 43–71
- Satisfactory: 22–42
- Low: 8–21

**Ajuste adicional:** o sistema soma 10 pontos ao score de projetos que
contribuam materialmente para clima e/ou inclusão, sob critérios estritos de
elegibilidade.

### 2.3 O exemplo oficial (nosso caso de teste principal)
A nota traz um exemplo trabalhado:
> "a project with an Unqualified rating of Strong for project outcomes will be
> assigned a score of 52 (Good)."

Cálculo: Project Strong-Unqualified = 30 × 1,00 = 30; Market Strong-Qualified =
30 × 0,75 = 22,5 → 22 (múltiplo de 2); total 30 + 22 = **52 (Good)**.

---

## 3. Como o motor ATUAL calcula (a mecânica implementada)

Evidência: `src/fito_aimm/aimm_engine.py`, funções `score_band`,
`calculate_indicator_scores`, `calculate_dimension_scores`, `calculate_overall`.

### 3.1 Faixas de score (linha 56–64)
Divide em cinco faixas de 20 em 20: ≤20 muito_baixo, ≤40 baixo, ≤60 medio,
≤80 alto, >80 muito_alto.
**Diverge da norma:** a norma tem quatro faixas (Excellent/Good/Satisfactory/Low)
com limiares 72/43/22/8, não cinco faixas de 20 em 20.

### 3.2 Score por indicador (`calculate_indicator_scores`)
Pega uma nota bruta 0–100 (`score_bruto_preliminar`) e multiplica por um fator de
confiança e um fator de prontidão de benchmark.
**Diverge da norma:** a norma não atribui nota 0–100 a indicadores individuais
nem os multiplica por fatores contínuos. Indicadores fundamentam um rating
qualitativo (Marginal/Moderate/Strong/Very Strong), não uma nota numérica.

### 3.3 Score por dimensão (`calculate_dimension_scores`)
Faz a **média aritmética** das notas ajustadas dos indicadores da dimensão.
**Diverge da norma:** não há média de indicadores na norma. Cada dimensão de
outcome recebe um rating qualitativo próprio, convertido em pontos fixos.

### 3.4 Score geral (`calculate_overall`, linha 172–200)
- Média ponderada das dimensões de "benefício" (`score_bruto`).
- Subtrai uma penalidade de risco proporcional (`1 - risk_penalty/100`).
- Multiplica por um fator de confiança (`monitor_factor`).
**Diverge da norma em três pontos:**
  (a) a norma **soma** pontos de project + market, não faz média ponderada;
  (b) o risco na norma é **binário** (fator 1,00 ou 0,75), não uma penalidade
      proporcional contínua;
  (c) não há "fator de confiança" multiplicativo na norma.

---

## 4. Tabela comparativa (lado a lado)

| Aspecto | Motor atual | Norma oficial IFC |
|---|---|---|
| Unidade de avaliação | Nota 0–100 por indicador | Rating qualitativo por outcome |
| Ratings | Não usa | Marginal / Moderate / Strong / Very Strong |
| Conversão | Nenhuma (já é número) | 4 / 12 / 30 / 50 pontos |
| Agregação | Média ponderada de dimensões | **Soma** de project + market |
| Risco | Penalidade proporcional (%) | Binário: fator 1,00 ou 0,75 |
| Confiança | Fator multiplicativo | Não existe (é parte do rating/risco) |
| Arredondamento | Não | Cada eixo ao múltiplo de 2 |
| Faixas | 5 faixas de 20 em 20 | 4 faixas: 72/43/22/8 |
| Ajuste clima/inclusão | Não | +10 pontos (critérios estritos) |

---

## 5. Especificação do motor correto (o que construir)

O motor correto recebe, para um projeto:
- Rating de **Project Outcome** (Marginal/Moderate/Strong/Very Strong) + risco
  (Unqualified/Qualified).
- Rating de **Market Outcome** (idem) + risco.
- (Opcional) elegibilidade a ajuste de clima/inclusão.

E produz:
1. Pontos de project = pontos(rating) × fator(risco), arredondado a múltiplo de 2.
2. Pontos de market = idem.
3. Score total = soma dos dois (+10 se elegível a clima/inclusão).
4. Faixa (Excellent/Good/Satisfactory/Low).

### 5.1 Casos de teste (derivados da mecânica oficial)
Estes devem passar exatamente no motor correto:

| Project | Market | Pontos P | Pontos M | Total | Faixa |
|---|---|---|---|---|---|
| Strong-UQ | Strong-Q | 30 | 22 | **52** | Good ← exemplo da nota |
| Very Strong-UQ | Very Strong-UQ | 50 | 50 | 100 | Excellent |
| Marginal-Q | Marginal-Q | 4 | 4 | 8 | Low |
| Strong-UQ | Moderate-UQ | 30 | 12 | 42 | Satisfactory |
| Very Strong-Q | Strong-UQ | 38 | 30 | 68 | Good |
| Moderate-UQ | Moderate-Q | 12 | 8 | 20 | Low |

---

## 6. Ambiguidades da fonte (declaradas, não resolvidas por conta própria)
- **Fronteiras de faixa:** a Figura 2 da nota lista "Good 34–71" e "Satisfactory
  22–42" (com sobreposição), enquanto a Tabela 6 lista "Good 43–71" e
  "Satisfactory 22–42". Há inconsistência na própria fonte nas fronteiras
  34–42. **Decisão pendente do usuário:** adotar os limiares da Tabela 6
  (43/22), que é a tabela de conversão oficial. Sinalizado para confirmação.
- **Sector framework de fitoterápicos:** a mecânica de score (este documento) é
  universal e suficiente para o motor. Mas os **indicadores e benchmarks** que
  geram os ratings vêm dos sector frameworks — documentos separados que não
  constam desta nota. Isso é a Camada 2 (framework setorial), a ser construída
  depois, e é onde entram suas "20 categorias".

## 7. Recomendação de sequência
1. Validar esta especificação (lógica de negócio).
2. Construir o motor correto (`aimm_score_engine`) conforme Seção 5, com os
   casos de teste da Seção 5.1.
3. Só então estruturar a Camada 2 (framework setorial de fitoterápicos) e as
   demais camadas.

> Nada neste documento decide o rumo do sistema. Ele descreve o descompasso e
> especifica a correção. A decisão de adotar a norma oficial é do usuário.
