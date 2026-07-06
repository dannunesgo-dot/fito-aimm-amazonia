param(
  [int[]]$Ports = @(8000,8080),
  [switch]$ShowOnly
)

$ErrorActionPreference = "Continue"

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
    $procIdRaw = $cols[4]   # <- não usar $pid

    if ($state -ne "LISTENING") { continue }

    if ($localAddr -match ":(\d+)$") {
      $p = [int]$Matches[1]
      if ($p -eq $Port) { $pids += [int]$procIdRaw }
    }
  }

  return ($pids | Select-Object -Unique)
}

Write-Host "==> [stop] Localizando processos vinculados às portas: $($Ports -join ', ')" -ForegroundColor Cyan

$targets = @()
foreach ($port in $Ports) {
  $pids = Get-PidsListeningOnPort -Port $port
  foreach ($procId in $pids) {
    try {
      $proc = Get-Process -Id $procId -ErrorAction Stop
      $targets += [PSCustomObject]@{
        Port = $port
        PID  = $procId
        Name = $proc.ProcessName
      }
    } catch {
      $targets += [PSCustomObject]@{
        Port = $port
        PID  = $procId
        Name = "(desconhecido)"
      }
    }
  }
}

$targets = $targets | Sort-Object PID -Unique

if (-not $targets -or $targets.Count -eq 0) {
  Write-Host "Nenhum processo escutando nessas portas." -ForegroundColor Yellow
  exit 0
}

Write-Host "Processos alvo:" -ForegroundColor Green
$targets | Format-Table -AutoSize

if ($ShowOnly) {
  Write-Host "Modo -ShowOnly: nenhum processo foi encerrado." -ForegroundColor Yellow
  exit 0
}

Write-Host "==> [stop] Encerrando processos alvo..." -ForegroundColor Cyan
foreach ($t in $targets) {
  try {
    Stop-Process -Id $t.PID -Force -ErrorAction Stop
    Write-Host "✅ Encerrado PID $($t.PID) ($($t.Name)) [porta $($t.Port)]" -ForegroundColor Green
  } catch {
    Write-Warning "Falha ao encerrar PID $($t.PID): $($_.Exception.Message)"
  }
}

Start-Sleep -Milliseconds 500

Write-Host "`n==> [stop] Verificação final" -ForegroundColor Cyan
foreach ($port in $Ports) {
  $remaining = Get-PidsListeningOnPort -Port $port
  if ($remaining -and $remaining.Count -gt 0) {
    Write-Warning "Porta $port ainda ocupada por PID(s): $($remaining -join ', ')"
  } else {
    Write-Host "✅ Porta $port liberada." -ForegroundColor Green
  }
}