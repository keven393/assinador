@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo ========================================
echo   VERIFICAÇÃO DO SISTEMA - ASSINADOR
echo ========================================
echo.

rem ==== CONFIGURAÇÕES ====
set "SERVICE_NAME=AssinadorPDF"
set "PORT=5001"
set "APP_DIR=%~dp0"

echo [INFO] Verificando sistema...
echo.

rem ==== 1. VERIFICA PYTHON VIA UV ====
echo [1/8] Verificando Python via UV...
uv run python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('uv run python --version') do echo ✅ Python: %%i
) else (
    echo ❌ Python não encontrado via UV!
    echo    UV deve gerenciar o Python automaticamente
    goto :error
)

rem ==== 2. VERIFICA UV ====
echo [2/8] Verificando UV...
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('uv --version') do echo ✅ UV: %%i
) else (
    echo ❌ UV não encontrado!
    echo    Instale UV: pip install uv
    goto :error
)

rem ==== 3. VERIFICA DEPENDÊNCIAS ====
echo [3/8] Verificando dependências...
cd /d "%APP_DIR%"
uv run python -c "import flask, flask_caching, flask_compress" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Dependências Python OK
) else (
    echo ⚠️ Dependências não encontradas
    echo    Execute: uv pip install -r requirements.txt
)

rem ==== 4. VERIFICA ARQUIVOS ESSENCIAIS ====
echo [4/8] Verificando arquivos essenciais...
set "missing_files="
if not exist "%APP_DIR%app.py" set "missing_files=%missing_files% app.py"
if not exist "%APP_DIR%asgi.py" set "missing_files=%missing_files% asgi.py"
if not exist "%APP_DIR%config.py" set "missing_files=%missing_files% config.py"
if not exist "%APP_DIR%requirements.txt" set "missing_files=%missing_files% requirements.txt"
if not exist "%APP_DIR%templates" set "missing_files=%missing_files% templates/"

if "%missing_files%"=="" (
    echo ✅ Arquivos essenciais OK
) else (
    echo ❌ Arquivos faltando:%missing_files%
    goto :error
)

rem ==== 5. VERIFICA SERVIÇO ====
echo [5/8] Verificando serviço...
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    sc query "%SERVICE_NAME%" | find "RUNNING" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Serviço: RODANDO
    ) else (
        echo ⚠️ Serviço: PARADO
        echo    Execute: sc start %SERVICE_NAME%
    )
) else (
    echo ❌ Serviço não instalado
    echo    Execute: install_service.bat
    goto :error
)

rem ==== 6. VERIFICA PORTA ====
echo [6/8] Verificando porta %PORT%...
netstat -an | find ":%PORT%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Porta %PORT%: EM USO
) else (
    echo ⚠️ Porta %PORT%: LIVRE
    echo    Serviço pode não estar rodando
)

rem ==== 7. VERIFICA FIREWALL ====
echo [7/8] Verificando firewall...
netsh advfirewall firewall show rule name="AssinadorPDF-%PORT%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Firewall: CONFIGURADO
) else (
    echo ⚠️ Firewall: NÃO CONFIGURADO
    echo    Execute: netsh advfirewall firewall add rule name="AssinadorPDF-%PORT%" dir=in action=allow protocol=TCP localport=%PORT%
)

rem ==== 8. VERIFICA LOGS ====
echo [8/8] Verificando logs...
if exist "%APP_DIR%logs\service.log" (
    echo ✅ Logs: DISPONÍVEIS
    echo    Localização: %APP_DIR%logs\
) else (
    echo ⚠️ Logs: NÃO ENCONTRADOS
    echo    Serão criados na primeira execução
)

rem ==== 9. TESTE DE CONECTIVIDADE ====
echo.
echo [BONUS] Testando conectividade...
powershell -Command "& {
    try {
        $response = Invoke-WebRequest -Uri 'http://localhost:%PORT%' -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host '✅ Aplicação: ACESSÍVEL'
        } else {
            Write-Host '⚠️ Aplicação: ERRO HTTP' $response.StatusCode
        }
    } catch {
        Write-Host '❌ Aplicação: INACESSÍVEL'
        Write-Host '   Erro:' $_.Exception.Message
    }
}" 2>nul

rem ==== RESUMO ====
echo.
echo ========================================
echo           RESUMO DA VERIFICAÇÃO
echo ========================================
echo.
echo 📊 Status do Sistema:
echo    - Python: ✅
echo    - UV: ✅
echo    - Arquivos: ✅
echo    - Serviço: Verificado
echo    - Porta: Verificada
echo    - Firewall: Verificado
echo    - Logs: Verificados
echo.
echo 🌐 Acesso:
echo    - URL: http://localhost:%PORT%
echo    - Admin: http://localhost:%PORT%/admin
echo.
echo 📁 Logs:
echo    - Localização: %APP_DIR%logs\
echo    - Arquivos: service.log, error.log
echo.
echo 🛠️ Comandos úteis:
echo    - Status: sc query %SERVICE_NAME%
echo    - Parar: sc stop %SERVICE_NAME%
echo    - Iniciar: sc start %SERVICE_NAME%
echo    - Logs: type %APP_DIR%logs\error.log
echo.

goto :end

:error
echo.
echo ========================================
echo           ERRO NA VERIFICAÇÃO
echo ========================================
echo.
echo ❌ Sistema não está pronto para produção!
echo.
echo 💡 Soluções:
echo    1. Instale as dependências faltantes
echo    2. Execute: install_service.bat
echo    3. Verifique os logs de erro
echo.

:end
echo Pressione qualquer tecla para continuar...
pause >nul