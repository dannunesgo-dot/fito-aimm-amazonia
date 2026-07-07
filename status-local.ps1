param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia",
  [switch]$OnlyProject = $true
)

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$ErrorActionPreference = "SilentlyContinue"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
  throw "ProjectRoot não encontrado: $ProjectRoot"
}
Set-Location -LiteralPath $ProjectRoot

function Mask-AuthHeader([string]$line) {
  if ([string]::IsNullOrWhiteSpace($line)) { return $line }
  return ($line -replace '(?i)(Authorization:\s*Bearer\s+)[^\s"]+', '$1***REDACTED***')
}

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

function HttpCode {
  param(
    [string]$Url,
    [hashtable]$Headers = $null
  )
  try {
    $r = Invoke-WebRequest -Uri $Url -Headers $Headers -SkipHttpErrorCheck -TimeoutSec 8
    return [int]$r.StatusCode
  } catch {
    return -1
  }
}

function Normalize-String([string]$s) {
  if ([string]::IsNullOrWhiteSpace($s)) { return "" }
  return $s.Trim().ToLowerInvariant()
}

function Get-ProcDetails([string]$Name, [string]$Root, [bool]$OnlyFromProject) {
  $all = @(Get-CimInstance Win32_Process -Filter "Name='$Name'" |
    Select-Object ProcessId, Name, ExecutablePath, CommandLine)

  if (-not $OnlyFromProject) {
    return @($all | ForEach-Object {
      [PSCustomObject]@{
        ProcessId      = $_.ProcessId
        Name           = $_.Name
        ExecutablePath = $_.ExecutablePath
        CommandLine    = $_.CommandLine
        Source         = "all-processes"
      }
    })
  }

  $rootNorm = Normalize-String $Root
  $filtered = @($all | Where-Object {
    $cmd = Normalize-String $_.CommandLine
    $exe = Normalize-String $_.ExecutablePath
    ($cmd -like "*$rootNorm*") -or ($exe -like "*$rootNorm*")
  })

  return @($filtered | ForEach-Object {
    [PSCustomObject]@{
      ProcessId      = $_.ProcessId
      Name           = $_.Name
      ExecutablePath = $_.ExecutablePath
      CommandLine    = $_.CommandLine
      Source         = "project-filter"
    }
  })
}

function Get-ListeningPidByPort([int]$Port) {
  try {
    $rows = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
    if ($rows.Count -eq 0) { return @() }
    return @($rows | Select-Object -ExpandProperty OwningProcess -Unique)
  } catch {
    return @()
  }
}

function Get-ProcessByPid([int]$Pid) {
  return @(Get-CimInstance Win32_Process -Filter "ProcessId=$Pid" |
    Select-Object ProcessId, Name, ExecutablePath, CommandLine)
}

function Get-ProcessNameByPid([int]$Pid) {
  try {
    return (Get-Process -Id $Pid -ErrorAction Stop).ProcessName
  } catch {
    return $null
  }
}

function Is-CaddyProcessName([string]$processName) {
  $n = Normalize-String $processName
  return ($n -eq "caddy" -or $n -eq "caddy.exe")
}

function Get-CaddyPidOn8080 {
  $pids = @(Get-ListeningPidByPort -Port 8080)
  foreach ($procId in $pids) {
    $pname = Get-ProcessNameByPid -Pid $procId
    if (Is-CaddyProcessName $pname) {
      return $procId
    }
  }
  return $null
}

Load-DotEnv

Write-Host "==> [status] Processos (com executável)" -ForegroundColor Cyan
Write-Host ("Filtro projeto atual: {0}" -f ($(if ($OnlyProject) { "ATIVO" } else { "DESATIVADO" })))

# Base (filtro normal)
$caddy  = @(Get-ProcDetails -Name "caddy.exe"  -Root $ProjectRoot -OnlyFromProject $OnlyProject)
$python = @(Get-ProcDetails -Name "python.exe" -Root $ProjectRoot -OnlyFromProject $OnlyProject)

