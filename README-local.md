# Ambiente local (Flask + Caddy)

Subida rápida da API local com proxy/autorização para integração com World Bank API.

## Pré-requisitos

- Windows + PowerShell
- Python (com `.venv` no projeto)
- Dependências instaladas (`pip install -r requirements.txt`)
- Caddy instalado e disponível no PATH

## Arquivos e scripts locais

- `.\run-local.ps1` → sobe Flask + Caddy e faz smoke tests
- `.\status-local.ps1` → mostra processos, portas e checks HTTP (com token mascarado)
- `.\stop-local.ps1` → para Caddy/Python
- `.\run-tests-local.ps1` → carrega `.env` sem expor token e executa testes
- `.\scripts\test_api_integration.ps1` → testes HTTP de integração Gateway/Backend

## Configuração do `.env` (raiz do projeto)

> **Local exato para inserir token:** arquivo **`.env`** na raiz, linha `AUTH_TOKEN=...`

Crie/edite `.env`:

```dotenv
WORLDBANK_API_URL=https://api.worldbank.org/v2
WORLDBANK_API_KEY=
GATEWAY_URL=http://127.0.0.1:8080
BACKEND_URL=http://127.0.0.1:8000
AUTH_TOKEN=oRmrORbfVba3x4xzSpqUsJMgWVwfcUlikjD3MjQD6XLJUMee
ENVIRONMENT=development
```

### Observações sobre token

- Para testes locais básicos, pode usar valor de dev (ex.: `AUTH_TOKEN=local-dev-token`).
- Não use token real em logs, prints ou commits.
- Se token real vazar em terminal/chat, revogue imediatamente no provedor OAuth.

## Uso (1 minuto)

```powershell
cd C:\Users\danie\work\github\fito-aimm-amazonia
.\run-local.ps1
.\status-local.ps1
.\run-tests-local.ps1
```

Para parar:

```powershell
.\stop-local.ps1
```

## Resultado esperado dos testes

- `GET /health` → `200`
- `GET /api/worldbank/countries` sem Authorization → `401`
- `GET /api/worldbank/countries` com `Authorization: Bearer <token>` → `200`  
  (ou `502` se backend indisponível)

## Troubleshooting rápido

### 1) `curl: (7) Could not connect to server`
Serviço não está no ar.

```powershell
.\status-local.ps1
.\run-local.ps1
```

### 2) `/health` retorna 404
Caddy pode ter carregado configuração errada/antiga.

```powershell
.\stop-local.ps1
.\run-local.ps1
```

### 3) `/api/...` com Bearer retorna 502
Gateway ativo, mas backend não respondeu.

```powershell
.\stop-local.ps1
.\run-local.ps1
```

### 4) Porta ocupada

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### 5) PowerShell bloqueando script

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run-local.ps1
```

## Segurança

- Nunca commitar `.env` com credenciais reais.
- `status-local.ps1` mascara `Authorization: Bearer ...`.