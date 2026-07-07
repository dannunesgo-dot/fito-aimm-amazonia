param(
  [string]$ProjectRoot = "C:\Users\danie\work\github\fito-aimm-amazonia"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

Write-Host "==> [activate-api] Encerrando instâncias anteriores..." -ForegroundColor Cyan
.\stop-local.ps1

Write-Host "==> [activate-api] Subindo ambiente..." -ForegroundColor Cyan
.\run-local.ps1

Write-Host "==> [activate-api] Validando status..." -ForegroundColor Cyan
.\status-local.ps1

Write-Host "==> [activate-api] Executando testes..." -ForegroundColor Cyan
.\run-tests-local.ps1

Write-Host "`n✅ API pronta para uso." -ForegroundColor Green