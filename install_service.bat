@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo ========================================
echo   REGISTRAR SERVICO - ASSINADOR PDF
echo ========================================
echo.

rem ==== VERIFICACAO DE ADMINISTRADOR ====
net session >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERRO] Execute como ADMINISTRADOR!
    pause
    exit /b 1
)

rem ==== CONFIGURACOES DO SERVICO ====
set "SERVICE_NAME=AssinadorPDF"
set "SERVICE_DISPLAY=Assinador de PDF - ASGI"
set "SERVICE_DESC=Sistema de assinatura digital de PDFs"
set "PORT=5001"

rem Diretorio da aplicacao
set "APP_DIR=C:\Nova pasta\assinador-main"

rem Detecta o caminho do UV
for /f "delims=" %%i in ('where uv 2^>nul') do set "UV_PATH=%%i"

if "%UV_PATH%"=="" (
    echo [ERRO] UV nao encontrado no PATH!
    echo Por favor, instale o UV ou adicione ao PATH
    pause
    exit /b 1
)

echo [INFO] UV encontrado em: %UV_PATH%

rem Caminhos
set "LOG_DIR=%APP_DIR%\logs"
set "NSSM_EXE=C:\nssm-2.24\win64\nssm.exe"

echo [INFO] Diretorio da aplicacao: %APP_DIR%
echo.

rem ==== DOWNLOAD DO NSSM (se necessario) ====
if not exist "%NSSM_EXE%" (
    echo [INFO] Baixando NSSM...
    if not exist "C:\nssm-2.24\win64" mkdir "C:\nssm-2.24\win64"
    powershell -Command "& {
        $url = 'https://nssm.cc/release/nssm-2.24.zip'
        $output = '%APP_DIR%\nssm.zip'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $output
        Expand-Archive -Path $output -DestinationPath '%APP_DIR%\temp_nssm' -Force
        Move-Item '%APP_DIR%\temp_nssm\nssm-2.24\win64\nssm.exe' '%NSSM_EXE%'
        Remove-Item -Recurse -Force '%APP_DIR%\temp_nssm'
        Remove-Item $output
    }"
    echo [OK] NSSM baixado!
)

rem ==== CRIACAO DO DIRETORIO DE LOGS ====
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

rem ==== REMOVE SERVICO EXISTENTE ====
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Removendo servico anterior...
    sc stop "%SERVICE_NAME%" >nul 2>&1
    timeout /t 2 /nobreak >nul
    "%NSSM_EXE%" remove "%SERVICE_NAME%" confirm >nul 2>&1
)

rem ==== REGISTRA O SERVICO ====
echo [INFO] Registrando servico...

rem Registra com UV rodando Uvicorn em producao - USANDO CAMINHO COMPLETO DO UV
"%NSSM_EXE%" install "%SERVICE_NAME%" "%UV_PATH%" run uvicorn asgi:asgi_app --host 0.0.0.0 --port %PORT% --workers 2

rem Configuracoes basicas
"%NSSM_EXE%" set "%SERVICE_NAME%" DisplayName "%SERVICE_DISPLAY%" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" Description "%SERVICE_DESC%" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppDirectory "%APP_DIR%" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" Start SERVICE_AUTO_START >nul

rem Logs
"%NSSM_EXE%" set "%SERVICE_NAME%" AppStdout "%LOG_DIR%\service.log" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppStderr "%LOG_DIR%\error.log" >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppRotateFiles 1 >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppRotateBytes 10485760 >nul

rem Auto-restart
"%NSSM_EXE%" set "%SERVICE_NAME%" AppExit Default Restart >nul
"%NSSM_EXE%" set "%SERVICE_NAME%" AppRestartDelay 5000 >nul

rem Variaveis de ambiente
"%NSSM_EXE%" set "%SERVICE_NAME%" AppEnvironmentExtra "PYTHONUNBUFFERED=1" >nul

rem Recuperacao em caso de falha
sc failure "%SERVICE_NAME%" reset= 86400 actions= restart/5000/restart/10000/restart/30000 >nul

echo [OK] Servico registrado!

rem ==== FIREWALL ====
echo [INFO] Configurando firewall...
netsh advfirewall firewall delete rule name="AssinadorPDF-5001" >nul 2>&1
netsh advfirewall firewall add rule name="AssinadorPDF-5001" dir=in action=allow protocol=TCP localport=%PORT% >nul
echo [OK] Firewall configurado!

rem ==== INICIA O SERVICO ====
echo [INFO] Iniciando servico...
sc start "%SERVICE_NAME%" >nul

timeout /t 5 /nobreak >nul

sc query "%SERVICE_NAME%" | find "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    color 0A
    echo.
    echo ========================================
    echo         SERVICO REGISTRADO!
    echo ========================================
    echo.
    echo Servico: %SERVICE_NAME%
    echo Status: RODANDO
    echo URL: http://localhost:%PORT%
    echo Logs: %LOG_DIR%
    echo.
) else (
    color 0E
    echo.
    echo [AVISO] Servico registrado mas nao iniciou.
    echo Verifique os logs em: %LOG_DIR%\error.log
    echo.
    echo Conteudo do log de erro:
    echo ------------------------
    if exist "%LOG_DIR%\error.log" (
        type "%LOG_DIR%\error.log"
    ) else (
        echo Arquivo de log ainda nao criado.
    )
)

pause