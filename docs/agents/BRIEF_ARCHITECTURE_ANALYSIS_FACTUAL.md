# BRIEF — AGENTE DE ANÁLISE DE ARQUITETURA E CONDIÇÕES TÉCNICAS (SEM INFERÊNCIA)

## Missão
Produzir um retrato factual e auditável da arquitetura do sistema AIMM (Análise
de Investimento e Maturidade de Mercado) aplicado a plantas medicinais,
fitoterápicos e produtos herbais, cobrindo cinco eixos:

1. **Arquitetura** — camadas, componentes, fluxo de dados, pontos de entrada e
   saída, dependências entre módulos.
2. **Objetivo do sistema** — finalidade declarada, extraída de documentação e
   código (não inferida).
3. **APIs válidas** — quais APIs externas o sistema consome, com verificação de
   validade/estado, e quais endpoints internos (Flask) expõe.
4. **Funcionalidades** — o que o sistema efetivamente faz hoje, por módulo, com
   distinção entre implementado e declarado-mas-não-implementado.
5. **Condições técnicas e estruturais** — stack, dependências, requisitos de
   execução, governança de dados, restrições e riscos.

O agente **não** avalia mérito de negócio, não recalcula score AIMM, não aprova
Organizações da Sociedade Civil (OSCs), espécies, produtos, orçamento ou rotas
regulatórias. Ele descreve e verifica **estrutura, capacidades e condições
técnicas**, com rastreabilidade por arquivo.

## Princípios obrigatórios
- Sem inferência: toda afirmação crítica cita arquivo e, quando aplicável,
  linha(s).
- Objetivo e funcionalidades vêm de documentação/código existente, nunca de
  suposição sobre a intenção do sistema.
- APIs externas são verificadas quanto a estado (URL responde? formato
  esperado?), não apenas listadas.
- Classificar cada achado por status controlado: `IMPLEMENTADO`, `PARCIAL`,
  `DECLARADO_NAO_IMPLEMENTADO`, `EXTERNO`, `NAO_COMPROVADO`.
- Lacuna sem evidência é declarada com o literal
  **"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.

## Repositório e escopo de análise
- Base: `main` do repositório
  `https://github.com/dannunesgo-dot/fito-aimm-amazonia`.
- Fontes primárias obrigatórias de leitura:
  - `app.py`, `Caddyfile`, `Caddyfile.local`, `requirements.txt`
  - `run-local.ps1`, `status-local.ps1`, `stop-local.ps1`, `*.cmd`
  - `src/fito_aimm/*.py`
  - `config/*.yaml`
  - `.github/workflows/*.yml`
  - `docs/*.md` e `docs/contracts/*`
  - `data/reference/*` (catálogos de query, registro de fontes)
  - `.env.example`

## Escopo factual por eixo

### Eixo 1 — Arquitetura
Mapear, com evidência de arquivo:
- Camadas (ex.: gateway Caddy → backend Flask → módulos → dados).
- Portas e protocolos (ex.: 8080 gateway, 8000 backend).
- Fluxo requisição→resposta.
- Grafo de dependência entre módulos (quem produz, quem consome saídas
  `data/processed/*`).
- Pontos de entrada (funções públicas de execução) e saída (constantes `OUT_*`,
  artefatos publicados por workflow).

### Eixo 2 — Objetivo do sistema
- Extrair a finalidade declarada de `README.md`, `README_operacional.md`,
  cabeçalhos de módulos e `config/projeto_fito_amazonia.yaml`.
- Registrar verbatim (trecho idêntico ao fonte) e citar o arquivo.
- Se houver divergência entre fontes, sinalizar.

### Eixo 3 — APIs válidas
**APIs externas consumidas** (verificar cada uma):
- World Bank (`https://api.worldbank.org/v2`)
- IBGE SIDRA (`https://apisidra.ibge.gov.br/values`)
- IBGE Localidades (`https://servicodados.ibge.gov.br/api/v1/localidades`)
- IBGE geoftp (arquivo territorial `.xls`)
- MapaOSC/IPEA (base de divulgação `.csv` e dicionário `.xlsx`)
Para cada: registrar módulo consumidor (arquivo/linha), formato esperado,
tratamento de erro/timeout, e estado atual da URL (responde? esquema esperado?).

**Endpoints internos expostos** (Flask, `app.py`):
- Listar cada rota, método, autenticação exigida, e o que retorna.

### Eixo 4 — Funcionalidades
Por módulo de negócio, descrever a capacidade real:
- O que a função pública de execução faz (entrada → processamento → saída).
- Distinguir capacidade **implementada** de comentário/TODO/placeholder.
- Cruzar com o inventário do agente `module_pipeline_audit` quando disponível.

### Eixo 5 — Condições técnicas e estruturais
- Stack e versões (`requirements.txt`, versão Python nos workflows).
- Requisitos de execução (portas, variáveis de ambiente de `.env.example`,
  dependências de sistema como Caddy).
- Governança de dados (política GitHub × Google Drive de
  `config/system_freeze_rules.yaml`; registro de fontes em
  `data/reference/source_registry.csv`).
- Restrições e riscos técnicos (dependência de artefato manual, dados sensíveis,
  cadeia de dependência de pipeline).

## Entregáveis obrigatórios
### A) `docs/ARCHITECTURE_ANALYSIS_FACTUAL.md`
Seções mínimas:
1. Cabeçalho de rastreabilidade (repositório, commit, data).
2. Resumo executivo factual (máx. 12 bullets).
3. Eixo 1 — Arquitetura (diagrama textual de camadas + grafo de dependência).
4. Eixo 2 — Objetivo do sistema (verbatim + fonte).
5. Eixo 3 — APIs (tabela externa + tabela de endpoints internos).
6. Eixo 4 — Funcionalidades por módulo.
7. Eixo 5 — Condições técnicas e estruturais.
8. Riscos técnicos e pendências.

### B) `docs/ARCHITECTURE_API_TABLE.csv`
Colunas obrigatórias (delimitador `;`, encoding `utf-8-sig`):
`tipo;nome;origem_ou_rota;modulo_consumidor;arquivo;metodo_ou_formato;estado;observacao`
- `tipo` ∈ {`api_externa`, `endpoint_interno`}.
- `estado` ∈ {`ATIVA`, `INATIVA`, `NAO_VERIFICADA`, `REQUER_AUTENTICACAO`}.

### C) `docs/ARCHITECTURE_EVIDENCE_TABLE.csv`
Colunas obrigatórias:
`eixo;item;status;arquivo;evidencia;observacao`
- `eixo` ∈ {`arquitetura`, `objetivo`, `apis`, `funcionalidades`, `condicoes_tecnicas`}.

## Critérios de aceite (hard gate)
Não concluir se faltar:
- objetivo do sistema com trecho verbatim e fonte citada;
- tabela de APIs externas com estado verificado por API;
- tabela de endpoints internos com método e autenticação;
- grafo de dependência entre módulos;
- descrição de funcionalidade por módulo de negócio;
- seção de condições técnicas com stack, portas e variáveis de ambiente.

## Regra final
Se não houver evidência suficiente para afirmar algo, registrar literalmente:
**"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.
