@echo off
REM ============================================
REM Script para Remover Serviço (Windows)
REM ============================================

echo ============================================
echo   Removendo Servico - Assinador de PDFs
echo ============================================

REM Verifica se está rodando como Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERRO: Este script precisa ser executado como Administrador
    echo Clique com botao direito e selecione "Executar como administrador"
    pause
    exit /b 1
)

REM Define o nome do serviço
set SERVICE_NAME=AssinadorPDF

echo.
echo Parando servico...
nssm stop %SERVICE_NAME%

echo.
echo Removendo servico...
nssm remove %SERVICE_NAME% confirm

if %errorLevel% equ 0 (
    echo.
    echo Servico removido com sucesso!
) else (
    echo.
    echo ERRO: Falha ao remover servico
    echo O servico pode nao existir ou ja ter sido removido.
)

echo.
echo ============================================
pause

