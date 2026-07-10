# AGENT OUTPUT CONTRACT — ARCHITECTURE & TECHNICAL ANALYSIS (AIMM)

## Princípio
A saída do agente deve ser auditável, rastreável e reexecutável. Cada afirmação
crítica remete a um arquivo do repositório. APIs externas têm estado verificado,
não presumido.

## Arquivos obrigatórios de saída

### 1) `docs/ARCHITECTURE_ANALYSIS_FACTUAL.md`
Estrutura obrigatória:
1. Cabeçalho de rastreabilidade (repositório, commit auditado, data).
2. Resumo executivo factual (máx. 12 bullets).
3. Eixo 1 — Arquitetura: camadas, portas, fluxo, grafo de dependência.
4. Eixo 2 — Objetivo do sistema: trecho verbatim + fonte.
5. Eixo 3 — APIs: tabela de APIs externas + tabela de endpoints internos.
6. Eixo 4 — Funcionalidades por módulo de negócio.
7. Eixo 5 — Condições técnicas e estruturais.
8. Riscos técnicos e pendências.

### 2) `docs/ARCHITECTURE_API_TABLE.csv`
- Delimitador `;` · Encoding `utf-8-sig`.
- Colunas, nesta ordem:
  `tipo;nome;origem_ou_rota;modulo_consumidor;arquivo;metodo_ou_formato;estado;observacao`
- `tipo` ∈ {`api_externa`, `endpoint_interno`}.
- `estado` ∈ {`ATIVA`, `INATIVA`, `NAO_VERIFICADA`, `REQUER_AUTENTICACAO`}.

### 3) `docs/ARCHITECTURE_EVIDENCE_TABLE.csv`
- Delimitador `;` · Encoding `utf-8-sig`.
- Colunas, nesta ordem:
  `eixo;item;status;arquivo;evidencia;observacao`
- `eixo` ∈ {`arquitetura`, `objetivo`, `apis`, `funcionalidades`,
  `condicoes_tecnicas`}.
- `status` ∈ {`IMPLEMENTADO`, `PARCIAL`, `DECLARADO_NAO_IMPLEMENTADO`,
  `EXTERNO`, `NAO_COMPROVADO`}.

---

## Regras de evidência obrigatória
- Toda afirmação crítica: arquivo, evidência descritiva e, quando aplicável,
  linha(s).
- Objetivo do sistema: trecho **idêntico** ao fonte (verbatim), com arquivo.
- API externa: estado verificado; se não houver rede, `NAO_VERIFICADA` com
  justificativa.
- Se não houver evidência: literal
  **"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.

## Critérios de aceite da saída
A saída é rejeitada se:
- faltar qualquer arquivo obrigatório;
- o objetivo não tiver trecho verbatim e fonte;
- alguma API externa não tiver estado classificado;
- algum endpoint interno não tiver método e indicação de autenticação;
- faltar o grafo de dependência entre módulos;
- faltar descrição de funcionalidade por módulo de negócio;
- faltar a seção de condições técnicas com stack, portas e variáveis de
  ambiente;
- o commit auditado não estiver registrado.

## Formato de linguagem
- Objetivo, técnico, sem adjetivação vaga.
- Siglas por extenso na primeira ocorrência (ex.: Organização da Sociedade Civil
  — OSC; Interface de Programação de Aplicações — API).
- Sem "melhores práticas" genéricas sem vínculo factual ao repositório.
