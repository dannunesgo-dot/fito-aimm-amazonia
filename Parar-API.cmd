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
  pause
  exit /b 1
)

where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PS_EXE=pwsh"
) else (
  set "PS_EXE=powershell"
)

echo [Parar-API] Executando com %PS_EXE%...
%PS_EXE% -NoProfile -ExecutionPolicy Bypass -File ".\deactivate-api.ps1"
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
