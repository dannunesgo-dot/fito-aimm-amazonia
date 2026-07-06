param(
    [string]$Token = "",
    [string]$GatewayUrl = "http://127.0.0.1:8080"
)

$ErrorActionPreference = "Stop"

function Ok($m){ Write-Host "✅ $m" -ForegroundColor Green }
function Warn($m){ Write-Host "⚠️ $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "❌ $m" -ForegroundColor Red }

Write-Host "==> TESTE 1: /health"
try {
    $r = Invoke-WebRequest -Uri "$GatewayUrl/health" -SkipHttpErrorCheck -TimeoutSec 8
    if ($r.StatusCode -eq 200) { Ok "/health = 200" } else { Err "/health = $($r.StatusCode)" }
} catch { Err "Falha em /health: $($_.Exception.Message)" }

Write-Host "==> TESTE 2: /api/worldbank/countries sem token (esperado 401)"
try {
    $r = Invoke-WebRequest -Uri "$GatewayUrl/api/worldbank/countries" -SkipHttpErrorCheck -TimeoutSec 12
    if ($r.StatusCode -eq 401) { Ok "sem token = 401" } else { Warn "sem token = $($r.StatusCode) (esperado 401)" }
} catch { Err "Falha sem token: $($_.Exception.Message)" }

if ([string]::IsNullOrWhiteSpace($Token)) {
    Warn "Token não informado. Pulando teste autenticado."
    exit 0
}

Write-Host "==> TESTE 3: /api/worldbank/countries com token (esperado 200)"
try {
    $headers = @{ Authorization = "Bearer $Token" }
    $r = Invoke-WebRequest -Uri "$GatewayUrl/api/worldbank/countries?per_page=5" -Headers $headers -SkipHttpErrorCheck -TimeoutSec 20
    if ($r.StatusCode -eq 200) { Ok "com token = 200" } else { Warn "com token = $($r.StatusCode) (esperado 200)" }
} catch { Err "Falha com token: $($_.Exception.Message)" }
