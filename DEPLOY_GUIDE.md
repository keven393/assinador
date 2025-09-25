# 🚀 Guia de Deploy - Assinador de PDFs

## 📋 Pré-requisitos

### Sistema Operacional
- **Windows Server 2016+** ou **Windows 10/11**
- **Acesso de Administrador** obrigatório
- **Python 3.11+** instalado

### Dependências
- **UV** (gerenciador de pacotes Python)
- **NSSM** (será baixado automaticamente)
- **Porta 5001** disponível

## 🛠️ Instalação Rápida

### 1. **Preparar o Servidor**
```cmd
# 1. Instalar UV (se não estiver instalado)
# Baixe de: https://github.com/astral-sh/uv
# Ou execute: pip install uv

# 2. Verificar Python
python --version

# 3. Verificar UV
uv --version
```

### 2. **Deploy dos Arquivos**
```cmd
# 1. Copie todos os arquivos para o servidor
# Exemplo: C:\AssinadorPDF\

# 2. Estrutura mínima necessária:
# ├── app.py
# ├── asgi.py
# ├── config.py
# ├── models.py
# ├── forms.py
# ├── auth.py
# ├── crypto_utils.py
# ├── certificate_manager.py
# ├── pdf_validator.py
# ├── password_utils.py
# ├── mobile_optimizations.py
# ├── requirements.txt
# ├── templates/
# ├── static/
# ├── install_service.bat
# └── uninstall_service.bat
```

### 3. **Instalar o Serviço**
```cmd
# 1. Abra o Prompt como Administrador
# 2. Navegue até a pasta do projeto
cd C:\AssinadorPDF

# 3. Execute o instalador
install_service.bat
```

## 📁 Estrutura de Arquivos Essenciais

### **Arquivos Principais**
```
📦 AssinadorPDF/
├── 🐍 app.py                    # Aplicação principal
├── 🐍 asgi.py                   # Configuração ASGI
├── 🐍 config.py                 # Configurações
├── 🐍 models.py                 # Modelos do banco
├── 🐍 forms.py                  # Formulários
├── 🐍 auth.py                   # Autenticação
├── 🐍 crypto_utils.py           # Criptografia
├── 🐍 certificate_manager.py    # Certificados
├── 🐍 pdf_validator.py          # Validação PDF
├── 🐍 password_utils.py         # Utilitários de senha
├── 🐍 mobile_optimizations.py  # Otimizações mobile
├── 📄 requirements.txt          # Dependências
├── 🎯 install_service.bat      # Instalador do serviço
├── 🎯 uninstall_service.bat     # Removedor do serviço
├── 📁 templates/               # Templates HTML
├── 📁 static/                  # Arquivos estáticos
├── 📁 instance/               # Banco de dados (criado automaticamente)
├── 📁 logs/                    # Logs do sistema (criado automaticamente)
├── 📁 pdf_assinados/          # PDFs assinados (criado automaticamente)
├── 📁 temp_files/             # Arquivos temporários (criado automaticamente)
├── 📁 certificates/            # Certificados (criado automaticamente)
└── 📁 keys/                    # Chaves (criado automaticamente)
```

## 🔧 Configurações do Serviço

### **Nome do Serviço**
- **Nome**: `AssinadorPDF`
- **Display**: `Assinador de PDFs`
- **Descrição**: `Sistema de Assinatura Digital de PDFs - Producao`

### **Configurações Técnicas**
- **Porta**: `5001`
- **Workers**: `2` (baseado em CPU)
- **Auto-restart**: `Sim`
- **Logs**: Rotação automática a 10MB
- **Firewall**: Configurado automaticamente

### **Variáveis de Ambiente**
```env
PYTHONUNBUFFERED=1
FLASK_CONFIG=production
PORT=5001
```

## 🚀 Comandos de Gerenciamento

### **Instalar Serviço**
```cmd
# Execute como Administrador
install_service.bat
```

### **Remover Serviço**
```cmd
# Execute como Administrador
uninstall_service.bat
```

### **Comandos Manuais**
```cmd
# Parar serviço
sc stop AssinadorPDF

# Iniciar serviço
sc start AssinadorPDF

# Status do serviço
sc query AssinadorPDF

# Remover serviço
sc delete AssinadorPDF
```

