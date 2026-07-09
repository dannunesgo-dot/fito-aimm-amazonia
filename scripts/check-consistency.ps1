# check-consistency.ps1
# Verificação rápida de consistência do repositório Fito+ Amazônia AIMM
#
# Uso:
#   .\scripts\check-consistency.ps1
#   .\scripts\check-consistency.ps1 -ProjectRoot "C:\caminho\para\repositorio"
#
# Retorna exit code 0 se tudo OK, 1 se houver falhas.

param(
  [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$pass = 0
$fail = 0
$warn = 0

function Write-Check([string]$label, [bool]$ok, [string]$detail = "") {
  if ($ok) {
    Write-Host "  [OK] $label" -ForegroundColor Green
    $script:pass++
  } else {
    Write-Host "  [FAIL] $label" -ForegroundColor Red
    if ($detail) { Write-Host "       $detail" -ForegroundColor DarkRed }
    $script:fail++
  }
}

function Write-Warn([string]$label, [string]$detail = "") {
  Write-Host "  [WARN] $label" -ForegroundColor Yellow
  if ($detail) { Write-Host "        $detail" -ForegroundColor DarkYellow }
  $script:warn++
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Verificacao de Consistencia — Fito+ Amazonia AIMM" -ForegroundColor Cyan
Write-Host " Raiz: $ProjectRoot" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------------
# 1) Arquivos essenciais de execucao
# ------------------------------------------------------------------
Write-Host "1. Arquivos essenciais de execucao" -ForegroundColor White

$essentials = @(
  "app.py",
  "requirements.txt",
  ".env.example",
  "run-local.ps1",
  "stop-local.ps1",
  "status-local.ps1",
  "run-tests-local.ps1"
)

foreach ($f in $essentials) {
  $path = Join-Path $ProjectRoot $f
  Write-Check $f (Test-Path -LiteralPath $path) "Arquivo nao encontrado: $path"
}

# ------------------------------------------------------------------
# 2) Presenca de .env (nao versionado)
# ------------------------------------------------------------------
Write-Host ""
Write-Host "2. Ambiente local" -ForegroundColor White

$envPath = Join-Path $ProjectRoot ".env"
if (Test-Path -LiteralPath $envPath) {
  Write-Check ".env presente (ambiente configurado)" $true
} else {
  Write-Warn ".env ausente" "Execute: copy .env.example .env  e preencha os valores"
}

$venvPy = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
Write-Check ".venv\Scripts\python.exe presente" (Test-Path -LiteralPath $venvPy) `
  "Crie com: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"

# ------------------------------------------------------------------
# 3) Caddy disponivel no PATH
# ------------------------------------------------------------------
Write-Host ""
Write-Host "3. Dependencias de sistema" -ForegroundColor White

$caddyOk = $null -ne (Get-Command caddy -ErrorAction SilentlyContinue)
Write-Check "caddy no PATH" $caddyOk "Instale Caddy e adicione ao PATH: https://caddyserver.com/docs/install"

# ------------------------------------------------------------------
# 4) Consistencia de documentacao
# ------------------------------------------------------------------
Write-Host ""
Write-Host "4. Documentacao de execucao" -ForegroundColor White

$docs = @(
  "README.md",
  "README-local.md",
  "docs/INDEX.md"
)

foreach ($d in $docs) {
  $path = Join-Path $ProjectRoot $d
  Write-Check $d (Test-Path -LiteralPath $path) "Documento ausente: $path"
}

# Verificar se README.md menciona run-local.ps1 como comando oficial
$readmePath = Join-Path $ProjectRoot "README.md"
if (Test-Path -LiteralPath $readmePath) {
  $readmeContent = Get-Content -LiteralPath $readmePath -Raw
  $mentionsOfficial = $readmeContent -match "run-local\.ps1"
  Write-Check "README.md menciona run-local.ps1" $mentionsOfficial `
    "README.md deve documentar run-local.ps1 como comando oficial"
}

# ------------------------------------------------------------------
# 5) tmp/ nao contem artefatos versionados indesejados
# ------------------------------------------------------------------
Write-Host ""
Write-Host "5. Higiene de repositorio" -ForegroundColor White

$tmpPath = Join-Path $ProjectRoot "tmp"
if (Test-Path -LiteralPath $tmpPath) {
  $tmpFiles = Get-ChildItem -LiteralPath $tmpPath -File | Where-Object { $_.Name -ne ".gitkeep" }
  if ($tmpFiles.Count -eq 0) {
    Write-Check "tmp/ limpa (apenas .gitkeep)" $true
  } else {
    Write-Warn "tmp/ contém $($tmpFiles.Count) arquivo(s) além de .gitkeep" `
      "Verifique se estao no .gitignore: $($tmpFiles.Name -join ', ')"
  }
} else {
  Write-Warn "Pasta tmp/ nao encontrada" "Crie com: mkdir tmp; touch tmp/.gitkeep"
}

$gitignorePath = Join-Path $ProjectRoot ".gitignore"
if (Test-Path -LiteralPath $gitignorePath) {
  $gi = Get-Content -LiteralPath $gitignorePath -Raw
  Write-Check ".gitignore inclui tmp/*" ($gi -match "tmp/\*") `
    "Adicione 'tmp/*' e '!tmp/.gitkeep' ao .gitignore"
  Write-Check ".gitignore inclui logs/" ($gi -match "logs/") `
    "Adicione 'logs/' ao .gitignore"
}

# ------------------------------------------------------------------
# Resumo
# ------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
$total = $pass + $fail + $warn
Write-Host " Resultado: $pass OK | $fail FALHA | $warn AVISO | $total verificacoes" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($fail -gt 0) {
  Write-Host "Corrija as falhas acima antes de iniciar o ambiente." -ForegroundColor Red
  exit 1
} elseif ($warn -gt 0) {
  Write-Host "Verifique os avisos para garantir execucao correta." -ForegroundColor Yellow
  exit 0
} else {
  Write-Host "Tudo OK. Ambiente pronto para .\run-local.ps1" -ForegroundColor Green
  exit 0
}
