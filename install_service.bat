@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo ========================================
echo   INSTALAR SERVIÇO - ASSINADOR PDF
echo ========================================
echo.

rem ==== VERIFICAÇÃO DE ADMINISTRADOR ====
net session >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERRO] Execute como ADMINISTRADOR!
    echo Clique com botão direito no arquivo e selecione "Executar como administrador"
    pause
    exit /b 1
)

rem ==== CONFIGURAÇÕES DO SERVIÇO ====
set "SERVICE_NAME=AssinadorPDF"
set "SERVICE_DISPLAY=Assinador de PDFs"
set "SERVICE_DESC=Sistema de Assinatura Digital de PDFs - Producao"
set "PORT=5001"

rem Diretório da aplicação (AJUSTE CONFORME SUA ESTRUTURA)
set "APP_DIR=%~dp0"
echo [INFO] Diretório da aplicação: %APP_DIR%

rem ==== DETECTA UV ====
for /f "delims=" %%i in ('where uv 2^>nul') do set "UV_PATH=%%i"
if "%UV_PATH%"=="" (
    echo [ERRO] UV não encontrado no PATH!
    echo.
    echo Para instalar o UV:
    echo 1. Acesse: https://github.com/astral-sh/uv
    echo 2. Baixe e instale o UV
    echo 3. Adicione ao PATH do sistema
    echo.
    pause
    exit /b 1
)
echo [OK] UV encontrado: %UV_PATH%

rem ==== PREPARA LOGS ====
set "LOG_DIR=%APP_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [OK] Diretório de logs: %LOG_DIR%

rem ==== DOWNLOAD DO NSSM ====
set "NSSM_DIR=%APP_DIR%nssm"
set "NSSM_EXE=%NSSM_DIR%\nssm.exe"

if not exist "%NSSM_EXE%" (
    echo [INFO] Baixando NSSM...
    if not exist "%NSSM_DIR%" mkdir "%NSSM_DIR%"
    
    powershell -Command "& {
        $url = 'https://nssm.cc/release/nssm-2.24.zip'
        $output = '%APP_DIR%nssm.zip'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        try {
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Expand-Archive -Path $output -DestinationPath '%APP_DIR%temp_nssm' -Force
            Copy-Item '%APP_DIR%temp_nssm\nssm-2.24\win64\nssm.exe' '%NSSM_EXE%'
            Remove-Item -Recurse -Force '%APP_DIR%temp_nssm'
            Remove-Item $output
            Write-Host '[OK] NSSM baixado com sucesso!'
        } catch {
            Write-Host '[ERRO] Falha ao baixar NSSM: ' $_.Exception.Message
            exit 1
        }
    }"
    
    if not exist "%NSSM_EXE%" (
        echo [ERRO] Falha ao baixar NSSM!
        echo Baixe manualmente de: https://nssm.cc/download
        pause
        exit /b 1
    )
) else (
    echo [OK] NSSM já disponível
)

rem ==== VERIFICA DEPENDÊNCIAS ====
echo [INFO] Verificando dependências...
python -c "import flask, flask_caching, flask_compress" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependências...
    "%UV_PATH%" pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependências!
        pause
        exit /b 1
    )
    echo [OK] Dependências instaladas
) else (
    echo [OK] Dependências já instaladas
)

rem ==== INICIALIZA BANCO DE DADOS ====
echo [INFO] Inicializando banco de dados...
python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('✅ Banco de dados inicializado')
" 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao inicializar banco de dados
    echo O banco será criado automaticamente na primeira execução
)

rem ==== REMOVE SERVIÇO EXISTENTE ====
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Removendo serviço anterior...
    sc stop "%SERVICE_NAME%" >nul 2>&1
    timeout /t 3 /nobreak >nul
    "%NSSM_EXE%" remove "%SERVICE_NAME%" confirm >nul 2>&1
    echo [OK] Serviço anterior removido
)

