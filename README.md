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
## Checklist de pré-execução

Antes de iniciar o ambiente local, verifique cada item:

- [ ] **Ambiente virtual criado e ativado**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- [ ] **Arquivo `.env` criado a partir do `.env.example`**
  ```powershell
  copy .env.example .env
  # Edite .env com seus valores (AUTH_TOKEN, etc.)
  ```

- [ ] **Portas necessárias livres**
  | Porta | Serviço |
  |-------|---------|
  | 8000  | Backend Flask |
  | 8080  | Gateway Caddy |

  Para verificar/liberar:
  ```powershell
  .\stop-local.ps1
  ```

- [ ] **Caddy disponível no PATH**
  ```powershell
  caddy version
  ```

- [ ] **Validação pós-subida (health endpoint)**
  ```powershell
  # Após .\run-local.ps1, verificar:
  Invoke-WebRequest http://127.0.0.1:8080/health
  # Esperado: HTTP 200 OK
  ```

## Setup rápido

> **Comando oficial de execução local: `.\run-local.ps1`**
> Os demais métodos (`python app.py`, `Iniciar-API.cmd`) são fallback e podem não iniciar todos os serviços.

Configure o ambiente local conforme o guia em README-local.md.
Suba os serviços:
```powershell
.\run-local.ps1
```
Verifique status:
```powershell
.\status-local.ps1
```
Execute testes de integração:
```powershell
.\run-tests-local.ps1
```
Para parar:
```powershell
.\stop-local.ps1
```

### Fallbacks (somente se `run-local.ps1` não estiver disponível)

| Método | Comando | Limitação |
|--------|---------|-----------|
| Flask direto | `python app.py` | Não sobe Caddy/gateway |
| CMD atalho | `Iniciar-API.cmd` | Depende de `activate-api.ps1`; não garante gateway |