@echo off
setlocal

set "PROJECT_ROOT=C:\Users\danie\work\github\fito-aimm-amazonia"

echo ============================================================
echo [Parar-API] Projeto: %PROJECT_ROOT%
echo ============================================================

if not exist "%PROJECT_ROOT%" (
  echo [ERRO] Pasta do projeto nao encontrada.
  pause
  exit /b 1
)

cd /d "%PROJECT_ROOT%"

if not exist ".\deactivate-api.ps1" (
  echo [ERRO] Arquivo .\deactivate-api.ps1 nao encontrado.
  echo Crie o deactivate-api.ps1 antes de usar este launcher.
  pause
  exit /b 1
)

echo [Parar-API] Executando deactivate-api.ps1...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\deactivate-api.ps1"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo [ERRO] Falha ao parar API. Codigo: %ERR%
  pause
  exit /b %ERR%
)

echo.
echo [OK] API parada com sucesso.
pause
exit /b 0