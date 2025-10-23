#!/bin/bash
# Script para baixar arquivos estáticos (Bootstrap) do CDN
# Executar antes do build ou deploy

set -e -o pipefail

# Variáveis (podem ser sobrescritas via env)
VERSION="${BOOTSTRAP_VERSION:-5.3.0}"
FORCE="${FORCE:-false}"

# Processar argumentos da linha de comando
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
            echo "Aviso: Argumento desconhecido: $1"
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
    
    # Desabilitar set -e temporariamente para capturar erro do wget
    set +e
    wget --show-progress "$url" -O "$output" 2>&1
    local wget_exit=$?
    set -e
    
    if [ $wget_exit -eq 0 ] && [ -f "$output" ] && [ -s "$output" ]; then
        size=$(du -h "$output" | cut -f1)
        echo "✓ $name - $size"
        ((DOWNLOADED++))
    else
        echo "✗ Erro ao baixar $name (exit code: $wget_exit)"
        rm -f "$output"  # Limpar arquivo corrompido
        ((FAILED++))
    fi
}

# Baixar arquivos essenciais
download_file \
    "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/css/bootstrap.min.css" \
    "$CSS_DIR/bootstrap.min.css" \
    "Bootstrap CSS"

download_file \
    "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/js/bootstrap.bundle.min.js" \
    "$JS_DIR/bootstrap.bundle.min.js" \
    "Bootstrap JS Bundle"

# Source maps são opcionais (não falhar se não baixar)
echo ""
echo "Baixando source maps (opcionais)..."
wget -q "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/css/bootstrap.min.css.map" -O "$CSS_DIR/bootstrap.min.css.map" 2>/dev/null && echo "✓ CSS Source Map" || echo "⊘ CSS Source Map (ignorado)"
wget -q "https://cdn.jsdelivr.net/npm/bootstrap@$VERSION/dist/js/bootstrap.bundle.min.js.map" -O "$JS_DIR/bootstrap.bundle.min.js.map" 2>/dev/null && echo "✓ JS Source Map" || echo "⊘ JS Source Map (ignorado)"

# Resumo
echo ""
echo "=== Resumo ==="
echo "Baixados: $DOWNLOADED"
echo "Ignorados: $SKIPPED"
echo "Falhas: $FAILED"
echo ""

# Verificar se arquivos essenciais existem
ESSENTIAL_FILES=("$CSS_DIR/bootstrap.min.css" "$JS_DIR/bootstrap.bundle.min.js")
MISSING=0

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ ! -f "$file" ] || [ ! -s "$file" ]; then
        echo "✗ ERRO: Arquivo essencial ausente ou vazio: $file"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "⚠ Erro: $MISSING arquivo(s) essencial(is) não encontrado(s)."
    exit 1
fi

if [ $FAILED -gt 0 ]; then
    echo "⚠ Alguns arquivos opcionais falharam, mas arquivos essenciais OK."
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

