Write-Host "==> [stop] Parando Caddy/Python..." -ForegroundColor Yellow
Get-Process caddy -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

$listen8080 = netstat -ano | Select-String ":8080\s+.*LISTENING"
$listen8000 = netstat -ano | Select-String ":8000\s+.*LISTENING"

if (-not $listen8080 -and -not $listen8000) {
  Write-Host "✅ Ambiente local parado." -ForegroundColor Green
} else {
  Write-Warning "Ainda há processo escutando em 8000/8080. Rode .\status-local.ps1"
}