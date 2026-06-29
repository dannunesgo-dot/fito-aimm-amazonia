# Fito+ Amazônia — Calculadora AIMM Adaptada

Este repositório é uma estrutura inicial para a Calculadora AIMM Adaptada aplicada a cadeias de valor de plantas medicinais, fitoterápicos e produtos herbais em saúde.

## Estrutura mínima

- `data/reference/source_registry.csv`: cadastro das fontes que podem alimentar indicadores.
- `data/evidence/evidence_registry.csv`: evidências extraídas, conferidas e vinculadas a indicadores.
- `data/reference/dicionario_indicadores.csv`: dicionário de indicadores da calculadora.
- `src/fito_aimm/`: módulos Python para busca, extração, normalização e conferência.
- `.github/workflows/`: automações do GitHub Actions.
- `outputs/`: resultados gerados localmente ou pelo GitHub Actions.

## Status

Versão inicial de arquitetura. Ainda requer implementação dos conectores reais de API, regras de conferência e sincronização autenticada com Google Drive.
