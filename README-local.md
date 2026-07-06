# Ambiente local (Flask + Caddy)

Subida rápida da API local com proxy/autorização.

## Pré-requisitos
- Windows + PowerShell
- Python (com `.venv` no projeto)
- Caddy instalado e disponível no PATH

## Scripts
- `.\run-local.ps1` → sobe Flask + Caddy e faz smoke tests
- `.\status-local.ps1` → mostra processos, portas e checks HTTP (com token mascarado)
- `.\stop-local.ps1` → para Caddy/Python

## Uso (1 minuto)
```powershell
cd C:\Users\danie\work\github\fito-aimm-amazonia
.\run-local.ps1
.\status-local.ps1
```

Para parar:
```powershell
.\stop-local.ps1
```

## Resultado esperado dos testes
- `GET /health` → `200`
- `GET /api/worldbank/countries` sem Authorization → `401`
- `GET /api/worldbank/countries` com `Authorization: Bearer local-dev-token` → `200` (ou `502` se backend cair)

## Troubleshooting rápido

### 1) `curl: (7) Could not connect to server`
Serviço não está no ar.
```powershell
.\status-local.ps1
.\run-local.ps1
```

### 2) `/health` retorna 404
Caddy carregou config errada ou antiga.
```powershell
.\stop-local.ps1
.\run-local.ps1
```

### 3) `/api/...` com Bearer retorna 502
Caddy está ok, mas Flask não subiu/caiu.
- Verifique janela do Flask
- Rode novamente:
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
- Não usar token real em teste local.
- Se token real vazar em terminal/chat, revogar imediatamente no provedor OAuth.
- `status-local.ps1` já mascara `Authorization: Bearer ...`.
