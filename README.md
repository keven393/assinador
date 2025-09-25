# 🚀 Assinador de PDFs - Sistema de Produção

Sistema completo de assinatura digital de documentos PDF com interface web responsiva, otimizado para tablets e dispositivos móveis.

## ✨ Funcionalidades

- 📄 **Upload e Assinatura** de arquivos PDF
- ✍️ **Assinatura Digital** com desenho em canvas
- 🔍 **Validação** de assinaturas digitais
- 👥 **Interface Administrativa** completa
- 📊 **Relatórios e Estatísticas** detalhadas
- 📱 **Otimizado para Mobile/Tablet**
- 🚀 **Performance** otimizada para produção

## 🛠️ Instalação Rápida

### **Para Produção (Recomendado)**
```cmd
# 1. Execute como Administrador
install_service.bat

# 2. Verifique o sistema
check_system.bat

# 3. Acesse: http://localhost:5001
```

### **Para Desenvolvimento**
```cmd
# 1. Instalar dependências
uv pip install -r requirements.txt

# 2. Executar aplicação
uv run python app.py
```

## 📁 Estrutura do Projeto

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
├── 🎯 check_system.bat          # Verificação do sistema
├── 📁 templates/               # Templates HTML
├── 📁 static/                  # Arquivos estáticos
└── 📖 DEPLOY_GUIDE.md          # Guia completo de deploy
```

## 🚀 Scripts Disponíveis

| Script | Descrição |
|--------|-----------|
| `install_service.bat` | Instala o serviço Windows |
| `uninstall_service.bat` | Remove o serviço Windows |
| `check_system.bat` | Verifica status do sistema |

## 🌐 Acesso

- **Principal**: http://localhost:5001
- **Login**: http://localhost:5001/login
- **Admin**: http://localhost:5001/admin

## 🔧 Comandos de Gerenciamento

```cmd
# Status do serviço
sc query AssinadorPDF

# Parar serviço
sc stop AssinadorPDF

# Iniciar serviço
sc start AssinadorPDF

