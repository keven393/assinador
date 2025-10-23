# Script para fazer deploy dos arquivos estáticos para o servidor Debian via SCP
# Certifique-se de ter configurado SSH no arquivo ~/.ssh/config

param(
    [string]$servidor = "assinador",  # Nome do host no ~/.ssh/config
    [string]$usuario = "suporte",
    [string]$caminho = "/home/assinador/app/assinador"
)

Write-Host "=== Deploy de Arquivos Estáticos ===" -ForegroundColor Cyan
Write-Host ""

# Baixar arquivos estáticos primeiro
Write-Host "Baixando arquivos estáticos..." -ForegroundColor Yellow
& ".\scripts\download_static.ps1" -Force
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha ao baixar arquivos estáticos" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verificar se scp está disponível
if (!(Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: scp não encontrado. Instale OpenSSH Client no Windows." -ForegroundColor Red
    exit 1
}

# Criar arquivo temporário com os arquivos a enviar
$tempDir = "$env:TEMP\assinador_deploy"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Copiando arquivos para diretório temporário..." -ForegroundColor Yellow

# Copiar estrutura de diretórios
Copy-Item -Path "static" -Destination "$tempDir\static" -Recurse -Force
Copy-Item -Path "templates" -Destination "$tempDir\templates" -Recurse -Force
Copy-Item -Path "app.py" -Destination "$tempDir\app.py" -Force
Copy-Item -Path "audit_logger.py" -Destination "$tempDir\audit_logger.py" -Force

Write-Host "✓ Arquivos copiados" -ForegroundColor Green
Write-Host ""

# Fazer upload via SCP
Write-Host "Enviando arquivos para $usuario@$servidor..." -ForegroundColor Yellow

try {
    # Upload dos arquivos estáticos
    scp -r "$tempDir\static" "${usuario}@${servidor}:${caminho}/"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Arquivos static/ enviados" -ForegroundColor Green
    }
    
    # Upload dos templates
    scp -r "$tempDir\templates" "${usuario}@${servidor}:${caminho}/"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Arquivos templates/ enviados" -ForegroundColor Green
    }
    
    # Upload do app.py
    scp "$tempDir\app.py" "${usuario}@${servidor}:${caminho}/"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Arquivo app.py enviado" -ForegroundColor Green
    }
    
    # Upload do audit_logger.py
    scp "$tempDir\audit_logger.py" "${usuario}@${servidor}:${caminho}/"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Arquivo audit_logger.py enviado" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "=== Reiniciando containers ===" -ForegroundColor Cyan
    
    # Rebuild e restart dos containers
    ssh "${usuario}@${servidor}" "cd ${caminho} && docker-compose down && docker-compose build --no-cache && docker-compose up -d"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Containers reiniciados" -ForegroundColor Green
        Write-Host ""
        Write-Host "Deploy concluído com sucesso!" -ForegroundColor Green
        Write-Host "Acesse: https://assinador.senadorcanedo.go.gov.br" -ForegroundColor Cyan
    } else {
        Write-Host "✗ Erro ao reiniciar containers" -ForegroundColor Red
    }
    
} catch {
    Write-Host "✗ Erro durante deploy: $_" -ForegroundColor Red
} finally {
    # Limpar diretório temporário
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
}

