#!/bin/bash

echo "========================================"
echo "    Assinador Rápido de PDFs - UV"
echo "========================================"
echo
echo "Instalando dependencias com UV..."
echo

# Verifica se uv está instalado
if ! command -v uv &> /dev/null; then
    echo "ERRO: UV não encontrado!"
    echo "Por favor, instale o UV primeiro."
    echo "Visite: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "UV encontrado. Instalando dependencias..."
uv add flask PyPDF2 reportlab pillow cryptography pycryptodome

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependencias!"
    exit 1
fi

echo
echo "========================================"
echo "    Instalação concluída com sucesso!"
echo "========================================"
echo
echo "Para executar a aplicação, use:"
echo "  uv run python app.py"
echo
echo "A aplicação será aberta em:"
echo "  http://localhost:5000"
echo 