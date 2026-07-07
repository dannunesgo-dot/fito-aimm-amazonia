@echo off
setlocal

set "PROJECT_ROOT=C:\Users\danie\work\github\fito-aimm-amazonia"

echo ============================================================
echo [Iniciar-API] Projeto: %PROJECT_ROOT%
echo ============================================================

if not exist "%PROJECT_ROOT%" (
  echo [ERRO] Pasta do projeto nao encontrada.
  pause
  exit /b 1
)

cd /d "%PROJECT_ROOT%"

if not exist ".\activate-api.ps1" (
  echo [ERRO] Arquivo .\activate-api.ps1 nao encontrado.
  echo Crie o activate-api.ps1 antes de usar este launcher.
  pause
  exit /b 1
)

echo [Iniciar-API] Executando activate-api.ps1...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\activate-api.ps1"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo [ERRO] Falha ao iniciar API. Codigo: %ERR%
  pause
  exit /b %ERR%
)

echo.
echo [OK] API iniciada com sucesso.
pause
exit /b 0