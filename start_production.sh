#!/bin/bash
# ============================================
# Script de Inicialização para Produção (Linux)
# Cria serviço Systemd automaticamente
# ============================================

echo "============================================"
echo "  Assinador de PDFs - Configuração de Serviço"
echo "============================================"

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERRO: Este script precisa ser executado como root (sudo)"
    echo "Execute: sudo $0"
    exit 1
fi

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "❌ ERRO: Arquivo .env não encontrado!"
    echo "Por favor, copie o arquivo env_example.txt para .env e configure as variáveis."
    exit 1
fi

# Carrega variáveis de ambiente
export $(cat .env | grep -v '^#' | xargs)

# Obtém o caminho completo do diretório
PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/venv"

# Verifica se o ambiente virtual existe
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ ERRO: Ambiente virtual não encontrado em $VENV_DIR"
    echo "Por favor, crie o ambiente virtual primeiro:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Cria diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p temp_files
mkdir -p pdf_assinados
mkdir -p signatures
mkdir -p certificates
mkdir -p keys
mkdir -p logs
mkdir -p static/images

# Verifica se o banco de dados existe
if [ ! -f "instance/assinador.db" ]; then
    echo "📊 Inicializando banco de dados..."
    $VENV_DIR/bin/python init_db.py
fi

# Verifica se o certificado existe
if [ ! -f "certificates/certificate.pem" ]; then
    echo "🔐 Gerando certificado..."
    $VENV_DIR/bin/python -c "from certificate_manager import certificate_manager; certificate_manager.generate_certificate()"
fi

echo ""
echo "📦 Aplicando migrations do Alembic..."
$VENV_DIR/bin/alembic upgrade head
if [ $? -ne 0 ]; then
    echo "❌ Erro ao aplicar migrations do Alembic."
    exit 1
fi

# Define o nome do serviço
SERVICE_NAME="assinador-pdf"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo ""
echo "🔧 Criando serviço Systemd..."

# Cria o arquivo de serviço
cat > $SERVICE_FILE <<EOF
[Unit]
Description=Assinador de PDFs - Sistema de Assinatura Digital
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="FLASK_ENV=production"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --bind $HOST:$PORT \\
    --workers $WORKERS \\
    --worker-class sync \\
    --timeout 120 \\
    --access-logfile $PROJECT_DIR/logs/access.log \\
    --error-logfile $PROJECT_DIR/logs/error.log \\
    --log-level info \\
    --capture-output \\
    app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Segurança
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR/temp_files $PROJECT_DIR/pdf_assinados $PROJECT_DIR/signatures $PROJECT_DIR/certificates $PROJECT_DIR/keys $PROJECT_DIR/logs $PROJECT_DIR/instance

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Arquivo de serviço criado: $SERVICE_FILE"

# Recarrega o systemd
echo "🔄 Recarregando systemd..."
systemctl daemon-reload

# Habilita o serviço para iniciar automaticamente
echo "🔧 Habilitando serviço para iniciar automaticamente..."
systemctl enable $SERVICE_NAME

# Inicia o serviço
echo "🚀 Iniciando serviço..."
systemctl start $SERVICE_NAME

# Aguarda um momento para o serviço iniciar
sleep 3

# Verifica o status do serviço
echo ""
echo "📊 Status do serviço:"
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "============================================"
echo "  ✅ Serviço Configurado com Sucesso!"
echo "============================================"
echo ""
echo "📋 Comandos úteis:"
echo "  Status:     sudo systemctl status $SERVICE_NAME"
echo "  Parar:      sudo systemctl stop $SERVICE_NAME"
echo "  Iniciar:    sudo systemctl start $SERVICE_NAME"
echo "  Reiniciar:  sudo systemctl restart $SERVICE_NAME"
echo "  Desabilitar: sudo systemctl disable $SERVICE_NAME"
echo ""
echo "📄 Logs:"
echo "  Ver logs:   sudo journalctl -u $SERVICE_NAME -f"
echo "  Logs de erro: sudo journalctl -u $SERVICE_NAME -p err"
echo ""
echo "🌐 Acesso:"
echo "  URL: http://$HOST:$PORT"
echo ""
echo "============================================"
