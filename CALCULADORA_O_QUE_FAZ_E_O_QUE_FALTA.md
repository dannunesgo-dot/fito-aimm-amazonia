# 🔍 O QUE A CALCULADORA AIMM JÁ FAZ vs. O QUE FALTA

**Data:** 2026-07-03  
**Público:** Usuários com conhecimento intermediário (não programadores)

---

## 📌 RESUMO EXECUTIVO - Em Uma Frase

> 🟢 **VERDE:** A calculadora consegue **coletar dados públicos, filtrar organizações, registrar benchmarks e calcular scores preliminares**  
> 🟡 **AMARELO:** Mas **não seleciona automaticamente quem executa**, **não calcula análise geográfica (mapas)** e **não gera resultado final validado**

---

## 🏗️ ARQUITETURA ATUAL - O Que Existe

### 📊 Fluxo Operacional

```
┌──────────────────────────────────────────────────────────────┐
│ ENTRADA: Municípios, Critérios, Bases Públicas              │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
     ┌───────────────────────────┐
     │ 1️⃣  COLETA DE DADOS       │ ✅ FUNCIONA
     │ (IBGE, Mapa OSC, etc)     │
     └───────────┬───────────────┘
                 │
                 ▼
     ┌───────────────────────────┐
     │ 2️⃣  TRIAGEM & FILTRAGEM   │ ✅ FUNCIONA
     │ (Riscos de OSC)           │
     └───────────┬───────────────┘
                 │
                 ▼
     ┌───────────────────────────┐
     │ 3️⃣  BENCHMARKS & SCORES   │ ⏳ PARCIAL
     │ (Comparação com padrões)  │
     └───────────┬───────────────┘
                 │
                 ▼
     ┌───────────────────────────┐
     │ 4️⃣  CÁLCULO DE INDICADORES│ ✅ FUNCIONA
     │ (5 dimensões AIMM)        │
     └───────────┬───────────────┘
                 │
                 ▼
     ┌───────────────────────────┐
     │ 5️⃣  RESULTADO FINAL       │ ❌ NÃO PRONTO
     │ (Validado para decisão)   │
     └───────────────────────────┘
```

---

## ✅ O QUE JÁ FUNCIONA (VERDE)

### 1️⃣ **COLETA AUTOMÁTICA DE DADOS PÚBLICOS**

**O que é?**  
A calculadora consegue conectar em bases de dados públicas e baixar informações automaticamente.

**Analogia:**  
Como um assistente que vai à biblioteca pública, pega o catálogo oficial, copia dados e traz de volta.

**Quais bases?**
- ✅ **IBGE/SIDRA** — População, economia, estatísticas oficiais
- ✅ **Mapa OSC** — Organizações da sociedade civil cadastradas
- ✅ **CNPJ Público** — Dados de registro de empresas

**Efeito no Processamento:**  
Economiza horas de digitação manual. Se há erro na fonte, a calculadora herda o erro também.

**Exemplo Real:**
```
Antes (Manual):
- Você digita: "Manaus 2024 população" no Google
- Copia número do artigo
- Cola em planilha Excel
- Tempo: 2 horas para 4 cidades

Agora (Automático):
- Sistema conecta IBGE API
- Baixa população de 4 cidades
- Registra em log (rastreável)
- Tempo: 30 segundos
```

**Fragilidade Específica:**
- ❌ Se a API da base pública cair → pausa a coleta
- ❌ Se o formato da base mudar → precisa atualizar código
- ❌ Só funciona com bases que têm API pública

---

### 2️⃣ **CLASSIFICAÇÃO E FILTRO DE RISCO (OSCs)**

**O que é?**  
A calculadora analisa organizações cadastradas e identifica quais têm sinais de risco.

**Analogia:**  
Como um sistema de pontuação de crédito. Cada característica (idade, documentos, histórico) vale pontos.

**O que analisa?**
- 🔍 Situação cadastral (ativa, inativa, suspensa?)
- 🔍 Regularidade documental (CNPJ, estatuto, atas)
- 🔍 Histórico de conflitos (processos, advertências)
- 🔍 Transparência (se publicam contas)

