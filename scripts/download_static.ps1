# Script para baixar arquivos estáticos (Bootstrap) do CDN
# Executar antes do build ou deploy

param(
    [string]$Version = "5.3.0",
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Download de Arquivos Estáticos ===" -ForegroundColor Cyan
Write-Host "Bootstrap versão: $Version" -ForegroundColor Yellow
Write-Host ""

# Definir caminhos
$cssDir = "static/css"
$jsDir = "static/js"

# Criar diretórios se não existirem
New-Item -ItemType Directory -Force -Path $cssDir | Out-Null
New-Item -ItemType Directory -Force -Path $jsDir | Out-Null

# Arquivos essenciais
$files = @(
    @{
        Url = "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/css/bootstrap.min.css"
        Output = "$cssDir/bootstrap.min.css"
        Name = "Bootstrap CSS"
        Essential = $true
    },
    @{
        Url = "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/js/bootstrap.bundle.min.js"
        Output = "$jsDir/bootstrap.bundle.min.js"
        Name = "Bootstrap JS Bundle"
        Essential = $true
    }
)

# Source maps (opcionais)
$optionalFiles = @(
    @{
        Url = "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/css/bootstrap.min.css.map"
        Output = "$cssDir/bootstrap.min.css.map"
        Name = "CSS Source Map"
    },
    @{
        Url = "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/js/bootstrap.bundle.min.js.map"
        Output = "$jsDir/bootstrap.bundle.min.js.map"
        Name = "JS Source Map"
    }
)

# Baixar arquivos
$downloaded = 0
$skipped = 0
$failed = 0

foreach ($file in $files) {
    $exists = Test-Path $file.Output
    
    if ($exists -and -not $Force) {
        Write-Host "⊘ $($file.Name) - Já existe (use -Force para sobrescrever)" -ForegroundColor DarkGray
        $skipped++
        continue
    }
    
    try {
        Write-Host "↓ Baixando $($file.Name)..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $file.Url -OutFile $file.Output -UseBasicParsing
        
        $size = (Get-Item $file.Output).Length
        $sizeKB = [math]::Round($size / 1KB, 2)
        
        Write-Host "✓ $($file.Name) - $sizeKB KB" -ForegroundColor Green
        $downloaded++
    }
    catch {
        Write-Host "✗ Erro ao baixar $($file.Name): $_" -ForegroundColor Red
        $failed++
    }
}

# Baixar source maps (opcionais - não falhar se der erro)
Write-Host ""
Write-Host "Baixando source maps (opcionais)..." -ForegroundColor Yellow
foreach ($file in $optionalFiles) {
    try {
        if (Test-Path $file.Output) {
            Write-Host "⊘ $($file.Name) - Já existe" -ForegroundColor DarkGray
        } else {
            Invoke-WebRequest -Uri $file.Url -OutFile $file.Output -UseBasicParsing -ErrorAction SilentlyContinue
            if (Test-Path $file.Output) {
                Write-Host "✓ $($file.Name)" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "⊘ $($file.Name) - Ignorado" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== Resumo ===" -ForegroundColor Cyan
Write-Host "Baixados: $downloaded" -ForegroundColor Green
Write-Host "Ignorados: $skipped" -ForegroundColor DarkGray
Write-Host "Falhas: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Verificar arquivos essenciais
$missingEssential = @()
foreach ($file in $files) {
    if (!(Test-Path $file.Output) -or (Get-Item $file.Output).Length -eq 0) {
        $missingEssential += $file.Name
    }
}

if ($missingEssential.Count -gt 0) {
    Write-Host "✗ ERRO: Arquivos essenciais ausentes:" -ForegroundColor Red
    foreach ($missing in $missingEssential) {
        Write-Host "  - $missing" -ForegroundColor Red
    }
    exit 1
}

if ($failed -gt 0) {
    Write-Host "⚠ Alguns arquivos opcionais falharam, mas arquivos essenciais OK." -ForegroundColor Yellow
}

if ($downloaded -eq 0 -and $skipped -gt 0) {
    Write-Host "✓ Todos os arquivos já estão atualizados!" -ForegroundColor Green
}
elseif ($downloaded -gt 0) {
    Write-Host "✓ Download concluído com sucesso!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Testar localmente: uv run python app.py" -ForegroundColor White
Write-Host "  2. Fazer deploy: .\deploy_static.ps1" -ForegroundColor White