rem ==== REGISTRA O SERVIÇO ====
echo [INFO] Registrando serviço...

rem Comando: uv run uvicorn asgi:asgi_app --host 0.0.0.0 --port 5001 --workers 2
"%NSSM_EXE%" install "%SERVICE_NAME%" "%UV_PATH%" run uvicorn asgi:asgi_app --host 0.0.0.0 --port %PORT% --workers 2

rem ==== CONFIGURAÇÕES DO SERVIÇO ====
echo [INFO] Configurando serviço...

rem Informações básicas
"%NSSM_EXE%" set "%SERVICE_NAME%" DisplayName "%SERVICE_DISPLAY%" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" Description "%SERVICE_DESC%" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppDirectory "%APP_DIR%" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" Start SERVICE_AUTO_START >nul

rem Logs com rotação
"%NSSM_EXE%" set "%SERVICE_NAME%" AppStdout "%LOG_DIR%\service.log" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppStderr "%LOG_DIR%\error.log" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppRotateFiles 1 >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppRotateBytes 10485760 >nul

rem Auto-restart e kill tree
"%NSSM_EXE%" set "%SERVICE_NAME%" AppExit Default Restart >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppRestartDelay 5000 >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppKillProcessTree 1 >nul

rem Variáveis de ambiente de produção
"%NSSM_EXE%" set "%SERVICE_NAME%" AppEnvironmentExtra "PYTHONUNBUFFERED=1" "FLASK_CONFIG=production" "PORT=%PORT%" >nul

rem Recuperação do Windows
sc failure "%SERVICE_NAME%" reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul

echo [OK] Serviço registrado com sucesso!

rem ==== CONFIGURA FIREWALL ====
echo [INFO] Configurando firewall...
netsh advfirewall firewall delete rule name="AssinadorPDF-%PORT%" >nul 2>&1
netsh advfirewall firewall add rule name="AssinadorPDF-%PORT%" dir=in action=allow protocol=TCP localport=%PORT% >nul
echo [OK] Firewall configurado!

rem ==== INICIA O SERVIÇO ====
echo [INFO] Iniciando serviço...
sc start "%SERVICE_NAME%" >nul

timeout /t 5 /nobreak >nul

rem ==== VERIFICA STATUS ====
sc query "%SERVICE_NAME%" | find "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    color 0A
    echo.
    echo ========================================
    echo         SERVIÇO INSTALADO!
    echo ========================================
    echo.
    echo ✅ Serviço: %SERVICE_NAME%
    echo ✅ Status : RODANDO
    echo ✅ URL    : http://localhost:%PORT%
    echo ✅ Logs   : %LOG_DIR%
    echo.
    echo 📋 Comandos úteis:
    echo    - Parar:   sc stop %SERVICE_NAME%
    echo    - Iniciar: sc start %SERVICE_NAME%
    echo    - Status:  sc query %SERVICE_NAME%
    echo    - Remover: sc delete %SERVICE_NAME%
    echo.
) else (
    color 0E
    echo.
    echo ========================================
    echo         ERRO NA INSTALAÇÃO!
    echo ========================================
    echo.
    echo ❌ Serviço registrado mas não iniciou.
    echo.
    echo 🔍 Verifique os logs em: %LOG_DIR%\error.log
    echo.
    if exist "%LOG_DIR%\error.log" (
        echo 📄 Conteúdo do log de erro:
        echo ------------------------
        type "%LOG_DIR%\error.log"
        echo ------------------------
    ) else (
        echo 📄 Arquivo de log ainda não foi criado.
    )
    echo.
    echo 💡 Soluções possíveis:
    echo    1. Verifique se a porta %PORT% está livre
    echo    2. Execute: netstat -an ^| find ":%PORT%"
    echo    3. Verifique as dependências Python
    echo    4. Execute: "%UV_PATH%" pip install -r requirements.txt
    echo.
)

echo.
echo Pressione qualquer tecla para continuar...
pause >nul