**Exemplo de Resultado:**
```
Organização: "Cooperativa Verde Amazônia"
├─ Cadastro: ✅ Ativo (40 pontos)
├─ CNPJ: ⚠️ Vencido (0 pontos)
├─ Histórico: ❌ 2 processos abertos (-20 pontos)
├─ Transparência: ✅ Publica relatórios (20 pontos)
└─ SCORE RISCO: 40 de 100 = 🔴 ALTO RISCO

Recomendação: Exigir mais documentação antes de trabalhar
```

**Efeito no Processamento:**  
Reduz chance de trabalhar com organizações problemáticas. Mas é baseado só em dados públicos (pode haver segredos).

**Fragilidade:**
- ❌ Dados públicos podem estar desatualizados
- ❌ Situação boa no papel não garante qualidade na prática
- ❌ Não identifica má conduta recente (leva tempo para registrar)

---

### 3️⃣ **REGISTRO DE BENCHMARKS (Comparação com Padrões)**

**O que é?**  
A calculadora define "benchmarks" = padrões de referência (quanto deveria gastar, qual população mínima, etc).

**Analogia:**  
Como definir "para cultivar açaí, a média de produtividade global é 5 ton/hectare". Depois você compara: seu produtor faz 3 ton? Está abaixo.

**Quais benchmarks existem?**
- 📊 **Benchmarks públicos:** BNDES, Sebrae, literatura técnica
- 📊 **Proxies:** Se benchmark não existe, usa algo similar (exemplo: custo coco = 70% custo açaí)
- 📊 **Lacunas:** Registra onde faltam comparações

**Exemplo:**
```
Espécie: Açaí
├─ Benchmark Global: 3 ton/hectare
├─ Benchmark Brasil: 2.5 ton/hectare
├─ Proxy Regional: Dados do IBGE adaptados
├─ Lacuna: Dados de produtividade por manejo agroecológico = ❌ NÃO EXISTE
└─ Fonte Usada: ITC/BNDES (2023)
```

**Efeito no Processamento:**  
Permite comparar: "Este projeto está dentro de limites realistas?" ou "Esta OSC gasta muito comparado a outras?"

**Fragilidade:**
- ❌ Proxies são estimativas, não medidas reais
- ❌ Benchmarks internacionais podem não valer para Amazônia
- ❌ Confunde "estar abaixo do benchmark" com "está ruim"

---

### 4️⃣ **CÁLCULO DE INDICADORES PRELIMINARES (5 Dimensões AIMM)**

**O que é?**  
A calculadora pega dados coletados e calcula um "score" (0-100) em cada uma de 5 áreas.

**As 5 Dimensões:**

| Dimensão | O Que Mede | Analogia |
|----------|-----------|----------|
| 🟢 **GAP** | Diferença entre onde está e onde deveria estar | Distância que precisa caminhar |
| 📈 **INTENSIDADE** | Força do investimento, escala do impacto | Tamanho do empurrão que vai dar |
| 💰 **MERCADO** | Viabilidade comercial, demanda, preço | Se o produto vai vender e por quanto |
| 🛑 **RISCO** | Problemas que podem impedir sucesso | Obstáculos na estrada |
| 👁️ **MONITORAMENTO** | Capacidade de acompanhar e medir | Se consegue verificar se funcionou |

**Exemplo Prático - Projeto Açaí:**