# Remover serviço
sc delete AssinadorPDF
```

## 📊 Monitoramento

- **Logs**: `logs/service.log` e `logs/error.log`
- **Performance**: Otimizada para tablets/mobile
- **Cache**: Inteligente baseado no dispositivo
- **Compressão**: Automática para mobile

## 🔒 Segurança

- ✅ Certificados digitais auto-assinados
- ✅ Criptografia RSA-SHA256
- ✅ Validação de integridade
- ✅ Firewall configurado automaticamente

## 📱 Otimizações Mobile

- **Detecção inteligente** de dispositivos
- **Cache adaptativo** (3-10 minutos)
- **Compressão automática** para mobile
- **Queries otimizadas** por dispositivo
- **Headers de performance** específicos

## 🛠️ Troubleshooting

### **Verificar Sistema**
```cmd
check_system.bat
```

### **Logs de Erro**
```cmd
type logs\error.log
```

### **Reinstalar Serviço**
```cmd
uninstall_service.bat
install_service.bat
```

## 📚 Documentação

- **Guia Completo**: `DEPLOY_GUIDE.md`
- **Configurações**: `config.py`
- **Otimizações**: `mobile_optimizations.py`

## 🎯 Requisitos

- **Windows Server 2016+** ou **Windows 10/11**
- **UV** (gerenciador de pacotes - instala Python automaticamente)
- **NSSM** (instalado e no PATH)
- **Acesso de Administrador**

## 🎉 **Sistema Pronto para Produção!**

Após a instalação, o sistema estará:
- ✅ Rodando como serviço Windows
- ✅ Iniciando automaticamente
- ✅ Otimizado para tablets/mobile
- ✅ Monitorado e com logs
- ✅ Seguro e configurado

**URL de Acesso**: http://localhost:5001

---

## 📋 Funcionalidades Detalhadas

### Sistema de Autenticação
- **Login/Logout** com sessões seguras
- **Apenas Administradores** podem criar novas contas de usuário
- **Controle de permissões** (Usuário normal vs Administrador)
- **Gerenciamento de perfis** com alteração de senha
- **Sessões com expiração** automática

### Assinatura de PDFs
- **Assinatura digital** com certificado X.509
- **Assinatura desenhada** com canvas interativo
- **Múltiplas opções** de posicionamento da assinatura
- **Verificação de integridade** dos documentos
- **Metadados embutidos** para rastreabilidade

### Painel Administrativo
- **Dashboard** com estatísticas em tempo real
- **Gerenciamento de usuários** (criar, editar, deletar)
- **Relatórios detalhados** com filtros
- **Exportação de dados** em formato JSON
- **Monitoramento de atividade** do sistema

## 🏗️ Tecnologias Utilizadas

- **Backend**: Flask (Python) + ASGI (Uvicorn)
- **Banco de Dados**: SQLite com SQLAlchemy
- **Autenticação**: Flask-Login com bcrypt
- **Frontend**: Bootstrap 5 + Font Awesome
- **Criptografia**: PyCryptodome + Cryptography
- **PDF**: PyPDF2 + ReportLab
- **Cache**: Flask-Caching
- **Compressão**: Flask-Compress

## 👤 Usuários Padrão

### Administrador
- **Usuário**: `admin`
- **Senha**: `admin123`
- **⚠️ IMPORTANTE**: Altere a senha padrão após o primeiro login!

## 🔐 Estrutura de Usuários

### Usuário Normal
- Acesso ao sistema de assinatura
- Visualização do próprio perfil
- Histórico de assinaturas pessoais

### Administrador
- Todas as funcionalidades do usuário normal
- Painel administrativo completo
- Gerenciamento de usuários
- Relatórios e estatísticas
- Exportação de dados

## 📱 Como Usar

### 1. Login
- Acesse a aplicação
- Faça login com suas credenciais
- Ou registre uma nova conta

### 2. Assinar PDF
- Faça upload do arquivo PDF
- Desenhe sua assinatura no canvas
- Preencha informações pessoais (opcional)
- Clique em "Assinar PDF"

### 3. Download
- Após a assinatura, o arquivo estará disponível para download
- O sistema gera um hash único para verificação

### 4. Verificar Assinatura
- Use a funcionalidade de verificação para validar documentos
- O sistema verifica integridade e autenticidade

## 🔒 Segurança

- **Senhas**: Hash bcrypt com salt único
- **Sessões**: Expiração automática em 8 horas (produção)
- **CSRF**: Proteção contra ataques Cross-Site Request Forgery
- **Validação**: Validação de entrada em todos os formulários
- **Permissões**: Controle granular de acesso por função

## 📊 Banco de Dados

### Tabelas Principais
- **users**: Informações dos usuários
- **signatures**: Registro de assinaturas
- **user_sessions**: Controle de sessões ativas

### Relacionamentos
- Usuário → Muitas assinaturas
- Usuário → Muitas sessões

## 🚨 Solução de Problemas

### Erro de Banco de Dados
```bash
# Recrie o banco de dados
rm instance/assinador.db
python init_db.py
```

### Erro de Dependências
```bash
# Atualize as dependências
uv pip install -r requirements.txt
```

### Problemas de Permissão
- Verifique se o usuário tem acesso de escrita nas pastas
- Certifique-se de que as chaves criptográficas estão acessíveis

## 🔄 Atualizações

### v3.0.0 (Produção)
- ✅ **Serviço Windows** com auto-start
- ✅ **Otimizações mobile/tablet** completas
- ✅ **Cache inteligente** baseado em dispositivo
- ✅ **Compressão automática** para mobile
- ✅ **Performance** otimizada para produção
- ✅ **Monitoramento** com logs detalhados
- ✅ **Firewall** configurado automaticamente

### v2.0.0
- ✅ Sistema de usuários e autenticação
- ✅ Controle de permissões
- ✅ Painel administrativo
- ✅ Relatórios e estatísticas
- ✅ Interface moderna e responsiva
- ✅ Rotina diária de limpeza com agendamento configurável

### v1.0.0
- ✅ Assinatura digital básica
- ✅ Verificação de integridade
- ✅ Suporte a certificados X.509

---

**Desenvolvido com ❤️ para facilitar a assinatura digital de documentos**