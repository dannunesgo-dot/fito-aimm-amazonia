function Mask-AuthHeader([string]$line) {
  if ([string]::IsNullOrWhiteSpace($line)) { return $line }
  # mascara qualquer "Authorization: Bearer <token>"
  return ($line -replace '(?i)(Authorization:\s*Bearer\s+)[^\s"]+', '$1***REDACTED***')
}

Write-Host "==> [status] Processos" -ForegroundColor Cyan
$caddy = Get-Process caddy -ErrorAction SilentlyContinue
$python = Get-Process python -ErrorAction SilentlyContinue

if ($caddy) { $caddy | ForEach-Object { Write-Host ("Caddy  PID=" + $_.Id) -ForegroundColor Green } }
else { Write-Warning "Caddy não está rodando." }

if ($python) { $python | ForEach-Object { Write-Host ("Python PID=" + $_.Id) -ForegroundColor Green } }
else { Write-Warning "Python não está rodando." }

Write-Host "`n==> [status] Portas" -ForegroundColor Cyan
$ports = netstat -ano | Select-String ":(8000|8080)\s+.*LISTENING"
if ($ports) { $ports | ForEach-Object { Write-Host $_.Line } }
else { Write-Warning "Nenhuma porta 8000/8080 em LISTENING." }

Write-Host "`n==> [status] HTTP checks (sem token real)" -ForegroundColor Cyan
$h = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/health"
$u = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/api/worldbank/countries"
$b = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8080/api/worldbank/countries" -H "Authorization: Bearer local-dev-token"

Write-Host (Mask-AuthHeader "Authorization: Bearer local-dev-token")
Write-Host "/health                         => $h"
Write-Host "/api/worldbank/countries        => $u (esperado 401)"
Write-Host "/api/... com Bearer dummy       => $b (esperado 200 ou 502)"