```
Dimensão GAP (Lacuna)
├─ Produtor cultiva em 5 hectares = 10 ton/ano
├─ Potencial regional = 50 hectares com 100 ton/ano possível
├─ Gap = 40 hectares não cultivados = GRANDE
└─ Score GAP: 25 (muito a crescer) ▶️ 📊

Dimensão INTENSIDADE (Força)
├─ Investimento: R$ 50 mil em máquinas
├─ Volume esperado: +60 ton/ano
├─ Impacto: 600% do investimento em produção
└─ Score INTENSIDADE: 85 (muito impacto) ▶️ 📊

Dimensão MERCADO (Viabilidade)
├─ Preço açaí: R$ 8-12 por kg
├─ Demanda regional: 200 ton/ano
├─ Oferta atual: 50 ton/ano
├─ Demanda > Oferta? SIM
└─ Score MERCADO: 80 (mercado existe) ▶️ 📊

Dimensão RISCO (Obstáculos)
├─ Capacidade técnica do produtor: Boa (10 anos)
├─ Acesso a crédito: Difícil (não tem garantias)
├─ Clima: Favorável para açaí
├─ Risco Geral: MODERADO
└─ Score RISCO: 60 (problema creditício) ▶️ 📊

Dimensão MONITORAMENTO (Acompanhamento)
├─ Dados de produção: Controla em caderneta
├─ Acesso a preços de mercado: Via WhatsApp
├─ Capacidade de relatório: Básica
├─ Score MONITORAMENTO: 40 (precisa de sistema) ▶️ 📊

RESULTADO FINAL: (25+85+80+60+40) ÷ 5 = 58/100
Status: MÉDIO - Projeto viável mas precisa reforço em crédito e monitoramento
```

**Efeito no Processamento:**  
- ✅ Mostra visão 360° do projeto (não vê só um lado)
- ✅ Identifica pontos fracos rapidinho
- ⚠️ Score é preliminar (não é recomendação final)

**Fragilidade:**
- ❌ Usa dados que podem estar defasados
- ❌ Calcula score "estrutural" mas não "qualidade real"
- ❌ Não diferencia entre "não sabe" e "é ruim"

---

## 🔴 O QUE AINDA NÃO FUNCIONA (FALTA FAZER)

### ❌ 1. **SELEÇÃO AUTOMÁTICA DE EXECUTOR**

**O que seria?**  
Após calcular tudo, a máquina recomendaria: "Esta OSC é a melhor para executar este projeto."

**Analogia:**  
Como um aplicativo de namoro que diz: "Você e João são 87% compatíveis!"

**Por que não existe?**
- ⚠️ Decisão humana é necessária (responsabilidade legal)
- ⚠️ Critérios mudam por circunstância política/social
- ⚠️ Não há quantidade suficiente de dados confiáveis

**Quando vai existir?**  
**FASE 3** (próximas 2-3 semanas) — Sistema vai sugerir, mas usuário decide.

**Efeito quando ficar pronto:**  
Reduz tempo de decisão de 1 semana para 1 dia. Mas risco: pode descartar executor bom por questão técnica.

---

### ❌ 2. **ANÁLISE GEOGRÁFICA (MAPAS)**

**O que seria?**  
A calculadora mostraria no mapa: "Aqui há potencial açaí", "Ali há OSC com risco", "Neste ponto há falta de acesso"

**Analogia:**  
Como Google Maps, mas para decisões de investimento. Você vê geograficamente onde estão os problemas e oportunidades.

**Por que não existe?**
- ⚠️ Requer dados geoespaciais (longitude/latitude) muito precisos
- ⚠️ Precisa de software GIS especializado (QGIS, ArcGIS)
- ⚠️ Banco de dados geográfico ainda não consolidado para toda região

**Dados que faltam:**
- 🟡 Mapa de desflorestamento (tem, mas desatualizado)
- 🟡 Zonas de potencial produtivo (parcial)
- 🔴 Rasters de cobertura vegetal em tempo real (não tem acesso público confiável)
- 🔴 Limites precisos de terras indígenas (sensível politicamente)

**Quando vai existir?**  
**FASE 3-4** (1-2 meses) — Começar com Manaus + 1 município, depois expandir.

**Efeito quando ficar pronto:**  
Aumenta confiança em decisão: "Não vou investir açaí aqui porque o desmate está acelerando"

---

### ❌ 3. **RESULTADO FINAL VALIDADO**

**O que seria?**  
Um documento oficial que diz: "Após análise completa, recomendamos Investimento X com Executor Y."

**Analogia:**  
Como um laudo de engenheiro ou parecer de advogado — documento que pode ser usado oficialmente.

