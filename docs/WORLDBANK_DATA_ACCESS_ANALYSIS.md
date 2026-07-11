# ANÁLISE DE ACESSO — World Bank Data (data.worldbank.org)

## Cabeçalho de rastreabilidade
- Fonte analisada: https://data.worldbank.org/ e Data Help Desk (Developer Information).
- Documentação oficial: https://datahelpdesk.worldbank.org/knowledgebase/articles/889386-developer-information-overview
- Data da análise: 2026-07-10.
- Método: leitura da documentação oficial de desenvolvedor + exemplos verbatim
  de endpoints. Limitação declarada na Seção 7.

## 1. Resumo executivo
O World Bank Data oferece **cinco APIs distintas**, todas públicas e sem
necessidade de chave de autenticação (API key) para uso básico. Para a
calculadora AIMM Fito+, três são diretamente relevantes: a **Indicators API**
(dados de séries temporais para benchmarks de gap e contexto), a **Projects
API** (operações do Banco Mundial, úteis como proxy de benchmark de projetos) e
a **Data Catalog API** (milhares de conjuntos de dados, para descoberta de
fontes). O acesso é gratuito, em formato JSON ou XML, e governado pelos Termos
de Uso para Dados do Banco Mundial.

## 2. As cinco APIs do World Bank (verbatim da documentação)
Conforme a página oficial "Developer Information: Overview":

1. **Indicators API** — "provides programmatic access to time series development
   data and metadata." É a principal; dá acesso a séries históricas por país e
   indicador.
2. **Data Catalog API** — "provides information about the thousands of
   development-relevant datasets available through the World Bank Data Catalog."
3. **Projects API** — "provides access to World Bank operations data, i.e.,
   active, pipeline and closed projects implemented in countries and around the
   world."
4. **Finances API** — "provides programmatic access to World Bank financial data
   (loans, credits, financial statements, etc)."
5. **Climate Data API** — "provides access to historical and modelled climate
   data from the Climate Knowledge Portal."

## 3. Indicators API — a mais relevante para benchmarks

### 3.1 Cobertura
A Indicators API dá acesso a **mais de 45 bases de dados** (incluindo World
Development Indicators, Worldwide Governance Indicators, International Debt
Statistics, Gender Statistics, entre outras) e **mais de 16.000 indicadores**.

### 3.2 Estrutura de chamada (base)
Toda chamada usa o prefixo `v2`. Exemplos oficiais verbatim:
- Lista de países: `https://api.worldbank.org/v2/country?format=json`
- Um indicador (metadados): `https://api.worldbank.org/v2/indicator/NY.GDP.MKTP.CD?format=json`
- Dado de país + indicador + ano:
  `https://api.worldbank.org/v2/country/br/indicator/NY.GDP.MKTP.CD?date=2006&format=json`
  (exemplo oficial: PIB do Brasil em 2006)
- Lista de fontes (as 45+ bases): `https://api.worldbank.org/v2/sources?format=json`

### 3.3 Parâmetros úteis para a calculadora (verbatim da documentação)
- `format=json` — resposta em JSON (padrão é XML).
- `date=2000:2001` — intervalo de anos (para séries históricas de benchmark).
- `mrv=5` — "most recent values": os 5 valores mais recentes (útil quando o ano
  varia por país).
- `mrnev=5` — "most recent non-empty values": os mais recentes não-vazios.
- `gapfill=Y` — preenche lacunas retrocedendo ao período disponível anterior.
- `per_page=500` — resultados por página (padrão 50).
- `source=2` — filtra por base de dados específica.
- Multi-indicador: separar códigos por `;` (máx. 60 indicadores por chamada).
- Multi-país: `country/chn;ago/` (vários países de uma vez).

### 3.4 Limites técnicos declarados
- Máximo de 60 indicadores por chamada.
- Máximo de 1.500 caracteres entre duas barras (`/`).
- Máximo de 4.000 caracteres na URL inteira.

## 4. Projects API — proxy de benchmark de projetos
A Projects API expõe operações do Banco Mundial (ativas, em pipeline e
encerradas), classificáveis por país, setor e tema. Para o AIMM Fito+, serve
como **fonte de benchmark de intensidade de projeto**: a metodologia AIMM permite
que o benchmark de intensidade se baseie em operações anteriores. Projetos do
Banco em saúde, agricultura e bioeconomia podem informar faixas de referência.
- Portal: https://projects.worldbank.org
- Endpoint base: http://search.worldbank.org/api/v2/projects

