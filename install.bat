@echo off
echo ========================================
echo    Instalador do Assinador de PDFs
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.9+ primeiro.
    echo Visite: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Instalando dependencias...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias!
    echo Tente executar: pip install --upgrade pip
    pause
    exit /b 1
)

echo.
echo Dependencias instaladas com sucesso!
echo.

echo Inicializando banco de dados...
python init_db.py

if errorlevel 1 (
    echo ERRO: Falha ao inicializar banco de dados!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Instalacao concluida com sucesso!
echo ========================================
echo.
echo Para executar a aplicacao:
echo   python app.py
echo.
echo Acesse: http://localhost:5000
echo.
echo Usuario padrao: admin
echo Senha padrao: admin123
echo.
echo IMPORTANTE: Altere a senha padrao apos o primeiro login!
echo.
pause 