# Fallback Caddy por porta 8080 + validação de nome do processo
if (($OnlyProject) -and (@($caddy).Count -eq 0)) {
  $caddyPid = Get-CaddyPidOn8080
  if ($caddyPid) {
    $proc = @(Get-ProcessByPid -Pid $caddyPid)
    if (@($proc).Count -gt 0) {
      $fallbackObj = [PSCustomObject]@{
        ProcessId      = $proc[0].ProcessId
        Name           = $proc[0].Name
        ExecutablePath = $proc[0].ExecutablePath
        CommandLine    = $proc[0].CommandLine
        Source         = "port-8080-fallback(caddy-validated)"
      }
      $caddy = @($fallbackObj)
    }
  }
}

if (@($caddy).Count -gt 0) {
  Write-Host "`n[CADDY]" -ForegroundColor Green
  $caddy | Sort-Object ProcessId | Format-Table -AutoSize `
    @{Label="PID";Expression={$_.ProcessId}}, `
    @{Label="Source";Expression={$_.Source}}, `
    @{Label="Exe";Expression={$_.ExecutablePath}}, `
    @{Label="CommandLine";Expression={$_.CommandLine}}
} else {
  Write-Warning "Caddy não encontrado com o filtro atual."
}

if (@($python).Count -gt 0) {
  Write-Host "`n[PYTHON]" -ForegroundColor Green
  $python | Sort-Object ProcessId | Format-Table -AutoSize `
    @{Label="PID";Expression={$_.ProcessId}}, `
    @{Label="Source";Expression={$_.Source}}, `
    @{Label="Exe";Expression={$_.ExecutablePath}}, `
    @{Label="CommandLine";Expression={$_.CommandLine}}
} else {
  Write-Warning "Python não encontrado com o filtro atual."
}

Write-Host "`n==> [status] Portas (8000/8080)" -ForegroundColor Cyan
$ports = @(netstat -ano | Select-String ":(8000|8080)\s+.*LISTENING")
if (@($ports).Count -gt 0) {
  $ports | ForEach-Object { Write-Host $_.Line }
} else {
  Write-Warning "Nenhuma porta 8000/8080 em LISTENING."
}

Write-Host "`n==> [status] HTTP checks" -ForegroundColor Cyan
$h = HttpCode -Url "http://127.0.0.1:8080/health"
$u = HttpCode -Url "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1"

if ([string]::IsNullOrWhiteSpace($env:AUTH_TOKEN)) {
  $tokenLine = "Authorization: Bearer (AUTH_TOKEN ausente)"
  $b = -1
} else {
  $tokenLine = "Authorization: Bearer $($env:AUTH_TOKEN)"
  $headers = @{ Authorization = "Bearer $env:AUTH_TOKEN" }
  $b = HttpCode -Url "http://127.0.0.1:8080/api/worldbank/countries?per_page=1&page=1" -Headers $headers
}

Write-Host (Mask-AuthHeader $tokenLine)
Write-Host "/health                         => $h"
Write-Host "/api/worldbank/countries        => $u (esperado 401)"
Write-Host "/api/... com Bearer token       => $b (esperado 200 ou 502)"

Write-Host "`n==> [status] Logs (tail 10)" -ForegroundColor Cyan

if (Test-Path -LiteralPath ".\logs\backend.out.log") {
  Write-Host "--- backend.out.log ---"
  Get-Content -LiteralPath ".\logs\backend.out.log" -Tail 10
}
if (Test-Path -LiteralPath ".\logs\backend.err.log") {
  Write-Host "--- backend.err.log ---"
  Get-Content -LiteralPath ".\logs\backend.err.log" -Tail 10
}
if (Test-Path -LiteralPath ".\logs\caddy.out.log") {
  Write-Host "--- caddy.out.log ---"
  Get-Content -LiteralPath ".\logs\caddy.out.log" -Tail 10
}
if (Test-Path -LiteralPath ".\logs\caddy.err.log") {
  Write-Host "--- caddy.err.log ---"
  Get-Content -LiteralPath ".\logs\caddy.err.log" -Tail 10
}