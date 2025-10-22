#!/bin/bash
# ============================================
# Script para Remover Serviço (Linux)
# ============================================

echo "============================================"
echo "  Removendo Serviço - Assinador de PDFs"
echo "============================================"

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERRO: Este script precisa ser executado como root (sudo)"
    echo "Execute: sudo $0"
    exit 1
fi

# Define o nome do serviço
SERVICE_NAME="assinador-pdf"

# Verifica se o serviço existe
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    echo "🛑 Parando serviço..."
    systemctl stop $SERVICE_NAME
    
    echo "🚫 Desabilitando serviço..."
    systemctl disable $SERVICE_NAME
    
    echo "🗑️  Removendo arquivo de serviço..."
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    
    echo "🔄 Recarregando systemd..."
    systemctl daemon-reload
    
    echo "✅ Serviço removido com sucesso!"
else
    echo "⚠️  Serviço não encontrado: $SERVICE_NAME"
fi

echo ""
echo "============================================"

