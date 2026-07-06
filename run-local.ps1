param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

Write-Host "==> [run] Matando processos antigos (caddy/python)..." -ForegroundColor Yellow
Get-Process caddy -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

Write-Host "==> [run] Escrevendo Caddyfile.local..." -ForegroundColor Cyan
@'
{
	admin off
}

:8080 {
	handle /health {
		respond "OK" 200
	}

	handle_path /api/* {
		@missingAuth not header Authorization *
		respond @missingAuth "Unauthorized" 401

		@notBearer not header Authorization "Bearer *"
		respond @notBearer "Unauthorized" 401

		reverse_proxy 127.0.0.1:8000
	}

	handle {
		respond "Not Found" 404
	}
}
'@ | Set-Content .\Caddyfile.local -Encoding utf8

Write-Host "==> [run] Subindo Flask em nova janela..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
  "-NoExit",
  "-Command",
  @'
$env:PYTHONUNBUFFERED="1"
if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }
python .\app.py
'@
) | Out-Null

Start-Sleep -Seconds 2

Write-Host "==> [run] Subindo Caddy em nova janela..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
  "-NoExit",
  "-Command",
  "caddy run --config .\Caddyfile.local"
) | Out-Null

Start-Sleep -Seconds 2

Write-Host "==> [run] Status rápido..." -ForegroundColor Cyan
$listen8000 = netstat -ano | Select-String ":8000\s+.*LISTENING"
$listen8080 = netstat -ano | Select-String ":8080\s+.*LISTENING"

if ($listen8000) { Write-Host "OK  : 8000 LISTENING" -ForegroundColor Green } else { Write-Warning "8000 NÃO está LISTENING" }
if ($listen8080) { Write-Host "OK  : 8080 LISTENING" -ForegroundColor Green } else { Write-Warning "8080 NÃO está LISTENING" }

Write-Host "==> [run] Smoke tests (sem token real)..." -ForegroundColor Cyan
$h = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/health"
$u = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/api/worldbank/countries"
$b = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/api/worldbank/countries" -H "Authorization: Bearer local-dev-token"

Write-Host "/health                         => $h"
Write-Host "/api/worldbank/countries        => $u (esperado 401)"
Write-Host "/api/... com Bearer dummy       => $b (esperado 200 ou 502 se backend cair)"

Write-Host "`n✅ Ambiente local iniciado." -ForegroundColor Green
Write-Host "Use .\status-local.ps1 para checar."