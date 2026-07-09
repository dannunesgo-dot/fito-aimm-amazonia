param(
  [string]$BaseBranch = "main",
  [string]$FeatureBranch = "docs/import-wb-artifacts",
  [switch]$DoHardResetClean
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "ERRO: $msg" -ForegroundColor Red
  exit 1
}

function Info($msg) {
  Write-Host ">> $msg" -ForegroundColor Cyan
}

# 0) Checagens iniciais
Info "Validando repositório Git..."
git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) { Fail "Não está em um repositório Git." }

# 1) Snapshot de segurança
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = ".safety\$ts"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Info "Gerando snapshot em $backupDir ..."
git diff | Out-File -Encoding utf8 "$backupDir\diff-working.patch"
git diff --staged | Out-File -Encoding utf8 "$backupDir\diff-staged.patch"
git status --porcelain | Out-File -Encoding utf8 "$backupDir\status.txt"

# 2) Atualizar refs remotas
Info "Fazendo fetch..."
git fetch origin

# 3) Ir para base branch e atualizar
Info "Checkout base branch: $BaseBranch"
git checkout $BaseBranch
if ($LASTEXITCODE -ne 0) { Fail "Falha ao trocar para $BaseBranch" }

Info "Pull da base branch..."
git pull origin $BaseBranch
if ($LASTEXITCODE -ne 0) { Fail "Falha no pull de $BaseBranch" }

# 4) Criar/resetar branch de trabalho
Info "Preparando branch de docs: $FeatureBranch"
git checkout -B $FeatureBranch
if ($LASTEXITCODE -ne 0) { Fail "Falha ao criar/resetar $FeatureBranch" }

# 5) Opcional: hard reset + clean seguro
if ($DoHardResetClean) {
  Info "Preview do clean (NADA apagado ainda):"
  git clean -nd

  Info "Executando reset/clean..."
  git reset --hard
  if ($LASTEXITCODE -ne 0) { Fail "Falha em git reset --hard" }

  git clean -fd
  if ($LASTEXITCODE -ne 0) { Fail "Falha em git clean -fd" }

  Info "Reatualizando base após limpeza..."
  git checkout $BaseBranch
  git pull origin $BaseBranch
  git checkout -B $FeatureBranch
}

# 6) Stage estrito: apenas docs/*
Info "Limpando stage atual..."
git restore --staged .

Info "Adicionando apenas docs/* ..."
git add docs

# 7) Validação automática de escopo
Info "Validando escopo staged..."
$staged = git diff --staged --name-only
if (-not $staged) { Fail "Nenhum arquivo staged em docs/." }

$invalid = @()
foreach ($f in $staged) {
  if (-not ($f -like "docs/*")) { $invalid += $f }
}

if ($invalid.Count -gt 0) {
  Write-Host "Arquivos fora de docs/ encontrados no stage:" -ForegroundColor Yellow
  $invalid | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
  Fail "Escopo inválido. Remova do stage: git restore --staged <arquivo>"
}

Info "Escopo válido: somente docs/*"

# 8) Mostrar resumo final
Write-Host ""
Write-Host "===== RESUMO =====" -ForegroundColor Green
Write-Host "Branch atual: $(git branch --show-current)"
Write-Host "Arquivos staged:"
$staged | ForEach-Object { Write-Host " - $_" }
Write-Host ""
Write-Host "Próximos comandos:"
Write-Host "git commit -m `"docs: update docs artifacts`""
Write-Host "git push -u origin $FeatureBranch"
Write-Host "Start-Process `"https://github.com/dannunesgo-dot/fito-aimm-amazonia/compare/$BaseBranch...$FeatureBranch?expand=1`""
