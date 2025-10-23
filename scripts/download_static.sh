#!/bin/bash
# Script para baixar arquivos estáticos (Bootstrap) do CDN
# Executar antes do build ou deploy

set -e

VERSION="${1:-5.3.0}"
FORCE=false

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

echo "=== Download de Arquivos Estáticos ==="
echo "Bootstrap versão: $VERSION"
echo ""

# Definir caminhos
CSS_DIR="static/css"
JS_DIR="static/js"

# Criar diretórios se não existirem
mkdir -p "$CSS_DIR"
mkdir -p "$JS_DIR"

# Contadores
DOWNLOADED=0
SKIPPED=0
FAILED=0

# Função para baixar arquivo
download_file() {
    local url="$1"
    local output="$2"
    local name="$3"
    
    if [ -f "$output" ] && [ "$FORCE" = false ]; then
        echo "⊘ $name - Já existe (use --force para sobrescrever)"
        ((SKIPPED++))
        return
    fi
    
    echo "↓ Baixando $name..."
    
    if wget -q --show-progress "$url" -O "$output"; then
        size=$(du -h "$output" | cut -f1)
        echo "✓ $name - $size"
        ((DOWNLOADED++))
    else
        echo "✗ Erro ao baixar $name"
        ((FAILED++))
    fi
}

# Baixar arquivos
download_file \
    "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/css/bootstrap.min.css" \
    "$CSS_DIR/bootstrap.min.css" \
    "Bootstrap CSS"

download_file \
    "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/css/bootstrap.min.css.map" \
    "$CSS_DIR/bootstrap.min.css.map" \
    "Bootstrap CSS Source Map"

download_file \
    "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/js/bootstrap.bundle.min.js" \
    "$JS_DIR/bootstrap.bundle.min.js" \
    "Bootstrap JS Bundle"

download_file \
    "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/js/bootstrap.bundle.min.js.map" \
    "$JS_DIR/bootstrap.bundle.min.js.map" \
    "Bootstrap JS Source Map"

# Resumo
echo ""
echo "=== Resumo ==="
echo "Baixados: $DOWNLOADED"
echo "Ignorados: $SKIPPED"
echo "Falhas: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "⚠ Alguns arquivos falharam ao baixar. Verifique sua conexão."
    exit 1
fi

if [ $DOWNLOADED -eq 0 ] && [ $SKIPPED -gt 0 ]; then
    echo "✓ Todos os arquivos já estão atualizados!"
elif [ $DOWNLOADED -gt 0 ]; then
    echo "✓ Download concluído com sucesso!"
fi

echo ""
echo "Próximos passos:"
echo "  1. Testar localmente: python app.py"
echo "  2. Fazer deploy: docker-compose up --build"

