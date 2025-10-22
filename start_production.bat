@echo off
REM ============================================
REM Script de Inicialização para Produção (Windows)
REM Cria serviço Windows automaticamente
REM ============================================

echo ============================================
echo   Assinador de PDFs - Configuracao de Servico
echo ============================================

REM Verifica se está rodando como Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERRO: Este script precisa ser executado como Administrador
    echo Clique com botao direito e selecione "Executar como administrador"
    pause
    exit /b 1
)

REM Verifica se o arquivo .env existe
if not exist .env (
    echo ERRO: Arquivo .env nao encontrado!
    echo Por favor, copie o arquivo env_example.txt para .env e configure as variaveis.
    pause
    exit /b 1
)

REM Obtém o caminho completo do diretório
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM Verifica se o ambiente virtual existe
if not exist "venv" (
    echo ERRO: Ambiente virtual nao encontrado em %PROJECT_DIR%\venv
    echo Por favor, crie o ambiente virtual primeiro:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Cria diretórios necessários
echo Criando diretorios necessarios...
if not exist temp_files mkdir temp_files
if not exist pdf_assinados mkdir pdf_assinados
if not exist signatures mkdir signatures
if not exist certificates mkdir certificates
if not exist keys mkdir keys
if not exist logs mkdir logs
if not exist static\images mkdir static\images

REM Verifica se o banco de dados existe
if not exist "instance\assinador.db" (
    echo Inicializando banco de dados...
    venv\Scripts\python.exe init_db.py
)

REM Verifica se o certificado existe
if not exist "certificates\certificate.pem" (
    echo Gerando certificado...
    venv\Scripts\python.exe -c "from certificate_manager import certificate_manager; certificate_manager.generate_certificate()"
)

REM Define o nome do serviço
set SERVICE_NAME=AssinadorPDF
set SERVICE_DISPLAY_NAME=Assinador de PDFs
set SERVICE_DESCRIPTION=Sistema de Assinatura Digital de Documentos PDF

echo.
echo Verificando se NSSM esta instalado...

REM Verifica se NSSM está instalado
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo NSSM nao encontrado no PATH.
    echo.
    echo Por favor, instale o NSSM:
    echo 1. Baixe de: https://nssm.cc/download
    echo 2. Extraia o arquivo
    echo 3. Adicione a pasta ao PATH do sistema
    echo    OU copie nssm.exe para C:\Windows\System32\
    echo.
    pause
    exit /b 1
)

echo NSSM encontrado!
echo.

REM Aplicar migrations do Alembic
echo.
echo Aplicando migrations do Alembic...
"%PROJECT_DIR%\venv\Scripts\alembic.exe" upgrade head
if %errorLevel% neq 0 (
    echo ERRO: Falha ao aplicar migrations do Alembic
    pause
    exit /b 1
)

REM Verifica se o serviço já existe
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo Servico ja existe. Removendo...
    nssm stop %SERVICE_NAME%
    nssm remove %SERVICE_NAME% confirm
    timeout /t 2 /nobreak >nul
)

echo Criando servico Windows...

REM Cria o serviço com NSSM
nssm install %SERVICE_NAME% "%PROJECT_DIR%\venv\Scripts\python.exe"
if %errorLevel% neq 0 (
    echo ERRO: Falha ao criar servico
    pause
    exit /b 1
)

REM Configura o serviço
nssm set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
nssm set %SERVICE_NAME% DisplayName "%SERVICE_DISPLAY_NAME%"
nssm set %SERVICE_NAME% Description "%SERVICE_DESCRIPTION%"
nssm set %SERVICE_NAME% AppParameters "-m gunicorn --bind 0.0.0.0:5001 --workers 4 --worker-class sync --timeout 120 --access-logfile %PROJECT_DIR%\logs\access.log --error-logfile %PROJECT_DIR%\logs\error.log --log-level info --capture-output app:app"
nssm set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\service.log"
nssm set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\service_error.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateOnline 1
nssm set %SERVICE_NAME% AppRotateSeconds 86400
nssm set %SERVICE_NAME% AppRotateBytes 10485760

REM Configura para iniciar automaticamente
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Configura para reiniciar em caso de falha
nssm set %SERVICE_NAME% AppThrottle 1500
nssm set %SERVICE_NAME% AppRestartDelay 10000

REM Configura o usuário (opcional - comentado por padrão)
REM nssm set %SERVICE_NAME% ObjectName LocalSystem

echo.
echo Iniciando servico...
nssm start %SERVICE_NAME%

REM Aguarda um momento para o serviço iniciar
timeout /t 3 /nobreak >nul

REM Verifica o status do serviço
echo.
echo Status do servico:
sc query %SERVICE_NAME%

echo.
echo ============================================
echo   Servico Configurado com Sucesso!
echo ============================================
echo.
echo Comandos uteis:
echo   Status:     sc query %SERVICE_NAME%
echo   Parar:      nssm stop %SERVICE_NAME%
echo   Iniciar:    nssm start %SERVICE_NAME%
echo   Reiniciar:  nssm restart %SERVICE_NAME%
echo   Remover:    nssm remove %SERVICE_NAME% confirm
echo.
echo Logs:
echo   Ver logs:   type %PROJECT_DIR%\logs\service.log
echo   Logs de erro: type %PROJECT_DIR%\logs\service_error.log
echo.
echo Acesso:
echo   URL: http://localhost:5001
echo.
echo ============================================
pause
