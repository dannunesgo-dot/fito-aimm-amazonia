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
  pause
  exit /b 1
)

where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PS_EXE=pwsh"
) else (
  set "PS_EXE=powershell"
)

echo [Iniciar-API] Executando com %PS_EXE%...
%PS_EXE% -NoProfile -ExecutionPolicy Bypass -File ".\activate-api.ps1"
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
