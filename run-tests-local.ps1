param(
    [string]$EnvFile = ".\.env",
    [string]$TestScript = ".\scripts\test_api_integration.ps1"
)

$ErrorActionPreference = "Stop"

function Set-DotEnvVars {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-Warning ".env não encontrado em: $Path"
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }

        $parts = $line.Split("=", 2)
        if ($parts.Length -ne 2) { return }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")

        Set-Item -Path "Env:$key" -Value $value
    }
}

Write-Host "==> [tests] Carregando variáveis de ambiente..." -ForegroundColor Cyan
Set-DotEnvVars -Path $EnvFile

$token = $env:AUTH_TOKEN
$hasToken = -not [string]::IsNullOrWhiteSpace($token)

Write-Host ("==> [tests] AUTH_TOKEN carregado: " + ($(if ($hasToken) { "SIM" } else { "NÃO" })))

if (-not (Test-Path $TestScript)) {
    throw "Script de teste não encontrado: $TestScript"
}

if ($hasToken) {
    Write-Host "==> [tests] Executando testes com token (sem exibir valor)..." -ForegroundColor Green
    & $TestScript -Token $token
} else {
    Write-Host "==> [tests] Executando testes sem token (somente cenários públicos/401)..." -ForegroundColor Yellow
    & $TestScript
}