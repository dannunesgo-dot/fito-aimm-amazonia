param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia",
  [switch]$OnlyProject = $true
)

$ErrorActionPreference = "SilentlyContinue"
Set-Location $ProjectRoot

function Mask-AuthHeader([string]$line) {
  if ([string]::IsNullOrWhiteSpace($line)) { return $line }
  return ($line -replace '(?i)(Authorization:\s*Bearer\s+)[^\s"]+', '$1***REDACTED***')
}

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

function HttpCode([string]$url, [hashtable]$headers = $null) {
  try {
    $r = Invoke-WebRequest -Uri $url -Headers $headers -SkipHttpErrorCheck -TimeoutSec 8
    return [int]$r.StatusCode
  } catch {
    return -1
  }
}

function Get-ProcDetails([string]$Name, [string]$Root, [bool]$OnlyFromProject) {
  $all = Get-CimInstance Win32_Process -Filter "Name='$Name'" |
    Select-Object ProcessId, Name, ExecutablePath, CommandLine

  if (-not $OnlyFromProject) { return $all }

  $rootNorm = $Root.ToLowerInvariant()
  return $all | Where-Object {
    $cmd = ($_.CommandLine   | Out-String).Trim().ToLowerInvariant()
    $exe = ($_.ExecutablePath | Out-String).Trim().ToLowerInvariant()
    ($cmd -like "*$rootNorm*") -or ($exe -like "*$rootNorm*")
  }
}

Load-DotEnv

Write-Host "==> [status] Processos (com executável)" -ForegroundColor Cyan
Write-Host ("Filtro projeto atual: {0}" -f ($(if ($OnlyProject) { "ATIVO" } else { "DESATIVADO" })))

$caddy  = Get-ProcDetails -Name "caddy.exe"  -Root $ProjectRoot -OnlyFromProject $OnlyProject
$python = Get-ProcDetails -Name "python.exe" -Root $ProjectRoot -OnlyFromProject $OnlyProject

if ($caddy) {
  Write-Host "`n[CADDY]" -ForegroundColor Green
  $caddy | Sort-Object ProcessId | Format-Table -AutoSize `
    @{Label="PID";Expression={$_.ProcessId}}, `
    @{Label="Exe";Expression={$_.ExecutablePath}}, `
    @{Label="CommandLine";Expression={$_.CommandLine}}
} else {
  Write-Warning "Caddy não encontrado com o filtro atual."
}

if ($python) {
  Write-Host "`n[PYTHON]" -ForegroundColor Green
  $python | Sort-Object ProcessId | Format-Table -AutoSize `
    @{Label="PID";Expression={$_.ProcessId}}, `
    @{Label="Exe";Expression={$_.ExecutablePath}}, `
    @{Label="CommandLine";Expression={$_.CommandLine}}
} else {
  Write-Warning "Python não encontrado com o filtro atual."
}

Write-Host "`n==> [status] Portas (8000/8080)" -ForegroundColor Cyan
$ports = netstat -ano | Select-String ":(8000|8080)\s+.*LISTENING"
if ($ports) { $ports | ForEach-Object { Write-Host $_.Line } }
else { Write-Warning "Nenhuma porta 8000/8080 em LISTENING." }

Write-Host "`n==> [status] HTTP checks" -ForegroundColor Cyan
$h = HttpCode "http://127.0.0.1:8080/health"
$u = HttpCode "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1"

if ([string]::IsNullOrWhiteSpace($env:AUTH_TOKEN)) {
  $tokenLine = "Authorization: Bearer (AUTH_TOKEN ausente)"
  $b = -1
} else {
  $tokenLine = "Authorization: Bearer $($env:AUTH_TOKEN)"
  $headers = @{ Authorization = "Bearer $env:AUTH_TOKEN" }
  $b = HttpCode "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1" $headers
}

Write-Host (Mask-AuthHeader $tokenLine)
Write-Host "/health                         => $h"
Write-Host "/api/worldbank/countries        => $u (esperado 401)"
Write-Host "/api/... com Bearer token       => $b (esperado 200 ou 502)"

Write-Host "`n==> [status] Logs (tail 10)" -ForegroundColor Cyan
if (Test-Path ".\logs\backend.log") {
  Write-Host "--- backend.log ---"
  Get-Content ".\logs\backend.log" -Tail 10
}
if (Test-Path ".\logs\caddy.log") {
  Write-Host "--- caddy.log ---"
  Get-Content ".\logs\caddy.log" -Tail 10
}