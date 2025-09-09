# Assinador de PDFs com Sistema de Usuários

Sistema completo de assinatura digital de PDFs com controle de usuários, sessões e permissões administrativas.

## 🚀 Funcionalidades

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

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Banco de Dados**: SQLite com SQLAlchemy
- **Autenticação**: Flask-Login com bcrypt
- **Frontend**: Bootstrap 5 + Font Awesome
- **Criptografia**: PyCryptodome + Cryptography
- **PDF**: PyPDF2 + ReportLab

## 📋 Pré-requisitos

- Python 3.9 ou superior
- pip ou uv (gerenciador de pacotes)

## 🔧 Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd Assinaturas
```

### 2. Instale as dependências
```bash
# Usando uv (recomendado)
uv sync

# Ou usando pip
pip install -r requirements.txt
```

### 3. Inicialize o banco de dados
```bash
python init_db.py
```

### 4. Execute a aplicação
```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`
## ⚙️ Configuração via .env

Crie um arquivo `.env` (baseado em `env_example.txt`) para configurar a aplicação sem editar código.

Principais variáveis:

- `FLASK_CONFIG`: development | production | testing
- `FLASK_DEBUG`: True | False
- `SECRET_KEY`: chave secreta da aplicação
- `DATABASE_URL`: URL do banco (ex.: sqlite:///assinador.db)
- `LOG_LEVEL`: nível de log (INFO, DEBUG, WARNING, ...)
- `SESSION_COOKIE_SECURE`: True (produção HTTPS) | False
- `MAX_CONTENT_LENGTH`: limite de upload em bytes (padrão 50MB)

### Limpeza automática de arquivos

- `CLEANUP_TIME`: horário diário de limpeza no timezone definido (formato HH:MM). Ex.: `02:00`
- `CLEANUP_TZ`: timezone da limpeza. Ex.: `America/Sao_Paulo`
- `CLEANUP_INTERVAL` e `FILE_RETENTION`: intervalos em segundos (opcionais, legado)

O que a limpeza faz:
- Remove todos os arquivos da pasta `temp_files/`
- Remove todos os PDFs `*_TEMP.pdf` na pasta `pdf_assinados/`
- Mantém os PDFs `*_KEEP.pdf`

Observação: a limpeza roda em um thread daemon em background e é iniciada automaticamente no boot da aplicação.


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

## 🏗️ Estrutura do Projeto

```
Assinaturas/
├── app.py                 # Aplicação principal Flask
├── models.py              # Modelos do banco de dados
├── forms.py               # Formulários WTForms
├── auth.py                # Sistema de autenticação
├── init_db.py             # Inicialização do banco
├── crypto_utils.py        # Utilitários de criptografia
├── certificate_manager.py  # Gerenciamento de certificados
├── templates/             # Templates HTML
│   ├── index.html         # Página principal
│   ├── login.html         # Página de login
│   ├── register.html      # Página de registro
│   ├── profile.html       # Perfil do usuário
│   ├── change_password.html # Alteração de senha
│   └── admin/             # Templates administrativos
│       ├── dashboard.html # Dashboard admin
│       ├── users.html     # Gerenciar usuários
│       ├── new_user.html  # Criar usuário
│       ├── edit_user.html # Editar usuário
│       └── reports.html   # Relatórios
├── static/                # Arquivos estáticos
├── signatures/            # Armazenamento de assinaturas
├── temp_files/            # Arquivos temporários
└── keys/                  # Chaves criptográficas
```

## 🔒 Segurança

- **Senhas**: Hash bcrypt com salt único
- **Sessões**: Expiração automática em 24 horas
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
rm assinador.db
python init_db.py
```

### Erro de Dependências
```bash
# Atualize as dependências
uv sync --upgrade
```

### Problemas de Permissão
- Verifique se o usuário tem acesso de escrita nas pastas
- Certifique-se de que as chaves criptográficas estão acessíveis

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte ou dúvidas:
- Abra uma issue no repositório
- Entre em contato com a equipe de desenvolvimento

## 🔄 Atualizações

### v2.0.0
- ✅ Sistema de usuários e autenticação
- ✅ Controle de permissões
- ✅ Painel administrativo
- ✅ Relatórios e estatísticas
- ✅ Interface moderna e responsiva
 - ✅ Rotina diária de limpeza com agendamento configurável via `.env` (CLEANUP_TIME/CLEANUP_TZ)
 - ✅ Armazenamento de PDFs assinados em `pdf_assinados/` com retenção `_KEEP`/_`TEMP`

### v1.0.0
- ✅ Assinatura digital básica
- ✅ Verificação de integridade
- ✅ Suporte a certificados X.509

---

**Desenvolvido com ❤️ para facilitar a assinatura digital de documentos**
