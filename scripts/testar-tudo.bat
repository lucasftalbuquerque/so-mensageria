@echo off
REM Duplo clique: roda os 3 cenarios e salva em evidencias\teste-automatico\
cd /d "%~dp0.."
where python >/dev/null 2>nul
if %errorlevel%==0 (
  python scripts\teste_automatico.py
) else (
  py scripts\teste_automatico.py
)
echo.
echo Codigo de saida: %errorlevel%
pause
