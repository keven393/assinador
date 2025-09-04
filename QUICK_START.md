# 🚀 Início Rápido - Assinador de PDFs

## ⚡ Instalação em 3 Passos

### 1. Clone e Entre no Diretório
```bash
git clone <url-do-repositorio>
cd Assinaturas
```

### 2. Instale as Dependências
**Windows:**
```bash
install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Manual:**
```bash
pip install -r requirements.txt
python init_db.py
```

### 3. Execute a Aplicação
```bash
python app.py
```

Acesse: **http://localhost:5000**

## 👤 Primeiro Acesso

### Usuário Administrador Padrão
- **Usuário**: `admin`
- **Senha**: `admin123`
- **⚠️ IMPORTANTE**: Altere a senha após o primeiro login!

## 🔒 **Política de Usuários**

- **Novos usuários** devem ser criados por administradores
- **Não há registro público** - apenas login com contas existentes  
- **Contate o administrador** para solicitar uma conta

## 🔐 Funcionalidades Principais

### Para Usuários Normais
1. **Login** - Acesse o sistema (conta criada por administrador)
2. **Assinar PDFs** - Upload, desenhar assinatura, processar
3. **Perfil** - Visualizar histórico e alterar senha
4. **Verificar Assinaturas** - Validar documentos

### Para Administradores
1. **Dashboard** - Estatísticas em tempo real
2. **Gerenciar Usuários** - Criar, editar, deletar contas
3. **Relatórios** - Dados detalhados com filtros
4. **Exportar Dados** - Dados em formato JSON

## 📱 Interface Web

- **Responsiva** - Funciona em desktop e mobile
- **Moderno** - Design com Bootstrap 5 e Font Awesome
- **Intuitiva** - Navegação clara e feedback visual
- **Segura** - Proteção CSRF e validação de entrada

## 🛡️ Segurança

- **Senhas**: Hash bcrypt com salt único
- **Sessões**: Expiração automática em 24h
- **Permissões**: Controle granular por função
- **Validação**: Todos os formulários validados

## 🔧 Configuração

### Variáveis de Ambiente
Copie `env_example.txt` para `.env` e ajuste:

```bash
FLASK_CONFIG=development
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=sqlite:///assinador.db
```

### Personalização
- **Logo**: Substitua `static/images/logo.png`
- **Cores**: Modifique CSS em `templates/`
- **Configurações**: Ajuste `config.py`

## 🚨 Solução de Problemas

### Erro de Banco
```bash
rm assinador.db
python init_db.py
```

### Erro de Dependências
```bash
pip install --upgrade -r requirements.txt
```

### Problemas de Permissão
- Verifique acesso de escrita nas pastas
- Certifique-se que as chaves estão acessíveis

## 📞 Suporte

- **Issues**: Abra no repositório
- **Documentação**: Consulte `README.md`
- **Logs**: Verifique `assinador.log`

---

**🎯 Pronto para usar! O sistema está configurado e funcionando.**
