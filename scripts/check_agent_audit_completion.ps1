param(
  [string]$RepoRoot = "C:\Users\danie\work\github\fito-aimm-amazonia"
)

Set-Location $RepoRoot
git fetch origin
git pull origin main

$required = @(
  "docs/UI_VISUAL_GUIDELINES_FACTUAL.md",
  "docs/UI_ARCHITECTURE_ALIGNMENT_FACTUAL.md",
  "docs/UI_VISUAL_EVIDENCE_TABLE.csv",
  "docs/UI_MUNICIPAL_COVERAGE_GAPS.md"
)

$missing = @()
foreach ($f in $required) {
  if (-not (Test-Path $f)) { $missing += $f }
}

if ($missing.Count -gt 0) {
  Write-Host "PENDENTE: auditoria não concluída. Arquivos ausentes:" -ForegroundColor Yellow
  $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
  exit 1
}

Write-Host "OK: auditoria concluída. Todos os entregáveis existem." -ForegroundColor Green

Write-Host "`nResumo de tamanho/última modificação:" -ForegroundColor Cyan
Get-Item $required | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize

Write-Host "`nValidação de conteúdo mínimo..." -ForegroundColor Cyan
$checks = @{
  "docs/UI_VISUAL_GUIDELINES_FACTUAL.md"   = @("Paleta oficial", "Legendas oficiais", "NÃO COMPROVADO")
  "docs/UI_ARCHITECTURE_ALIGNMENT_FACTUAL.md" = @("Bloco UI", "Endpoint", "Status")
  "docs/UI_VISUAL_EVIDENCE_TABLE.csv"      = @("tema,status,branch,arquivo,linhas,evidencia,impacto_ui,acao_recomendada")
  "docs/UI_MUNICIPAL_COVERAGE_GAPS.md"     = @("Manaus", "Benjamin Constant", "Belém", "Santarém")
}

$failed = $false
foreach ($file in $checks.Keys) {
  $content = Get-Content $file -Raw
  foreach ($token in $checks[$file]) {
    if ($content -notmatch [regex]::Escape($token)) {
      Write-Host "FALHA: '$token' não encontrado em $file" -ForegroundColor Red
      $failed = $true
    }
  }
}

if ($failed) {
  Write-Host "PENDENTE: arquivos existem, mas conteúdo mínimo está incompleto." -ForegroundColor Yellow
  exit 2
}

Write-Host "OK FINAL: auditoria concluída e conteúdo mínimo validado." -ForegroundColor Green
exit 0