## 5. Data Catalog API — descoberta de fontes
Cataloga milhares de datasets. Útil na fase de construção do sector framework
Fito+ para **descobrir quais bases têm indicadores aplicáveis** a plantas
medicinais, fitoterápicos, saúde e meio ambiente, antes de fixar os indicadores.
- Portal: https://datacatalog.worldbank.org

## 6. Como isto se conecta à calculadora AIMM Fito+ (bases interconectadas)

A metodologia AIMM exige benchmarks para avaliar o **development gap** (contexto
do país) e a **project intensity**. O World Bank Data alimenta especificamente:

| Necessidade AIMM | Fonte World Bank | Exemplo de indicador |
|---|---|---|
| Contexto/gap do país | Indicators API (WDI) | PIB, PIB per capita, gasto em saúde |
| Benchmark relativo (normalização) | Indicators API | Indicadores por milhão de US$ ou por PIB |
| Estágio de mercado | Indicators API (governança) | Worldwide Governance Indicators |
| Benchmark de projetos | Projects API | Operações em saúde/agricultura |
| Descoberta de indicadores | Data Catalog API | Datasets de saúde/ambiente |

**Interconexão com as demais bases do sistema:** o World Bank fornece o
**contexto macro e comparativo internacional** (o "gap" relativo entre países,
que a AIMM exige). As bases brasileiras já no sistema (IBGE, MapaOSC) fornecem o
**contexto territorial e local**. As bases de comércio exterior que você mapeou
(Comtrade, Comexstat, Siscomex, Comex 360) fornecem a **dimensão de mercado e
competitividade**. A calculadora precisa cruzar as três camadas:
- World Bank → onde o Brasil está no espectro internacional (gap relativo).
- IBGE/MapaOSC → realidade territorial e organizacional local.
- Comércio exterior → dinâmica de mercado do produto Fito+ específico.

Um ponto de atenção metodológico: a AIMM faz o benchmark do gap **entre países
onde o IFC opera** (mercados emergentes). O World Bank Data permite exatamente
essa comparação internacional, pois cobre todos esses países com os mesmos
indicadores — é a fonte natural para posicionar o Brasil no espectro de gap.

## 7. Limitações e verificações declaradas
- **Verificação de rede:** a estrutura e os endpoints foram confirmados pela
  documentação oficial do Banco Mundial e por exemplos verbatim. A chamada real
  à API **não foi executada do ambiente de desenvolvimento de análise** (que tem
  acesso de rede restrito a uma lista branca que não inclui api.worldbank.org).
  No ambiente operacional da calculadora (com internet plena) as chamadas
  funcionam normalmente — a própria documentação permite testar colando qualquer
  endpoint de exemplo no navegador.
- **API v1 descontinuada:** a versão 1 foi descontinuada em 19 de junho de 2020.
  Usar sempre `v2` na chamada. Endpoints antigos retornam "Resource not found".
- **Termos de uso:** o uso dos dados é regido pelos Termos de Uso para Dados do
  Banco Mundial; o uso das APIs, pelos Termos e Condições. Verificar antes de
  redistribuir dados.
- **NÃO COMPROVADO NESTA ANÁLISE:** se existe indicador específico do World Bank
  dedicado a "plantas medicinais/fitoterápicos" — isto exige busca dirigida na
  Data Catalog API na fase de construção do framework (Camada 2).

## 8. Recomendação de integração (faseada)
1. **Agora (não):** não integrar ainda. O World Bank entra na Camada 3
   (pipeline), depois do sector framework (Camada 2) definir QUAIS indicadores
   são necessários.
2. **Na Camada 2:** usar a Data Catalog API e a Indicators API (lista de
   indicadores) para descobrir quais indicadores do World Bank servem de proxy
   para os gaps do framework Fito+.
3. **Na Camada 3:** implementar um coletor World Bank (padrão dos coletores IBGE
   existentes) que busca os indicadores selecionados, com os parâmetros `mrv`,
   `gapfill` e `date` conforme a necessidade de série histórica.

> Esta análise descreve os acessos disponíveis. A seleção de quais indicadores
> usar é decisão de conteúdo do framework Fito+ (sua expertise), não desta
> análise técnica.
