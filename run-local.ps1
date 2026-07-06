param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

function Write-Step($msg) { Write-Host "==> [run] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "⚠️ $msg" -ForegroundColor Yellow }

function Load-DotEnv {
  param([string]$Path = ".\.env")
  if (-not (Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $parts = $line.Split("=", 2)
    if ($parts.Length -eq 2) {
      Set-Item -Path "Env:$($parts[0].Trim())" -Value $parts[1].Trim().Trim('"').Trim("'")
    }
  }
}

function Get-PidsListeningOnPort {
  param([int]$Port)
  $rows = netstat -ano -p tcp | Select-String "LISTENING\s+(\d+)$"
  $pids = @()
  foreach ($r in $rows) {
    $line = ($r.Line -replace "\s+", " ").Trim()
    $cols = $line.Split(" ")
    if ($cols.Length -lt 5) { continue }
    $localAddr = $cols[1]
    $state     = $cols[3]
    $procIdRaw = $cols[4]
    if ($state -ne "LISTENING") { continue }
    if ($localAddr -match ":(\d+)$" -and [int]$Matches[1] -eq $Port) {
      $pids += [int]$procIdRaw
    }
  }
  return ($pids | Select-Object -Unique)
}

function Stop-PidsOnPorts {
  param([int[]]$Ports = @(8000,8080))
  $all = @()
  foreach ($p in $Ports) { $all += Get-PidsListeningOnPort -Port $p }
  $all = $all | Select-Object -Unique
  if (-not $all -or $all.Count -eq 0) {
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
    if ((Get-PidsListeningOnPort -Port $Port).Count -gt 0) { return $true }
    Start-Sleep -Milliseconds 400
  }
  return $false
}

function HttpCode([string]$Url, [hashtable]$Headers = $null) {
  try {
    $r = Invoke-WebRequest -Uri $Url -Headers $Headers -SkipHttpErrorCheck -TimeoutSec 10
    return [int]$r.StatusCode
  } catch { return -1 }
}

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
'@ | Set-Content .\Caddyfile.local -Encoding utf8

if (-not (Test-Path ".\.venv\Scripts\python.exe")) { throw "Falta .\.venv\Scripts\python.exe" }
if (-not (Test-Path ".\app.py")) { throw "Falta .\app.py" }

New-Item -ItemType Directory -Path .\logs -Force | Out-Null

Write-Step "Subindo Flask"
Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
  "-NoExit",
  "-Command",
  "& .\.venv\Scripts\python.exe .\app.py *>> .\logs\backend.log"
) | Out-Null

if (-not (Wait-PortListening -Port 8000 -TimeoutSec 20)) {
  Write-Warn "Backend não abriu 8000 (ver .\logs\backend.log)"
}

Write-Step "Subindo Caddy"
Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
  "-NoExit",
  "-Command",
  "caddy run --config .\Caddyfile.local *>> .\logs\caddy.log"
) | Out-Null

if (-not (Wait-PortListening -Port 8080 -TimeoutSec 20)) {
  throw "Caddy não abriu 8080 (ver .\logs\caddy.log)"
}

$h = HttpCode "http://127.0.0.1:8080/health"
$u = HttpCode "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1"
$b = if ($env:AUTH_TOKEN) {
  HttpCode "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1" @{ Authorization = "Bearer $env:AUTH_TOKEN" }
} else { -1 }

Write-Host "/health                         => $h"
Write-Host "/api/worldbank/countries        => $u (esperado 401)"
Write-Host "/api/... com Bearer token       => $b (esperado 200 ou 502 se backend cair)"
Write-Host "`n✅ Ambiente local iniciado."