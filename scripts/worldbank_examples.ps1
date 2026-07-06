param(
    [string]$GatewayUrl = "http://127.0.0.1:8080",
    [string]$ApiBase = "https://api.worldbank.org/v2"
)

$ErrorActionPreference = "Stop"

function Write-Title($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "⚠️ $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "❌ $msg" -ForegroundColor Red }

function Load-DotEnv {
    param([string]$Path = ".\.env")
    if (-not (Test-Path $Path)) {
        Write-Warn ".env não encontrado em $Path (seguindo sem carregar variáveis)."
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

function Ask-NonEmpty {
    param([string]$Prompt, [string]$Default = "")
    while ($true) {
        $v = Read-Host "$Prompt$(if ($Default) { " [$Default]" })"
        if ([string]::IsNullOrWhiteSpace($v)) { $v = $Default }
        if (-not [string]::IsNullOrWhiteSpace($v)) { return $v.Trim() }
        Write-Warn "Valor obrigatório."
    }
}

function Ask-Format {
    while ($true) {
        $f = (Read-Host "Formato (json/xml/csv) [json]").Trim().ToLower()
        if ([string]::IsNullOrWhiteSpace($f)) { $f = "json" }
        if ($f -in @("json","xml","csv")) { return $f }
        Write-Warn "Formato inválido. Use json, xml ou csv."
    }
}

function Ask-YesNo {
    param([string]$Prompt, [bool]$Default = $true)
    $hint = if ($Default) { "[Y/n]" } else { "[y/N]" }
    $ans = (Read-Host "$Prompt $hint").Trim().ToLower()
    if ([string]::IsNullOrWhiteSpace($ans)) { return $Default }
    return $ans -in @("y","yes","s","sim")
}

function Build-QueryString {
    param([hashtable]$Params)

    $pairs = @()
    foreach ($k in $Params.Keys) {
        $v = $Params[$k]
        if (-not [string]::IsNullOrWhiteSpace([string]$v)) {
            $pairs += ("{0}={1}" -f [uri]::EscapeDataString($k), [uri]::EscapeDataString([string]$v))
        }
    }
    return ($pairs -join "&")
}

function Invoke-WorldBankRequest {
    param(
        [string]$Url,
        [string]$Format,
        [string]$OutFile = ""
    )

    Write-Host "`nURL:"
    Write-Host $Url -ForegroundColor Gray

    try {
        if ($Format -eq "csv") {
            if ([string]::IsNullOrWhiteSpace($OutFile)) {
                $ts = Get-Date -Format "yyyyMMdd_HHmmss"
                $OutFile = ".\outputs\worldbank_$ts.zip"
            }
            $dir = Split-Path -Parent $OutFile
            if ($dir -and -not (Test-Path $dir)) {
                New-Item -ItemType Directory -Force -Path $dir | Out-Null
            }
            Invoke-WebRequest -Uri $Url -OutFile $OutFile -TimeoutSec 60
            Write-Ok "Download concluído: $OutFile"
        } else {
            $resp = Invoke-WebRequest -Uri $Url -TimeoutSec 60
            Write-Ok "HTTP $($resp.StatusCode)"
            Write-Host ""
            $resp.Content
        }
    } catch {
        Write-Err $_.Exception.Message
    }
}

function Ensure-AuthHeader {
    Load-DotEnv
    if ([string]::IsNullOrWhiteSpace($env:AUTH_TOKEN)) {
        Write-Warn "AUTH_TOKEN não encontrado na sessão/.env."
        if (Ask-YesNo "Deseja informar token agora?" $false) {
            $env:AUTH_TOKEN = Ask-NonEmpty "Informe AUTH_TOKEN"
        } else {
            return $null
        }
    }
    return @{ Authorization = "Bearer $env:AUTH_TOKEN" }
}

function Menu {
    Write-Title "World Bank Examples"
    Write-Host "1) Indicadores (API pública World Bank)"
    Write-Host "2) Países (API pública World Bank)"
    Write-Host "3) Série por país+indicador (API pública World Bank)"
    Write-Host "4) Endpoint privado via Gateway (/api/worldbank/data/{pais}/{indicador})"
    Write-Host "5) Endpoint privado via Gateway (/api/worldbank/indicators?search=...)"
    Write-Host "0) Sair"
    return (Read-Host "Escolha uma opção").Trim()
}

do {
    $op = Menu

    switch ($op) {
        "1" {
            $format = Ask-Format
            $perPage = Ask-NonEmpty "per_page" "50"
            $page    = Ask-NonEmpty "page" "1"
            $source  = Read-Host "source (opcional, ex: 2 para WDI)"
            $search  = Read-Host "search (opcional, filtro textual no seu app; API pública pode ignorar)"

            $params = @{
                format   = $format
                per_page = $perPage
                page     = $page
                source   = $source
            }

            $qs = Build-QueryString $params
            $url = "$ApiBase/indicator?$qs"
            if (-not [string]::IsNullOrWhiteSpace($search)) {
                Write-Warn "Obs: search textual é mais confiável no seu backend; API pública pode não filtrar por texto livre."
            }

            $out = ""
            if ($format -eq "csv") {
                $out = Ask-NonEmpty "Arquivo de saída (.zip)" ".\outputs\indicators.zip"
            }

            Invoke-WorldBankRequest -Url $url -Format $format -OutFile $out
        }

        "2" {
            $format = Ask-Format
            $perPage = Ask-NonEmpty "per_page" "300"
            $page    = Ask-NonEmpty "page" "1"

            $params = @{
                format   = $format
                per_page = $perPage
                page     = $page
            }

            $qs = Build-QueryString $params
            $url = "$ApiBase/country?$qs"

            $out = ""
            if ($format -eq "csv") {
                $out = Ask-NonEmpty "Arquivo de saída (.zip)" ".\outputs\countries.zip"
            }

            Invoke-WorldBankRequest -Url $url -Format $format -OutFile $out
        }

        "3" {
            $country   = Ask-NonEmpty "Código do país (ex: BR)" "BR"
            $indicator = Ask-NonEmpty "Código do indicador (ex: NY.GDP.MKTP.CD)" "NY.GDP.MKTP.CD"
            $format    = Ask-Format
            $dateRange = Read-Host "Intervalo de datas (opcional, ex: 2010:2023)"
            $mrv       = Read-Host "mrv (opcional, ex: 5)"
            $perPage   = Ask-NonEmpty "per_page" "200"
            $source    = Read-Host "source (opcional, ex: 2 para WDI)"

            $params = @{
                format   = $format
                date     = $dateRange
                mrv      = $mrv
                per_page = $perPage
                source   = $source
            }

            $qs = Build-QueryString $params
            $url = "$ApiBase/country/$country/indicator/$indicator?$qs"

            $out = ""
            if ($format -eq "csv") {
                $default = ".\outputs\${country}_${indicator}.zip"
                $out = Ask-NonEmpty "Arquivo de saída (.zip)" $default
            }

            Invoke-WorldBankRequest -Url $url -Format $format -OutFile $out
        }

        "4" {
            $headers = Ensure-AuthHeader
            if ($null -eq $headers) {
                Write-Warn "Sem token. Operação cancelada."
                break
            }

            $country   = Ask-NonEmpty "Código do país (ex: BR)" "BR"
            $indicator = Ask-NonEmpty "Código do indicador (ex: NY.GDP.MKTP.CD)" "NY.GDP.MKTP.CD"
            $url = "$GatewayUrl/api/worldbank/data/$country/$indicator"

            Write-Host "`nURL:"
            Write-Host $url -ForegroundColor Gray

            try {
                $resp = Invoke-WebRequest -Uri $url -Headers $headers -TimeoutSec 60 -SkipHttpErrorCheck
                Write-Ok "HTTP $($resp.StatusCode)"
                Write-Host ""
                $resp.Content
            } catch {
                Write-Err $_.Exception.Message
            }
        }

        "5" {
            $headers = Ensure-AuthHeader
            if ($null -eq $headers) {
                Write-Warn "Sem token. Operação cancelada."
                break
            }

            $search = Ask-NonEmpty "Texto de busca (ex: gdp)" "gdp"
            $url = "$GatewayUrl/api/worldbank/indicators?search=$([uri]::EscapeDataString($search))"

            Write-Host "`nURL:"
            Write-Host $url -ForegroundColor Gray

            try {
                $resp = Invoke-WebRequest -Uri $url -Headers $headers -TimeoutSec 60 -SkipHttpErrorCheck
                Write-Ok "HTTP $($resp.StatusCode)"
                Write-Host ""
                $resp.Content
            } catch {
                Write-Err $_.Exception.Message
            }
        }

        "0" { Write-Host "Saindo..." }
        default { Write-Warn "Opção inválida." }
    }

    if ($op -ne "0") {
        [void](Read-Host "`nPressione Enter para voltar ao menu")
        Clear-Host
    }

} while ($op -ne "0")