**Por que não existe agora?**
- ⚠️ Score atual é "preliminar" porque:
  - Usa benchmarks parciais (proxies, não dados reais)
  - Não tem validação humana independente
  - Não tem assinatura de responsável técnico
  - Ainda há lacunas em 3 dos 5 indicadores

**O que falta?**
```
Score Preliminar (agora existe)
        ⬇️
Revisão de Especialista (não existe)
        ⬇️
Validação de Risco (parcial)
        ⬇️
Assinatura Responsável (não existe)
        ⬇️
Score FINAL Validado (meta)
```

**Exemplo do que está pendente:**
```
Indicador MONITORAMENTO:
├─ Score calculado automaticamente: 40
├─ Revisão humana: ⏳ PENDENTE
│  └─ Pergunta: "Mas este projeto TEM capacidade de medir?"
│  └─ Resposta automática: "Dados indicam não"
│  └─ Validação: "Concordo, vai precisar de sistema"
├─ Assinatura: ⏳ PENDENTE (quem vai assinar?)
└─ Resultado: Score FINAL ainda não existe
```

**Quando vai existir?**  
**FASE 4** (2-3 semanas após FASE 3) — Workflow com aprovador responsável.

**Efeito quando ficar pronto:**  
Resultado pode ser usado em documentos oficiais, licitações, relatórios públicos.

---

### ❌ 4. **SELEÇÃO AUTOMÁTICA DE ESPÉCIES/PRODUTOS**

**O que seria?**  
Sistema automaticamente recomenda: "Para esta região, estes são os 3 melhores produtos para cultivar"

**Analogia:**  
Como Netflix recomenda filmes com base no que você viu antes.

**Dados que são necessários:**
- 🟡 Matriz clima-espécie (parcial)
- 🟡 Dados de mercado por produto (incompleto)
- 🔴 Rentabilidade real por região (não existe centralizado)
- 🔴 Requisitos regulatórios por UF (disperso)

**Quando vai existir?**  
**FASE 5** (próximo mês) — Depende de coleta de dados de produtores reais.

---

### ❌ 5. **INTEGRAÇÃO COM GOOGLE DRIVE (Automática)**

**O que seria?**  
Dados salvam automaticamente em uma pasta compartilhada do Google Drive. Todos veem em tempo real.

**Analogia:**  
Como um documento Google Docs que múltiplas pessoas editam, mas para decisões de investimento.

**Por que não existe?**
- ⚠️ Requer configuração de autenticação segura
- ⚠️ Não há padrão de pasta definido
- ⚠️ Questões de acesso/permissões não resolvidas

**Quando vai existir?**  
**FASE 2-3** (próxima semana) — Será implementado com segurança.

---

## 📊 TABELA RESUMIDA: O QUE EXISTE vs. O QUE FALTA

| Funcionalidade | Status | Quando | Impacto |
|---|---|---|---|
| 🔵 Coleta IBGE/Mapa OSC | ✅ **PRONTO** | Uso imediato | Alto |
| 🔵 Classificação risco OSC | ✅ **PRONTO** | Uso imediato | Alto |
| 🔵 Registro benchmarks | ✅ **PRONTO** | Uso imediato | Médio |
| 🔵 Cálculo 5 dimensões | ✅ **PRONTO** | Uso imediato | Alto |
| 🟡 Seleção executor | ⏳ **2 sem** | FASE 3 | Alto |
| 🟡 Análise geográfica (mapas) | ⏳ **3 sem** | FASE 4 | Muito Alto |
| 🟡 Resultado final validado | ⏳ **4 sem** | FASE 4 | Crítico |
| 🟡 Seleção espécie/produto | ⏳ **4+ sem** | FASE 5 | Médio |
| 🟡 Google Drive automático | ⏳ **1 sem** | FASE 2 | Baixo-Médio |

---

## 🎯 O QUE FAZER AGORA (PRÓXIMAS SEMANAS)

### Semana 1 (2026-07-04 a 07): TESTES & INTEGRAÇÃO
```
✓ Validar que coleta + cálculo funcionam em conjunto
✓ Testar com dados reais de 2-3 projetos
✓ Identificar erros nos scores
✓ Documentar limitações para usuários
```

