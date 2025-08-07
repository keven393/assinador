@echo off
echo ========================================
echo    Assinador Rápido de PDFs
echo ========================================
echo.
echo Instalando dependencias...
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    echo Visite: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python encontrado. Instalando dependencias...
pip install flask PyPDF2 reportlab pillow

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
echo   python app.py
echo.
echo A aplicacao sera aberta em:
echo   http://localhost:5000
echo.
pause 