## 📊 Monitoramento

### **Logs do Sistema**
- **Localização**: `C:\AssinadorPDF\logs\`
- **Arquivos**:
  - `service.log` - Log geral do serviço
  - `error.log` - Log de erros

### **Verificar Status**
```cmd
# Status do serviço
sc query AssinadorPDF

# Verificar porta
netstat -an | find "5001"

# Testar aplicação
curl http://localhost:5001
```

### **Logs de Performance**
- Requests > 1s são logados automaticamente
- Métricas por tipo de dispositivo
- Cache hit/miss rates

## 🔒 Segurança

### **Firewall**
- Porta 5001 liberada automaticamente
- Regra: `AssinadorPDF-5001`

### **Certificados**
- Certificados auto-assinados gerados automaticamente
- Localização: `certificates/`
- Validade: 5 anos

### **Banco de Dados**
- SQLite por padrão
- Localização: `instance/assinador.db`
- Backup recomendado

## 🌐 Acesso

### **URLs de Acesso**
- **Principal**: `http://localhost:5001`
- **Login**: `http://localhost:5001/login`
- **Admin**: `http://localhost:5001/admin`

### **Usuários Padrão**
- **Admin**: Criado via script de inicialização
- **Senha**: Definida na primeira execução

## 🛠️ Troubleshooting

### **Problemas Comuns**

#### 1. **Serviço não inicia**
```cmd
# Verificar logs
type C:\AssinadorPDF\logs\error.log

# Verificar dependências
uv pip install -r requirements.txt

# Verificar porta
netstat -an | find "5001"
```

#### 2. **Erro de dependências**
```cmd
# Reinstalar dependências
uv pip install -r requirements.txt

# Verificar Python
python --version
```

#### 3. **Porta ocupada**
```cmd
# Verificar processo na porta
netstat -ano | find "5001"

# Matar processo (substitua PID)
taskkill /PID <PID> /F
```

#### 4. **Permissões**
```cmd
# Verificar permissões da pasta
icacls C:\AssinadorPDF

# Dar permissões completas
icacls C:\AssinadorPDF /grant Everyone:F /T
```

### **Logs de Debug**
```cmd
# Executar em modo debug
cd C:\AssinadorPDF
uv run python app.py
```

## 📈 Performance

### **Otimizações Implementadas**
- ✅ Cache inteligente (3-10 minutos)
- ✅ Compressão automática
- ✅ Detecção de dispositivos
- ✅ Queries otimizadas
- ✅ Headers de performance

### **Métricas Esperadas**
- **Tempo de carregamento**: 1-2s
- **Uso de memória**: Otimizado
- **Requests lentos**: < 5%
- **Cache hit rate**: > 80%

## 🔄 Atualizações

### **Atualizar Código**
```cmd
# 1. Parar serviço
sc stop AssinadorPDF

# 2. Fazer backup
xcopy C:\AssinadorPDF C:\AssinadorPDF_backup /E /I

# 3. Atualizar arquivos
# (copiar novos arquivos)

# 4. Reinstalar dependências
uv pip install -r requirements.txt

# 5. Reiniciar serviço
sc start AssinadorPDF
```

### **Backup**
```cmd
# Backup completo
xcopy C:\AssinadorPDF C:\Backup_AssinadorPDF_%date% /E /I

# Backup apenas banco
copy C:\AssinadorPDF\instance\assinador.db C:\Backup_assinador_%date%.db
```

## 📞 Suporte

### **Verificações Básicas**
1. ✅ Serviço rodando: `sc query AssinadorPDF`
2. ✅ Porta aberta: `netstat -an | find "5001"`
3. ✅ Logs sem erro: `type logs\error.log`
4. ✅ Aplicação acessível: `http://localhost:5001`

### **Contatos**
- **Logs**: `C:\AssinadorPDF\logs\`
- **Configurações**: `config.py`
- **Banco**: `instance\assinador.db`

---

## 🎉 **Sistema Pronto para Produção!**

Após seguir este guia, o sistema estará:
- ✅ Rodando como serviço Windows
- ✅ Iniciando automaticamente
- ✅ Otimizado para tablets/mobile
- ✅ Monitorado e com logs
- ✅ Seguro e configurado

**URL de Acesso**: `http://localhost:5001`
