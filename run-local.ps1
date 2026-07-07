param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia"
)

$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
  throw "ProjectRoot não encontrado: $ProjectRoot"
}
Set-Location -LiteralPath $ProjectRoot

function Write-Step([string]$msg) { Write-Host "==> [run] $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg)   { Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "⚠️ $msg" -ForegroundColor Yellow }

function Load-DotEnv {
  param([string]$Path = ".\.env")
  if (-not (Test-Path -LiteralPath $Path)) { return }

  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }

    $parts = $line.Split("=", 2)
    if ($parts.Length -eq 2) {
      $key = $parts[0].Trim()
      $val = $parts[1].Trim().Trim('"').Trim("'")
      Set-Item -Path "Env:$key" -Value $val
    }
  }
}

function Get-PidsListeningOnPort {
  param([int]$Port)
  try {
    $rows = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
    if ($rows.Count -eq 0) { return @() }
    return @($rows | Select-Object -ExpandProperty OwningProcess -Unique)
  } catch {
    return @()
  }
}

function Stop-PidsOnPorts {
  param([int[]]$Ports = @(8000,8080))

  $all = @()
  foreach ($p in $Ports) {
    $all += @(Get-PidsListeningOnPort -Port $p)
  }
  $all = @($all | Select-Object -Unique)

  if (@($all).Count -eq 0) {
    Write-Step "Nenhum processo ocupando portas $($Ports -join ', ')."
    return
  }

  Write-Step "Encerrando processos nas portas $($Ports -join ', '): $($all -join ', ')"
  foreach ($procId in $all) {
    try {
      Stop-Process -Id $procId -Force -ErrorAction Stop
      Write-Ok "PID $procId encerrado."
    } catch {
      Write-Warn ("Não foi possível encerrar PID {0}: {1}" -f $procId, $_.Exception.Message)
    }
  }
  Start-Sleep -Seconds 1
}

function Wait-PortListening {
  param([int]$Port, [int]$TimeoutSec = 20)

  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    if (@(Get-PidsListeningOnPort -Port $Port).Count -gt 0) { return $true }
    Start-Sleep -Milliseconds 400
  }
  return $false
}

function HttpCode {
  param(
    [string]$Url,
    [hashtable]$Headers = $null
  )
  try {
    $r = Invoke-WebRequest -Uri $Url -Headers $Headers -SkipHttpErrorCheck -TimeoutSec 10
    return [int]$r.StatusCode
  } catch {
    return -1
  }
}

# --------------------------------------------------------------------------------

Load-DotEnv

Write-Step "Limpando processos antigos SOMENTE nas portas 8000/8080"
Stop-PidsOnPorts -Ports @(8000,8080)

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
'@ | Set-Content -LiteralPath .\Caddyfile.local -Encoding utf8

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) { throw "Falta .\.venv\Scripts\python.exe" }
if (-not (Test-Path -LiteralPath ".\app.py")) { throw "Falta .\app.py" }

New-Item -ItemType Directory -Path .\logs -Force | Out-Null

# Limpa logs da execução anterior
$logFiles = @(
  ".\logs\backend.out.log",
  ".\logs\backend.err.log",
  ".\logs\caddy.out.log",
  ".\logs\caddy.err.log"
)
foreach ($lf in $logFiles) {
  if (Test-Path -LiteralPath $lf) { Remove-Item -LiteralPath $lf -Force -ErrorAction SilentlyContinue }
}

Write-Step "Subindo Flask (venv python)"
Start-Process -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList ".\app.py" `
  -WorkingDirectory $ProjectRoot `
  -RedirectStandardOutput ".\logs\backend.out.log" `
  -RedirectStandardError ".\logs\backend.err.log" `
  -WindowStyle Hidden | Out-Null

if (-not (Wait-PortListening -Port 8000 -TimeoutSec 20)) {
  Write-Warn "Backend não abriu 8000. Verifique .\logs\backend.err.log"
}

Write-Step "Subindo Caddy"
Start-Process -FilePath "caddy" `
  -ArgumentList @("run","--config",".\Caddyfile.local") `
  -WorkingDirectory $ProjectRoot `
  -RedirectStandardOutput ".\logs\caddy.out.log" `
  -RedirectStandardError ".\logs\caddy.err.log" `
  -WindowStyle Hidden | Out-Null

if (-not (Wait-PortListening -Port 8080 -TimeoutSec 20)) {
  throw "Caddy não abriu 8080. Verifique .\logs\caddy.err.log"
}

$healthUrl = "http://127.0.0.1:8080/health"
$apiUrl    = "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1"

$h = HttpCode -Url $healthUrl
$u = HttpCode -Url $apiUrl
$b = if ($env:AUTH_TOKEN) {
  HttpCode -Url $apiUrl -Headers @{ Authorization = "Bearer $env:AUTH_TOKEN" }
} else { -1 }

Write-Host ""
Write-Host "==> [run] Health checks finais" -ForegroundColor Cyan
Write-Host "/health                         => $h"
Write-Host "/api/worldbank/countries        => $u (esperado 401)"
Write-Host "/api/... com Bearer token       => $b (esperado 200 ou 502 se backend cair)"
Write-Host ""
Write-Ok "Ambiente local iniciado."
Write-Host "Logs:"
Write-Host " - .\logs\backend.out.log"
Write-Host " - .\logs\backend.err.log"
Write-Host " - .\logs\caddy.out.log"
Write-Host " - .\logs\caddy.err.log"