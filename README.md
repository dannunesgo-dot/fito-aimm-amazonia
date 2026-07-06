Fito+ Amazônia — Calculadora AIMM Adaptada
Este repositório é uma estrutura inicial para a Calculadora AIMM Adaptada aplicada a cadeias de valor de plantas medicinais, fitoterápicos e produtos herbais em saúde.

Estrutura mínima
data/reference/source_registry.csv: cadastro das fontes que podem alimentar indicadores.
data/evidence/evidence_registry.csv: evidências extraídas, conferidas e vinculadas a indicadores.
data/reference/dicionario_indicadores.csv: dicionário de indicadores da calculadora.
src/fito_aimm/: módulos Python para busca, extração, normalização e conferência.
.github/workflows/: automações do GitHub Actions.
outputs/: resultados gerados localmente ou pelo GitHub Actions.
Status
Versão inicial de arquitetura. Ainda requer implementação dos conectores reais de API, regras de conferência e sincronização autenticada com Google Drive.

Integração local — Gateway + Backend + World Bank API
Visão Geral
Este projeto integra a World Bank Indicators API por meio de um gateway Caddy local com autenticação via Bearer token.

Arquitetura
┌─────────────────┐
│ Seu App         │
│ (Frontend)      │
└────────┬────────┘
         │ HTTP Request
         ↓
┌─────────────────────────────┐
│ Gateway Caddy (8080)        │
│ - Valida Bearer token       │
│ - Reverse proxy             │
│ - Rate limiting (opcional)  │
└────────┬────────────────────┘
         │ Reencaminha
         ↓
┌─────────────────────────────┐
│ Backend API (8000)          │
│ - Flask app                 │
│ - Consulta World Bank       │
│ - Retorna dados             │
└────────┬────────────────────┘
         │ Requisição HTTP
         ↓
┌─────────────────────────────┐
│ World Bank API              │
│ https://api.worldbank.org   │
└─────────────────────────────┘
Setup rápido
Configure o ambiente local conforme o guia em README-local.md.
Suba os serviços:
.\run-local.ps1
Verifique status:
.\status-local.ps1
Execute testes de integração:
.\run-tests-local.ps1
Para parar:
.\stop-local.ps1