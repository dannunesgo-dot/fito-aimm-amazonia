# Ambiente local (Flask + Caddy)

Subida rápida da API local com proxy/autorização para integração com World Bank API.

## Pré-requisitos

- Windows + PowerShell
- Python com `.venv` no projeto
- Dependências instaladas
- Caddy instalado e disponível no PATH

## Arquivos e scripts locais

- `.\run-local.ps1` → sobe Flask + Caddy e faz smoke tests
- `.\status-local.ps1` → mostra processos, portas e checks HTTP (token mascarado)
- `.\stop-local.ps1` → para somente processos vinculados às portas 8000/8080
- `.\run-tests-local.ps1` → carrega `.env` e executa testes
- `.\scripts\test_api_integration.ps1` → testes HTTP de integração Gateway/Backend

## Configuração do `.env` (raiz do projeto)

Crie/edite `.env`:

```dotenv
WORLDBANK_API_URL=https://api.worldbank.org/v2
GATEWAY_URL=http://127.0.0.1:8080
BACKEND_URL=http://127.0.0.1:8000
AUTH_TOKEN=local-dev-token
ENVIRONMENT=development
```

> Nunca commitar `.env` com token real.

## Instalação rápida de dependências

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install flask requests python-dotenv
```

## Uso (fluxo padrão)

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

## Resultado esperado

- `GET /health` → `200`
- `GET /api/worldbank/countries` sem Authorization → `401`
- `GET /api/worldbank/countries` com Bearer token válido local → `200`  
  (`502` indica backend fora do ar)

## Troubleshooting

### 1) `502` com token
Backend não subiu ou caiu.
```powershell
.\status-local.ps1
Get-Content .\logs\backend.log -Tail 50
```

### 2) `ModuleNotFoundError: flask`
Use Python da venv:
```powershell
.\.venv\Scripts\python.exe .\app.py
```

### 3) Porta ocupada
```powershell
.\stop-local.ps1 -ShowOnly
.\stop-local.ps1
```

### 4) Script bloqueado pelo PowerShell
```powershell
Set-ExecutionPolicy -Scope Process Bypass
```