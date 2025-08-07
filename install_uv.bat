@echo off
echo ========================================
echo    Assinador Rápido de PDFs - UV
echo ========================================
echo.
echo Instalando dependencias com UV...
echo.

REM Verifica se uv está instalado
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: UV nao encontrado!
    echo Por favor, instale o UV primeiro.
    echo Visite: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo UV encontrado. Instalando dependencias...
uv add flask PyPDF2 reportlab pillow

if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Instalacao concluida com sucesso!
echo ========================================
echo.
echo Para executar a aplicacao, use:
echo   uv run python app.py
echo.
echo A aplicacao sera aberta em:
echo   http://localhost:5000
echo.
pause 