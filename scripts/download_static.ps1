# Script para baixar arquivos estáticos (Bootstrap + Font Awesome) do CDN
# Executar antes do build ou deploy

param(
    [switch]$Force,
    [string]$Version = "5.3.0"
)

# Diretórios
$cssDir = "static/css"
$jsDir = "static/js"

# Criar diretórios se não existirem
New-Item -ItemType Directory -Force -Path $cssDir | Out-Null
New-Item -ItemType Directory -Force -Path $jsDir | Out-Null

Write-Host "=== Download de Arquivos Estáticos ===" -ForegroundColor Cyan
Write-Host "Bootstrap versão: $Version" -ForegroundColor White
Write-Host ""

# Baixar Bootstrap CSS
$bootstrapCss = "$cssDir/bootstrap.min.css"
if (-not (Test-Path $bootstrapCss) -or $Force) {
    Write-Host "↓ Baixando Bootstrap CSS..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/css/bootstrap.min.css" -OutFile $bootstrapCss -UseBasicParsing
    $size = (Get-Item $bootstrapCss).Length
    $sizeKB = [math]::Round($size / 1KB, 1)
    Write-Host "✓ Bootstrap CSS - $sizeKB KB" -ForegroundColor Green
} else {
    Write-Host "⊘ Bootstrap CSS - Já existe" -ForegroundColor DarkGray
}

# Baixar Bootstrap JS
$bootstrapJs = "$jsDir/bootstrap.bundle.min.js"
if (-not (Test-Path $bootstrapJs) -or $Force) {
    Write-Host "↓ Baixando Bootstrap JS..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/js/bootstrap.bundle.min.js" -OutFile $bootstrapJs -UseBasicParsing
    $size = (Get-Item $bootstrapJs).Length
    $sizeKB = [math]::Round($size / 1KB, 1)
    Write-Host "✓ Bootstrap JS - $sizeKB KB" -ForegroundColor Green
} else {
    Write-Host "⊘ Bootstrap JS - Já existe" -ForegroundColor DarkGray
}

# Baixar Font Awesome completo
$fontAwesomeCss = "$cssDir/font-awesome.min.css"
if (-not (Test-Path $fontAwesomeCss) -or $Force) {
    Write-Host "↓ Baixando Font Awesome completo..." -ForegroundColor Yellow
    $fontAwesomeZip = "fontawesome.zip"
    $tempDir = "temp_fontawesome"
    
    try {
        # Baixar ZIP
        Invoke-WebRequest -Uri "https://github.com/FortAwesome/Font-Awesome/releases/download/6.4.0/fontawesome-free-6.4.0-web.zip" -OutFile $fontAwesomeZip -UseBasicParsing
        
        # Extrair ZIP
        Expand-Archive -Path $fontAwesomeZip -DestinationPath $tempDir -Force
        
        # Copiar CSS
        Copy-Item "$tempDir/fontawesome-free-6.4.0-web/css/all.min.css" -Destination $fontAwesomeCss -Force
        
        # Copiar webfonts para local correto
        $webfontsDir = "static/webfonts"
        New-Item -ItemType Directory -Force -Path $webfontsDir | Out-Null
        Copy-Item "$tempDir/fontawesome-free-6.4.0-web/webfonts/*" -Destination $webfontsDir -Recurse -Force
        
        # Limpar
        Remove-Item $fontAwesomeZip, $tempDir -Recurse -Force
        
        Write-Host "✓ Font Awesome completo - CSS + Fonts" -ForegroundColor Green
    } catch {
        Write-Host "✗ Erro ao baixar Font Awesome: $_" -ForegroundColor Red
    }
} else {
    Write-Host "⊘ Font Awesome - Já existe" -ForegroundColor DarkGray
}

# Source maps (opcionais)
Write-Host ""
Write-Host "Baixando source maps (opcionais)..." -ForegroundColor Yellow

$bootstrapCssMap = "$cssDir/bootstrap.min.css.map"
if (-not (Test-Path $bootstrapCssMap)) {
    try {
        Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/css/bootstrap.min.css.map" -OutFile $bootstrapCssMap -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "✓ CSS Source Map" -ForegroundColor Green
    } catch {
        Write-Host "⊘ CSS Source Map (ignorado)" -ForegroundColor DarkGray
    }
}

$bootstrapJsMap = "$jsDir/bootstrap.bundle.min.js.map"
if (-not (Test-Path $bootstrapJsMap)) {
    try {
        Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@$Version/dist/js/bootstrap.bundle.min.js.map" -OutFile $bootstrapJsMap -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "✓ JS Source Map" -ForegroundColor Green
    } catch {
        Write-Host "⊘ JS Source Map (ignorado)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== Resumo ===" -ForegroundColor Cyan
Write-Host "✓ Download concluído com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Testar localmente: uv run python app.py" -ForegroundColor White
Write-Host "  2. Fazer deploy: .\deploy_static.ps1" -ForegroundColor White