# 🚀 Assinador de PDFs - Sistema de Produção

Sistema completo de assinatura digital de documentos PDF com interface web responsiva, otimizado para tablets e dispositivos móveis.

> **⚠️ IMPORTANTE:** Este sistema foi configurado para usar **PostgreSQL em produção**. SQLite é apenas para desenvolvimento local.

---

## 📋 Índice

1. [Funcionalidades](#-funcionalidades)
2. [Instalação](#-instalação)
3. [Configuração](#-configuração)
4. [Uso](#-uso)
5. [Estrutura do Projeto](#-estrutura-do-projeto)
6. [Deployment](#-deployment)
7. [Segurança](#-segurança)
8. [Monitoramento](#-monitoramento)
9. [Troubleshooting](#-troubleshooting)
10. [Arquivos Não Utilizados](#-arquivos-não-utilizados)

---

## ✨ Funcionalidades

- 📄 **Upload e Assinatura** de arquivos PDF
- ✍️ **Assinatura Digital** com desenho em canvas (apenas cor preta)
- 🔍 **Validação** de assinaturas digitais
- 👥 **Interface Administrativa** completa
- 📊 **Relatórios e Estatísticas** detalhadas
- 📱 **Otimizado para Mobile/Tablet**
- 🚀 **Performance** otimizada para produção
- 🧹 **Limpeza Automática** de arquivos temporários
- 🔐 **Termo de Aceite** baseado na Lei 14.063/2020

---

## 🛠️ Instalação

### Pré-requisitos

#### Desenvolvimento
- **Python 3.9+**
- **pip** ou **uv** (gerenciador de pacotes)
- **Git** (para clonar o repositório)

#### Produção
- **Python 3.9+**
- **PostgreSQL 12+** (banco de dados de produção)
- **NSSM** (apenas Windows - para criar serviço)
  - Download: https://nssm.cc/download
  - Adicione ao PATH ou copie para `C:\Windows\System32\`
- **Gunicorn** (servidor WSGI)
- **Nginx** (opcional - proxy reverso)

### Passo 1: Clonar Repositório

```bash
git clone <url-do-repositorio>
cd Assinaturas
```

### Passo 2: Criar Ambiente Virtual

```bash
# Com venv
python -m venv venv

# Com uv
uv venv
```

### Passo 3: Ativar Ambiente Virtual

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Passo 4: Instalar Dependências

```bash
# Com pip
pip install -r requirements.txt

# Com uv
uv pip install -r requirements.txt
```

---

## ⚙️ Configuração

### Passo 1: Criar Arquivo .env

```bash
# Windows
copy env_example.txt .env

# Linux/macOS
cp env_example.txt .env
```

### Passo 2: Configurar Variáveis de Ambiente

Edite o arquivo `.env` e configure as seguintes variáveis:

#### 🔐 Configurações Obrigatórias

```env
# Ambiente
FLASK_ENV=development
FLASK_DEBUG=True

# Chave Secreta (GERE UMA NOVA PARA PRODUÇÃO!)
# Use: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<sua-chave-secreta-forte>

# Banco de Dados
# Desenvolvimento (SQLite)
DATABASE_URL=sqlite:///assinador.db

# PRODUÇÃO (PostgreSQL) - Use esta configuração em produção!
# DATABASE_URL=postgresql://usuario:senha@localhost:5432/assinador_db

# Servidor
HOST=0.0.0.0
PORT=5001
WORKERS=4
```

#### 🔒 Configurações de Segurança

```env
# CSRF Protection
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600

# Sessão
SESSION_LIFETIME_HOURS=24
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

#### 📁 Configurações de Diretórios

```env
TEMP_DIR=temp_files
STATIC_DIR=static
SIGNATURES_DIR=signatures
CERTIFICATES_DIR=certificates
KEYS_DIR=keys
PDF_SIGNED_DIR=pdf_assinados
LOGS_DIR=logs
```

#### 🧹 Configurações de Limpeza

```env
CLEANUP_INTERVAL=3600
FILE_RETENTION_DAYS=7
TEMP_FILE_RETENTION_HOURS=1
CLEANUP_TIME=02:00
CLEANUP_TZ=America/Sao_Paulo
```

### Passo 3: Gerar Chave Secreta

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado e cole no arquivo `.env` na variável `SECRET_KEY`.

### Passo 4: Configurar PostgreSQL (Produção)

#### Instalar PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**CentOS/RHEL:**
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
```

**Windows:**
- Baixe o instalador: https://www.postgresql.org/download/windows/
- Execute o instalador e siga as instruções

#### Criar Banco de Dados

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar banco de dados
CREATE DATABASE assinador_db;

# Criar usuário
CREATE USER assinador_user WITH PASSWORD 'senha_forte_aqui';

# Dar permissões
GRANT ALL PRIVILEGES ON DATABASE assinador_db TO assinador_user;
ALTER DATABASE assinador_db OWNER TO assinador_user;

# Sair
\q
```

#### Configurar .env para PostgreSQL

```env
# PRODUÇÃO - PostgreSQL
DATABASE_URL=postgresql://assinador_user:senha_forte_aqui@localhost:5432/assinador_db
```

### Passo 5: Inicializar Banco de Dados

```bash
python init_db.py
```

### Passo 6: Gerar Certificado

```bash
python -c "from certificate_manager import certificate_manager; certificate_manager.generate_certificate()"
```

---

## 🚀 Uso

### Desenvolvimento

```bash
# Com uv (recomendado)
uv run python app.py

# Com python
python app.py
```

### Produção (Cria Serviço Automaticamente)

#### Windows (Como Administrador)
```bash
# Execute como Administrador
start_production.bat
```

**O script irá:**
- ✅ Criar serviço Windows automaticamente
- ✅ Configurar para iniciar automaticamente
- ✅ Iniciar o serviço
- ✅ Configurar logs e monitoramento

#### Linux/macOS (Com sudo)
```bash
# Execute com sudo
sudo chmod +x start_production.sh
sudo ./start_production.sh
```

**O script irá:**
- ✅ Criar serviço Systemd automaticamente
- ✅ Configurar para iniciar automaticamente
- ✅ Iniciar o serviço
- ✅ Configurar logs e monitoramento

### Acesso

- **Principal**: http://localhost:5001
- **Login**: http://localhost:5001/login
- **Admin**: http://localhost:5001/admin

### Usuário Padrão

- **Usuário**: `admin`
- **Senha**: `admin123`
- **⚠️ IMPORTANTE**: Altere a senha padrão após o primeiro login!

### Gerenciamento do Serviço

#### Windows

```cmd
# Ver status do serviço
sc query AssinadorPDF

# Parar serviço
nssm stop AssinadorPDF

# Iniciar serviço
nssm start AssinadorPDF

# Reiniciar serviço
nssm restart AssinadorPDF

# Remover serviço (ou use o script)
nssm remove AssinadorPDF confirm
# OU
remove_service.bat
```

#### Linux

```bash
# Ver status do serviço
sudo systemctl status assinador-pdf

# Parar serviço
sudo systemctl stop assinador-pdf

# Iniciar serviço
sudo systemctl start assinador-pdf

# Reiniciar serviço
sudo systemctl restart assinador-pdf

# Desabilitar serviço
sudo systemctl disable assinador-pdf

# Remover serviço (ou use o script)
sudo rm /etc/systemd/system/assinador-pdf.service
sudo systemctl daemon-reload
# OU
sudo ./remove_service.sh

# Ver logs em tempo real
sudo journalctl -u assinador-pdf -f

# Ver logs de erro
sudo journalctl -u assinador-pdf -p err
```

---

## 📁 Estrutura do Projeto

```
📦 AssinadorPDF/
├── 🐍 app.py                    # Aplicação principal Flask
├── 🐍 config.py                 # Configurações (usa .env)
├── 🐍 models.py                 # Modelos do banco de dados
├── 🐍 forms.py                  # Formulários WTForms
├── 🐍 auth.py                   # Sistema de autenticação
├── 🐍 crypto_utils.py           # Utilitários de criptografia
├── 🐍 certificate_manager.py    # Gerenciamento de certificados
├── 🐍 pdf_validator.py          # Validação de PDFs
├── 🐍 password_utils.py         # Utilitários de senha
├── 🐍 mobile_optimizations.py   # Otimizações mobile
├── 🐍 init_db.py                # Inicialização do banco
├── 📄 requirements.txt          # Dependências
├── 📄 pyproject.toml            # Configuração do projeto
├── 📄 .env                      # Variáveis de ambiente (NÃO commitado)
├── 📄 env_example.txt           # Exemplo de configuração
├── 📄 .gitignore                # Arquivos ignorados pelo Git
├── 🚀 start_production.sh       # Script de inicialização com serviço (Linux/macOS)
├── 🚀 start_production.bat      # Script de inicialização com serviço (Windows)
├── 🗑️ remove_service.sh         # Script para remover serviço (Linux/macOS)
├── 🗑️ remove_service.bat        # Script para remover serviço (Windows)
├── 📁 templates/                # Templates HTML
│   ├── admin/                   # Templates administrativos
│   ├── client/                  # Templates do cliente
│   ├── internal/                # Templates internos
│   └── signature/               # Templates de assinatura
├── 📁 static/                   # Arquivos estáticos
│   └── images/
│       └── logo.png
├── 📁 instance/                 # Banco de dados
│   └── assinador.db
├── 📁 temp_files/               # Arquivos temporários
├── 📁 pdf_assinados/            # PDFs assinados
├── 📁 signatures/               # Assinaturas
├── 📁 certificates/             # Certificados
├── 📁 keys/                     # Chaves
└── 📁 logs/                     # Logs
```

---

## 🚀 Deployment

### Opção 1: Script de Inicialização com Serviço (Recomendado)

#### Windows (Como Administrador)
```bash
# Execute como Administrador
start_production.bat
```

**O script irá:**
- ✅ Verificar arquivo .env
- ✅ Criar diretórios necessários
- ✅ Inicializar banco de dados
- ✅ Gerar certificado
- ✅ Criar serviço Windows com NSSM
- ✅ Configurar para iniciar automaticamente
- ✅ Iniciar o serviço
- ✅ Configurar logs rotativos

#### Linux/macOS (Com sudo)
```bash
# Execute com sudo
sudo chmod +x start_production.sh
sudo ./start_production.sh
```

**O script irá:**
- ✅ Verificar arquivo .env
- ✅ Criar diretórios necessários
- ✅ Inicializar banco de dados
- ✅ Gerar certificado
- ✅ Criar serviço Systemd
- ✅ Configurar para iniciar automaticamente
- ✅ Iniciar o serviço
- ✅ Configurar logs no journalctl

### Opção 2: Iniciar Manualmente com Gunicorn

```bash
gunicorn --bind 0.0.0.0:80 \
         --workers 4 \
         --worker-class sync \
         --timeout 120 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         --log-level info \
         --capture-output \
         app:app
```

### Opção 3: Usando Systemd (Linux)

Crie o arquivo `/etc/systemd/system/assinador.service`:

```ini
[Unit]
Description=Assinador de PDFs
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/caminho/para/Assinaturas
Environment="PATH=/caminho/para/venv/bin"
ExecStart=/caminho/para/venv/bin/gunicorn --bind 0.0.0.0:80 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable assinador
sudo systemctl start assinador
```

### Opção 4: Usando Nginx como Proxy Reverso

```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Opção 5: Docker (Windows/Linux)

#### Pré-requisitos
- Windows: Docker Desktop instalado e em execução (`https://docs.docker.com/desktop/`)
- Linux: Docker Engine + Docker Compose V2 (`https://docs.docker.com/engine/install/` e `https://docs.docker.com/compose/install/`)

#### 1) Criar arquivo .env
- Windows (PowerShell):
```powershell
copy env_example.txt .env
notepad .env
```
- Linux:
```bash
cp env_example.txt .env
nano .env
```
Edite ao menos:
```env
SECRET_KEY=coloque_uma_chave_forte
POSTGRES_PASSWORD=senha_forte_do_postgres
SERVER_NAME=assinador.seudominio.com   # opcional em dev
COOKIE_DOMAIN=.seudominio.com          # opcional em dev
```

#### 2) Subir com Docker Compose
```bash
docker compose up -d --build
```

#### 3) Acessar
- App: `http://localhost:5001`
- Healthcheck: `http://localhost:5001/healthz`

#### 4) Logs e status
```bash
docker compose logs -f web       # logs do app
docker compose ps                # deve mostrar web (healthy)
```

#### 5) Parar/Remover containers
```bash
docker compose down              # mantém volumes (dados do Postgres)
docker compose down -v           # remove volumes (APAGA dados do Postgres)
```

#### 6) Atualizar imagem/config
```bash
docker compose build --no-cache web
docker compose up -d
```

#### 7) Pastas montadas e permissões (Linux)
As pastas `logs/`, `pdf_assinados/`, `temp_files/` e `keys/` são montadas no container.
Em Linux, garanta que o seu usuário tenha permissão:
```bash
mkdir -p logs pdf_assinados temp_files keys
sudo chown -R $USER:$USER logs pdf_assinados temp_files keys
```

#### 8) Reset do banco (opcional)
O volume do Postgres se chama `db_data` (o nome real pode aparecer como `<projeto>_db_data`). Para apagar todos os dados:
```bash
docker compose down -v
# ou apague apenas o volume do Postgres
docker volume ls
docker volume rm <nome_do_volume_db_data>
```

#### 9) Variáveis úteis no .env (exemplo)
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=coloque_uma_chave_forte
POSTGRES_PASSWORD=senha_forte_do_postgres
SERVER_NAME=assinador.seudominio.com
COOKIE_DOMAIN=.seudominio.com
```

Observações:
- Em produção, coloque o serviço atrás de um proxy HTTPS (Nginx/Traefik) e aponte para `web:5001`.
- Os headers de proxy já são tratados (ProxyFix). HSTS/CSP são aplicados automaticamente em `FLASK_ENV=production`.

---

## 🔐 Segurança

### Configurações de Produção

Para produção, configure no arquivo `.env`:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<sua-chave-secreta-forte>
SESSION_COOKIE_SECURE=True
DATABASE_URL=<url-do-banco-de-dados>
```

### Checklist de Segurança

- [ ] `SECRET_KEY` foi alterada e é forte
- [ ] `FLASK_DEBUG=False`
- [ ] `SESSION_COOKIE_SECURE=True` (requer HTTPS)
- [ ] Banco de dados com senha forte
- [ ] Firewall configurado
- [ ] HTTPS/SSL configurado
- [ ] Backup automático configurado
- [ ] Logs sendo monitorados
- [ ] Limpeza automática ativada

### HTTPS com Let's Encrypt

```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com
```

---

## 📊 Monitoramento

### Logs

#### Windows
Os logs são salvos em:
- `logs/service.log` - Log principal do serviço
- `logs/service_error.log` - Log de erros do serviço
- `logs/access.log` - Log de acesso (Gunicorn)
- `logs/error.log` - Log de erros (Gunicorn)

#### Linux
Os logs são salvos em:
- `logs/assinador.log` - Log principal da aplicação
- `logs/access.log` - Log de acesso (Gunicorn)
- `logs/error.log` - Log de erros (Gunicorn)
- `journalctl` - Logs do Systemd

### Verificar Status

#### Windows
```cmd
# Status do serviço
sc query AssinadorPDF

# Ver logs em tempo real
type logs\service.log

# Ver logs de erro
type logs\service_error.log
```

#### Linux
```bash
# Status do serviço
sudo systemctl status assinador-pdf

# Ver logs em tempo real
sudo journalctl -u assinador-pdf -f

# Ver logs de erro
sudo journalctl -u assinador-pdf -p err

# Ver logs da aplicação
tail -f logs/assinador.log
```

### Verificar Performance

Acesse: `http://seu-servidor/admin/dashboard`

---

## 🔄 Backup

### Backup Automático do PostgreSQL

#### Backup Completo

Crie um script de backup:

```bash
#!/bin/bash
# backup_postgres.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="assinador_db"
DB_USER="assinador_user"

mkdir -p $BACKUP_DIR

# Backup completo
pg_dump -U $DB_USER -F c -f "$BACKUP_DIR/assinador_db_$DATE.backup" $DB_NAME

# Comprimir
gzip "$BACKUP_DIR/assinador_db_$DATE.backup"

# Manter apenas os últimos 30 backups
find $BACKUP_DIR -name "assinador_db_*.backup.gz" -mtime +30 -delete

echo "Backup concluído: assinador_db_$DATE.backup.gz"
```

Adicione ao crontab:
```bash
0 2 * * * /caminho/para/backup_postgres.sh
```

#### Restaurar Backup

```bash
# Descomprimir
gunzip assinador_db_20240101_020000.backup.gz

# Restaurar
pg_restore -U assinador_user -d assinador_db assinador_db_20240101_020000.backup
```

### Backup SQLite (Desenvolvimento)

```bash
#!/bin/bash
# backup_sqlite.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/sqlite"
DB_FILE="instance/assinador.db"

mkdir -p $BACKUP_DIR
cp $DB_FILE "$BACKUP_DIR/assinador_$DATE.db"

# Manter apenas os últimos 30 backups
find $BACKUP_DIR -name "assinador_*.db" -mtime +30 -delete
```

---

## 🚨 Troubleshooting

### Erro de Banco de Dados

#### SQLite (Desenvolvimento)

```bash
# Recrie o banco de dados
rm instance/assinador.db
python init_db.py
```

#### PostgreSQL (Produção)

```bash
# Verificar conexão
psql -U assinador_user -d assinador_db -h localhost

# Verificar se o banco existe
psql -U postgres -l

# Recriar banco de dados
psql -U postgres
DROP DATABASE assinador_db;
CREATE DATABASE assinador_db;
GRANT ALL PRIVILEGES ON DATABASE assinador_db TO assinador_user;
ALTER DATABASE assinador_db OWNER TO assinador_user;
\q

# Reinicializar
python init_db.py
```

### Problemas de Conexão PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Iniciar PostgreSQL
sudo systemctl start postgresql

# Verificar configuração pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Reiniciar PostgreSQL após alterações
sudo systemctl restart postgresql
```

### Erro de Dependências

```bash
# Atualize as dependências
pip install -r requirements.txt
```

### Problemas de Permissão

- Verifique se o usuário tem acesso de escrita nas pastas
- Certifique-se de que as chaves criptográficas estão acessíveis

### Verificar Sistema

```bash
# Verificar se todas as dependências estão instaladas
pip list

# Verificar se o banco de dados existe
ls -la instance/

# Verificar se o certificado existe
ls -la certificates/
```

### Problemas com o Serviço

#### Windows

```cmd
# Verificar status do serviço
sc query AssinadorPDF

# Ver logs do serviço
type logs\service.log

# Reiniciar serviço
nssm restart AssinadorPDF

# Se o serviço não iniciar, verifique:
# 1. Se o NSSM está instalado
# 2. Se o arquivo .env existe
# 3. Se o ambiente virtual está configurado
# 4. Se as portas não estão em uso
```

#### Linux

```bash
# Verificar status do serviço
sudo systemctl status assinador-pdf

# Ver logs do serviço
sudo journalctl -u assinador-pdf -n 50

# Reiniciar serviço
sudo systemctl restart assinador-pdf

# Se o serviço não iniciar, verifique:
# 1. Se o arquivo .env existe
# 2. Se o ambiente virtual está configurado
# 3. Se as portas não estão em uso
# 4. Se as permissões estão corretas
```

---

## 🗑️ Arquivos Não Utilizados

### Arquivos que PODEM ser removidos:

#### 📄 Documentação Antiga (Opcional)
- `CLEANUP_SYSTEM.md` - Substituído por este README
- `DEPLOY_GUIDE.md` - Substituído por este README
- `PRODUCTION_SUMMARY.md` - Substituído por este README
- `SYSTEM_ANALYSIS_REPORT.md` - Substituído por este README
- `PRODUCTION_SETUP.md` - Substituído por este README

#### 🧪 Scripts de Teste (Opcional)
- `check_system.bat` - Script de verificação do sistema
- `install_service.bat` - Script de instalação de serviço
- `uninstall_service.bat` - Script de desinstalação de serviço

#### 📦 Cache e Build
- `__pycache__/` - Cache do Python (gerado automaticamente)
- `*.pyc` - Arquivos compilados (gerados automaticamente)
- `uv.lock` - Lock file do uv (opcional)

#### 🗂️ Arquivos Temporários
- `temp_files/*.pdf` - PDFs temporários antigos
- `temp_files/*.txt` - Arquivos de teste
- `pdf_assinados/*.pdf` - PDFs assinados antigos (após backup)

### Arquivos que DEVEM ser mantidos:

✅ **Core da Aplicação:**
- `app.py`, `config.py`, `models.py`, `forms.py`, `auth.py`
- `crypto_utils.py`, `certificate_manager.py`, `pdf_validator.py`
- `password_utils.py`, `mobile_optimizations.py`, `init_db.py`

✅ **Configuração:**
- `requirements.txt`, `pyproject.toml`, `.env`, `env_example.txt`, `.gitignore`

✅ **Scripts:**
- `start_production.sh`, `start_production.bat`

✅ **Templates e Static:**
- `templates/`, `static/images/logo.png`

---

## 🏗️ Tecnologias Utilizadas

- **Backend**: Flask (Python) + Gunicorn
- **Banco de Dados**: SQLite com SQLAlchemy
- **Autenticação**: Flask-Login com bcrypt
- **Frontend**: Bootstrap 5 + Font Awesome
- **Criptografia**: PyCryptodome + Cryptography
- **PDF**: PyPDF2 + ReportLab
- **Cache**: Flask-Caching
- **Compressão**: Flask-Compress
- **Variáveis de Ambiente**: python-dotenv

---

## 📱 Funcionalidades Detalhadas

### Sistema de Autenticação
- **Login/Logout** com sessões seguras
- **Apenas Administradores** podem criar novas contas de usuário
- **Controle de permissões** (Usuário normal vs Administrador)
- **Gerenciamento de perfis** com alteração de senha
- **Sessões com expiração** automática

### Assinatura de PDFs
- **Assinatura digital** com certificado X.509
- **Assinatura desenhada** com canvas interativo (apenas cor preta)
- **Rubrica posicionada acima** do nome no carimbo
- **Verificação de integridade** dos documentos
- **Metadados embutidos** para rastreabilidade

### Painel Administrativo
- **Dashboard** com estatísticas em tempo real
- **Gerenciamento de usuários** (criar, editar, deletar)
- **Relatórios detalhados** com filtros
- **Exportação de dados** em formato JSON
- **Monitoramento de atividade** do sistema
- **Limpeza de arquivos** automática e manual

### Termo de Aceite
- **Lei 14.063/2020** - Uso de assinaturas eletrônicas
- **LGPD** - Proteção de dados pessoais
- **Declarações de responsabilidade** do cidadão
- **Características técnicas** da assinatura

---

## 📈 Otimizações de Performance

### Configurações Recomendadas

```env
# Para servidor com 4GB RAM
WORKERS=4
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Para servidor com 8GB+ RAM
WORKERS=8
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=600
```

### Banco de Dados

**⚠️ IMPORTANTE:** Para produção, **SEMPRE use PostgreSQL**. SQLite é apenas para desenvolvimento!

#### PostgreSQL (Recomendado para Produção)

```env
# PostgreSQL
DATABASE_URL=postgresql://usuario:senha@localhost:5432/assinador_db
```

**Vantagens do PostgreSQL:**
- ✅ Melhor performance
- ✅ Suporte a transações ACID
- ✅ Backup e recuperação robustos
- ✅ Suporte a múltiplos usuários simultâneos
- ✅ Recursos avançados (views, triggers, stored procedures)
- ✅ Escalabilidade horizontal

#### MySQL (Alternativa)

```env
# MySQL
DATABASE_URL=mysql://usuario:senha@localhost:3306/assinador_db
```

#### SQLite (Apenas Desenvolvimento)

```env
# SQLite - NÃO USE EM PRODUÇÃO!
DATABASE_URL=sqlite:///assinador.db
```

---

## ✅ Checklist Final

Antes de colocar em produção:

- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas
- [ ] Arquivo `.env` configurado
- [ ] `SECRET_KEY` alterada
- [ ] **PostgreSQL instalado e configurado**
- [ ] **Banco de dados PostgreSQL criado**
- [ ] **DATABASE_URL configurado para PostgreSQL**
- [ ] Banco de dados inicializado
- [ ] Certificado gerado
- [ ] Diretórios criados
- [ ] Serviço criado (start_production.sh/bat)
- [ ] HTTPS configurado
- [ ] Firewall configurado
- [ ] Backup configurado
- [ ] Monitoramento configurado
- [ ] Testes realizados
- [ ] Documentação lida

---

## ⚡ Performance & Otimizações

### Arquitetura Async

O sistema foi otimizado para alta performance com suporte assíncrono:

- **SQLAlchemy Async**: Operações de banco de dados assíncronas com `asyncpg`
- **Processamento Paralelo**: Uso de `asyncio.gather` para operações simultâneas
- **Thread Pool**: Processamento pesado de PDFs em thread pool separado
- **Pool de Conexões**: Configurado com 20 conexões base + 30 overflow

### Cache

Sistema de cache em múltiplas camadas:

- **Hash SHA256 Cacheado**: Evita recálculo constante de hashes de PDFs
- **Flask-Caching**: Cache de relatórios e queries frequentes
- **Lazy Loading**: Relationships SQLAlchemy configurados como `lazy='dynamic'`
- **Timeout Configurável**: Cache com TTL de 300 segundos (5 minutos)

### Índices de Performance

Índices otimizados para queries rápidas:

```sql
-- Tabela signatures
CREATE INDEX idx_signatures_user_id ON signatures (user_id);
CREATE INDEX idx_signatures_timestamp ON signatures (timestamp);
CREATE INDEX idx_signatures_file_id ON signatures (file_id);
CREATE INDEX idx_signatures_status ON signatures (status);
CREATE INDEX idx_signatures_hash ON signatures (signature_hash);

-- Tabela users
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);

-- Tabela user_sessions
CREATE INDEX idx_sessions_user_id ON user_sessions (user_id);
CREATE INDEX idx_sessions_expires_at ON user_sessions (expires_at);
CREATE INDEX idx_sessions_session_id ON user_sessions (session_id);
```

### Armazenamento Otimizado

- **PDFs no Filesystem**: Armazenamento em `pdf_assinados/{year}/{month}/` ao invés do banco
- **Redução de 80-90%**: Tamanho do banco de dados significativamente reduzido
- **Backup Eficiente**: Backups do banco muito mais rápidos

### Queries Assíncronas

Módulo `async_queries.py` com versões assíncronas de:

- `get_signature_stats_async()`: Estatísticas de assinaturas
- `get_user_stats_async()`: Estatísticas de usuários
- `get_recent_signatures_async()`: Assinaturas recentes
- `get_signature_by_file_id_async()`: Busca por file_id
- `get_user_signatures_async()`: Assinaturas de usuário
- `get_expired_sessions_async()`: Sessões expiradas

### Validação Unificada

Lógica de validação consolidada em `crypto_utils.py`:

- `verify_pdf_signature_unified()`: Função única para verificação
- Elimina código duplicado entre `crypto_utils` e `pdf_validator`
- Melhor manutenibilidade e consistência

### Impacto Esperado

**Performance:**
- 🔥 **Redução de 20s para 1-3s** em operações de validação múltipla
- 🔥 **Queries 5-10x mais rápidas** com índices otimizados
- ⚡ **Cache SHA256** elimina recálculo constante
- ⚡ **Armazenamento em filesystem** reduz tamanho do DB em 80-90%

**Escalabilidade:**
- ✅ **100+ requests simultâneas** com async
- ✅ **Pool de conexões** otimizado (20 base + 30 overflow)
- ✅ **Lazy loading** reduz uso de memória

---

## 🔒 Segurança Avançada

### Rate Limiting

Sistema de rate limiting implementado com Flask-Limiter:

```python
# Limites padrão
default_limits=["200 per day", "50 per hour"]

# Limites específicos por rota
@limiter.limit("10 per minute")  # Assinatura
@limiter.limit("20 per minute")  # Validação
```

### Logs de Auditoria

Sistema de logging estruturado em JSON:

**Arquivo**: `logs/audit.log`

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "event_type": "signature",
  "user_id": 1,
  "file_id": "abc123",
  "status": "success",
  "ip_address": "192.168.1.100",
  "details": {"filename": "documento.pdf"}
}
```

**Tipos de eventos:**
- `signature`: Eventos de assinatura
- `validation`: Eventos de validação
- `signature_failed`: Tentativas falhadas
- `security`: Eventos de segurança
- `admin_action`: Ações administrativas

### Proteção de Chaves

Chaves privadas protegidas:

```env
# Diretório seguro fora do projeto
KEYS_DIR_SECURE=/etc/assinador/keys
```

**Permissões:**
```bash
chmod 700 /etc/assinador/keys
chmod 600 /etc/assinador/keys/private_key.pem
```

### Forçar Troca de Senha

Admin padrão configurado para trocar senha no primeiro login:

```python
admin.must_change_password = True
```

---

## 🗄️ Migrations com Alembic

O sistema agora usa Alembic para versionamento de schema:

### Comandos Básicos

```bash
# Inicializar Alembic (já feito)
alembic init alembic

# Criar nova migration
alembic revision -m "descrição da mudança"

# Criar migration automática
alembic revision --autogenerate -m "descrição"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1

# Ver histórico
alembic history

# Ver versão atual
alembic current
```

### Migrations Automáticas

Os scripts de produção aplicam migrations automaticamente:

**Linux:**
```bash
./start_production.sh
# Aplica: alembic upgrade head
```

**Windows:**
```batch
start_production.bat
REM Aplica: alembic upgrade head
```

---

## 📊 Monitoramento de Performance

### Logs Estruturados

**Auditoria**: `logs/audit.log`
```bash
tail -f logs/audit.log | jq .
```

**Aplicação**: `logs/assinador.log`
```bash
tail -f logs/assinador.log
```

**Serviço** (Linux):
```bash
sudo journalctl -u assinador-pdf -f
```

### Métricas de Performance

**Queries lentas**:
```python
# Habilitar SQLAlchemy echo em desenvolvimento
SQLALCHEMY_ECHO = True
```

**Cache hit rate**:
```python
from flask_caching import Cache
cache.get_stats()  # {'hits': 100, 'misses': 20}
```

---

## 🎉 Sistema Pronto para Produção!

Após a instalação e configuração, o sistema estará:
- ✅ Rodando com Gunicorn
- ✅ Configurado com .env
- ✅ Otimizado para tablets/mobile
- ✅ Monitorado e com logs
- ✅ Seguro e configurado
- ✅ Com limpeza automática

**URL de Acesso**: http://localhost:5001

---

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs em `logs/assinador.log`
2. Verifique se todas as variáveis de ambiente estão configuradas
3. Verifique se os diretórios necessários existem
4. Verifique se as portas estão abertas no firewall

---

## 📚 Versões

### v3.1.0 (Atual - Produção)
- ✅ **Criação automática de serviços** Windows e Linux
- ✅ **Inicialização automática** após reiniciar o servidor
- ✅ **Logs rotativos** configurados
- ✅ **Monitoramento** integrado
- ✅ **Reinício automático** em caso de falha
- ✅ **Configuração com .env** completa
- ✅ **Assinatura apenas em preto**
- ✅ **Rubrica acima do nome** no carimbo
- ✅ **Termo de aceite** atualizado (Lei 14.063/2020)
- ✅ **Scripts de produção** para Windows e Linux
- ✅ **Documentação consolidada** em um único README
- ✅ **.gitignore** configurado
- ✅ **Segurança** aprimorada

### v2.0.0
- ✅ Sistema de usuários e autenticação
- ✅ Controle de permissões
- ✅ Painel administrativo
- ✅ Relatórios e estatísticas
- ✅ Interface moderna e responsiva
- ✅ Rotina diária de limpeza

### v1.0.0
- ✅ Assinatura digital básica
- ✅ Verificação de integridade
- ✅ Suporte a certificados X.509

---

**Desenvolvido com ❤️ para facilitar a assinatura digital de documentos**
