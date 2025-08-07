#!/bin/bash

echo "========================================"
echo "    Assinador Rápido de PDFs"
echo "========================================"
echo
echo "Instalando dependencias..."
echo

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python não encontrado!"
    echo "Por favor, instale o Python 3.8 ou superior."
    echo "Visite: https://www.python.org/downloads/"
    exit 1
fi

echo "Python encontrado. Instalando dependencias..."
pip3 install flask PyPDF2 reportlab pillow

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
echo "  python app.py"
echo
echo "A aplicação será aberta em:"
echo "  http://localhost:5000"
echo 