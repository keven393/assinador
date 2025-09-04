#!/bin/bash

echo "========================================"
echo "    Instalador do Assinador de PDFs"
echo "========================================"
echo

echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado!"
    echo "Por favor, instale o Python 3.9+ primeiro."
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "Python encontrado!"
echo

echo "Verificando versão do Python..."
python3 --version
echo

echo "Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependências!"
    echo "Tente executar: pip3 install --upgrade pip"
    exit 1
fi

echo
echo "Dependências instaladas com sucesso!"
echo

echo "Inicializando banco de dados..."
python3 init_db.py

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao inicializar banco de dados!"
    exit 1
fi

echo
echo "========================================"
echo "    Instalação concluída com sucesso!"
echo "========================================"
echo
echo "Para executar a aplicação:"
echo "  python3 app.py"
echo
echo "Acesse: http://localhost:5000"
echo
echo "Usuário padrão: admin"
echo "Senha padrão: admin123"
echo
echo "IMPORTANTE: Altere a senha padrão após o primeiro login!"
echo 