### Semana 2-3 (2026-07-10 a 21): SELEÇÃO AUTOMÁTICA
```
✓ Implementar recomendação de executor (sugestão, não obrigação)
✓ Criar interface para usuário validar/rejeitar sugestão
✓ Registrar motivo da rejeição (aprendizado)
✓ Testar com 5-10 projetos reais
```

### Semana 3-4 (2026-07-17 a 31): MAPAS & GEOLOCALIZAÇÃO
```
✓ Conectar com bases GIS abertas (INPE, IBGE)
✓ Criar mapa de potencial por município
✓ Visualizar OSCs no mapa
✓ Testar em QGIS (software de mapas)
```

### Semana 4+ (2026-07-31+): VALIDAÇÃO FINAL
```
✓ Criar workflow de assinatura digital
✓ Designar responsáveis técnicos
✓ Gerar relatório final com evidências
✓ Publicar resultado (ou manter confidencial conforme política)
```

---

## ⚡ FRAGILIDADES ESPECÍFICAS A CONHECER

### 1. **Dados Defasados**
```
Risco: Sistema usa dados de 6 meses atrás
Efeito: Pode recomendar executor que depois perdeu certificação
Mitigação: Validação manual antes de decisão final
```

### 2. **Proxies Estimadas**
```
Risco: Usa "custo coco ≈ 70% custo açaí" (não é verdade absoluta)
Efeito: Pode calcular score incorreto
Mitigação: Marcar claramente quais são proxies vs. dados reais
```

### 3. **Viés de Seleção**
```
Risco: Se OSC com bom risco for rara, sistema sempre recomenda a mesma
Efeito: Concentra investimentos em poucos executores
Mitigação: Cotas mínimas ou critérios sociais adicionados manualmente
```

### 4. **Falta de Contexto Político**
```
Risco: Sistema não sabe de mudanças governamentais ou pressões políticas
Efeito: Recomenda algo que, na realidade, é politicamente impossível
Mitigação: Revisor humano deve validar "fazibilidade política"
```

---

## 🔄 FLUXO RECOMENDADO DE USO (HOJE)

```
1. Você define:
   ├─ Municípios de interesse
   ├─ Espécies/produtos prioritários
   ├─ Orçamento disponível
   └─ Prazos

2. Sistema faz:
   ├─ Coleta dados públicos
   ├─ Filtra OSCs por risco
   ├─ Calcula scores 5 dimensões
   └─ Gera relatório com evidências

3. Você revisa:
   ├─ Resultado faz sentido?
   ├─ Há dados que você desconfia?
   ├─ Fatores políticos/sociais que sistema não vê?
   └─ Recomenda ajustes

4. Resultado Final:
   ├─ Você aprova/rejeita
   ├─ Sistema registra feedback
   └─ Próxima rodada usa aprendizado
```

---

## 📞 PERGUNTAS FREQUENTES

### P: "Por que o sistema recomenda esta OSC se tem risco alto?"
**R:** Porque tem gap grande (muita oportunidade) mas capacidade limitada. Sistema diz "risco, mas é oportunidade". Você decide se vale a pena investir em capacitação dela.

### P: "E se dados do IBGE estiverem errados?"
**R:** Sistema herda o erro. Isso é normal em qualquer análise. Por isso precisa de validação humana.

### P: "Quando posso usar isto para decisão oficial?"
**R:** Quando houver assinatura de responsável técnico (Fase 4, ~3-4 semanas).

### P: "Posso exportar para Excel?"
**R:** Sim. Sistema gera CSVs que abrem em qualquer programa.

---

## 🎯 CONCLUSÃO

**RESUMO EM 3 FRASES:**
1. ✅ **Agora:** Você consegue coletar dados, filtrar riscos e ver scores prelim inares rapidinho
2. ⏳ **Em 2-3 semanas:** Sistema vai sugerir quem executa (você valida)
3. 🎯 **Em 1 mês:** Sistema pronto para decisões oficiais

**Próximo Passo:** Testar com 2-3 projetos reais e dar feedback.

---

**Dúvidas?** Este documento será atualizado conforme o sistema evolui.
