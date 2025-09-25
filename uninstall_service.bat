@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo ========================================
echo   REMOVER SERVIÇO - ASSINADOR PDF
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

rem ==== CONFIGURAÇÕES ====
set "SERVICE_NAME=AssinadorPDF"
set "NSSM_EXE=nssm.exe"

rem ==== VERIFICA SE SERVIÇO EXISTE ====
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo [AVISO] Serviço '%SERVICE_NAME%' não encontrado!
    echo.
    echo O serviço pode já ter sido removido ou nunca foi instalado.
    pause
    exit /b 0
)

rem ==== PARA O SERVIÇO ====
echo [INFO] Parando serviço...
sc stop "%SERVICE_NAME%" >nul 2>&1
timeout /t 3 /nobreak >nul

rem ==== REMOVE O SERVIÇO ====
echo [INFO] Removendo serviço...

rem Verifica se NSSM está disponível
where "%NSSM_EXE%" >nul 2>&1
if %errorlevel% equ 0 (
    "%NSSM_EXE%" remove "%SERVICE_NAME%" confirm >nul 2>&1
    echo [OK] Serviço removido via NSSM
) else (
    sc delete "%SERVICE_NAME%" >nul 2>&1
    echo [OK] Serviço removido via SC
)

rem ==== REMOVE REGRA DO FIREWALL ====
echo [INFO] Removendo regra do firewall...
netsh advfirewall firewall delete rule name="AssinadorPDF-5001" >nul 2>&1
echo [OK] Regra do firewall removida

rem ==== VERIFICA REMOÇÃO ====
timeout /t 2 /nobreak >nul
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    color 0A
    echo.
    echo ========================================
    echo         SERVIÇO REMOVIDO!
    echo ========================================
    echo.
    echo ✅ Serviço '%SERVICE_NAME%' removido com sucesso!
    echo ✅ Firewall limpo
    echo.
    echo 📁 Arquivos mantidos:
    echo    - Logs: %~dp0logs\
    echo    - Banco: %~dp0instance\
    echo    - PDFs: %~dp0pdf_assinados\
    echo.
) else (
    color 0C
    echo.
    echo ========================================
    echo         ERRO NA REMOÇÃO!
    echo ========================================
    echo.
    echo ❌ Falha ao remover o serviço.
    echo.
    echo 💡 Tente executar manualmente:
    echo    sc delete %SERVICE_NAME%
    echo.
)

echo.
echo Pressione qualquer tecla para continuar...
pause >nul