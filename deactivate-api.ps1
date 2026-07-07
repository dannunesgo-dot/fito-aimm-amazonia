param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

Write-Host "==> [deactivate-api] Parando ambiente..." -ForegroundColor Cyan
.\stop-local.ps1
.\status-local.ps1

Write-Host "`n✅ Ambiente local finalizado." -ForegroundColor Green