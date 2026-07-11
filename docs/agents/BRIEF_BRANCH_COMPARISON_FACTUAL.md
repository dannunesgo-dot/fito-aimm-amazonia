# BRIEF — AGENTE DE COMPARAÇÃO ENTRE BRANCHES (SEM INFERÊNCIA)

## Missão
Comparar, de forma factual e auditável, um branch qualquer do repositório com o
`main`, para responder: **o que este branch muda em relação ao sistema real?**

Para um branch-alvo, o agente produz:
1. Módulos e arquivos **adicionados**, **removidos** e **modificados** (conteúdo
   útil separado de ruído).
2. Impacto no **núcleo** vs periferia: destaca modificações em módulos da cadeia
   de processamento AIMM (`aimm_engine`, `aimm_dashboard`, `aimm_communication`)
   e em `app.py`.
3. Mudanças no **grafo de dependência** entre módulos (novas dependências,
   dependências removidas).
4. Mudanças em **endpoints Flask** e **APIs externas**.
5. **Ruído de versionamento** (`__pycache__`, `.pyc`, arquivos de erro de shell)
   isolado e quantificado — para que o volume de "arquivos diferentes" não seja
   confundido com volume de trabalho útil.

O agente **não** decide se o branch deve ser mesclado, não avalia qualidade nem
correção do código, não recalcula score AIMM. Ele descreve **o que muda**, com
rastreabilidade, para que a decisão de aproveitamento seja informada.

## Princípios obrigatórios
- Sem inferência: toda afirmação cita branch, arquivo e tipo de mudança (A/M/D).
- `main` é a verdade de referência; o branch é a proposta de mudança.
- Cada branch é comparado **isoladamente** com o `main`; o agente NUNCA funde
  conteúdo de branches diferentes.
- Ruído é classificado e separado, nunca contado como conteúdo.
- Classificar cada arquivo por status: `ADICIONADO`, `REMOVIDO`, `MODIFICADO`,
  `RUIDO`.
- Lacuna sem evidência: literal **"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.

## Definição de ruído (isolado, não contado como conteúdo)
Um arquivo é `RUIDO` se seu caminho contém `__pycache__`, termina em `.pyc`,
começa com `=` (erro de redirecionamento de `pip install`), ou é log/binário
temporário não versionável pela política do repositório
(`config/system_freeze_rules.yaml`).

## Definição de "impacto no núcleo"
Modificação (`M`) em qualquer um destes é destacada como impacto no núcleo:
- `src/fito_aimm/aimm_engine.py` (produtor primário da cadeia)
- `src/fito_aimm/aimm_dashboard.py`
- `src/fito_aimm/aimm_communication.py`
- `app.py` (backend/endpoints)
Demais modificações são periféricas.

## Entradas
- Nome do branch-alvo (parâmetro; um por execução).
- Repositório com o branch remoto disponível (`git fetch`).

## Escopo factual
Para o branch-alvo, extrair:
1. Diff `main...<branch>` classificado (A/M/D), com ruído isolado.
2. Módulos Python novos em `src/` (não-ruído), com suas classes/funções
   públicas (reconhecendo `class`, `def execute_*`, `def executar_*`,
   `def coletar_*`).
3. Módulos do `main` modificados pelo branch, com magnitude (linhas +/-).
4. Impacto no núcleo (lista de módulos-núcleo modificados).
5. Novos endpoints/APIs se `app.py` ou coletores forem tocados.
6. Contagem de ruído vs conteúdo útil.

## Entregáveis obrigatórios
### A) `docs/BRANCH_COMPARISON_<branch>.md` (um por branch comparado)
Seções mínimas:
1. Cabeçalho de rastreabilidade (branch, commit, ahead/behind, data).
2. Resumo factual (conteúdo útil vs ruído; impacto no núcleo sim/não).
3. Arquivos adicionados (não-ruído).
4. Arquivos modificados, com destaque para o núcleo.
5. Módulos Python novos e suas classes/funções.
6. Ruído isolado (contagem + amostra).
7. Observações de conflito potencial (se aplicável).

### B) `docs/BRANCH_COMPARISON_TABLE.csv` (consolida todas as comparações feitas)
Colunas (delimitador `;`, encoding `utf-8-sig`):
`branch;arquivo;tipo;categoria;impacto_nucleo;observacao`
- `tipo` ∈ {`ADICIONADO`, `REMOVIDO`, `MODIFICADO`, `RUIDO`}.
- `categoria` ∈ {`modulo_python`, `documento`, `config`, `workflow`, `dado`,
  `outro`}.
- `impacto_nucleo` ∈ {`sim`, `nao`}.

## Critérios de aceite (hard gate)
Não concluir uma comparação se faltar:
- classificação A/M/D de cada arquivo do diff;
- ruído isolado e quantificado;
- resposta explícita "impacto no núcleo? (sim/não)";
- lista de módulos Python novos com suas classes/funções;
- ahead/behind do branch registrado.

## Regra final
Se não houver evidência suficiente, registrar literalmente:
**"NÃO COMPROVADO NO REPOSITÓRIO ANALISADO"**.
