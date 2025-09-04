# 🔄 Sistema de Atualização do Banco de Dados

## 📋 Visão Geral

Este sistema permite atualizar o banco de dados existente para incluir as novas funcionalidades de auditoria, sem perder dados existentes.

## 🚀 Comandos Disponíveis

### 1. Verificar Status do Banco
```bash
python update_database.py info
```
**O que faz:**
- Mostra todas as colunas existentes na tabela `signatures`
- Conta o total de registros
- Verifica se as novas colunas de auditoria estão presentes
- Identifica colunas pendentes (se houver)

### 2. Atualizar o Banco
```bash
python update_database.py update
```
**O que faz:**
- Adiciona todas as novas colunas necessárias
- Define valores padrão para colunas existentes
- Preserva todos os dados existentes
- Executa de forma segura com rollback em caso de erro

### 3. Ajuda
```bash
python update_database.py help
```
**O que faz:**
- Mostra todos os comandos disponíveis
- Explica o propósito de cada funcionalidade

## 🆕 Novas Colunas Adicionadas

### 📝 Informações do Cliente/Assinante
- `client_name` - Nome completo do cliente
- `client_cpf` - CPF do cliente (formato: 000.000.000-00)
- `client_email` - Email do cliente
- `client_phone` - Telefone do cliente
- `client_birth_date` - Data de nascimento
- `client_address` - Endereço completo

### 💻 Informações do Dispositivo
- `ip_address` - Endereço IP do cliente
- `mac_address` - Endereço MAC (quando disponível)
- `user_agent` - String completa do User-Agent
- `browser_name` - Nome do navegador
- `browser_version` - Versão do navegador
- `operating_system` - Sistema operacional
- `device_type` - Tipo de dispositivo (desktop, mobile, tablet)
- `screen_resolution` - Resolução da tela
- `timezone` - Fuso horário do cliente

### 🌍 Informações de Localização
- `location_country` - País (quando disponível)
- `location_city` - Cidade (quando disponível)
- `location_latitude` - Latitude (quando disponível)
- `location_longitude` - Longitude (quando disponível)

### ✍️ Informações da Assinatura
- `signature_method` - Método usado (drawing, digital, etc.)
- `signature_duration` - Tempo para assinar (em segundos)
- `verification_status` - Status da verificação
- `verification_notes` - Notas adicionais

### 📅 Auditoria
- `created_at` - Data/hora de criação
- `updated_at` - Data/hora da última atualização

## 🔧 Como Funciona

### 1. **Verificação Segura**
- O script verifica se a tabela existe antes de fazer alterações
- Não executa se o banco não estiver inicializado

### 2. **Adição Incremental**
- Adiciona apenas colunas que não existem
- Não duplica colunas existentes
- Preserva estrutura atual

### 3. **Valores Padrão**
- Define valores padrão para colunas existentes
- Garante compatibilidade com registros antigos

### 4. **Transação Segura**
- Todas as alterações são feitas em uma transação
- Rollback automático em caso de erro
- Commit apenas após sucesso total

## 📊 Exemplo de Saída

```bash
$ python update_database.py info

📊 Informações do Banco de Dados:
==================================================
📋 Tabela 'signatures':
   Total de colunas: 34

   Colunas:
     id: INTEGER NOT NULL (PK)
     user_id: INTEGER NOT NULL
     file_id: VARCHAR(255) NOT NULL
     original_filename: VARCHAR(255) NOT NULL
     signature_hash: VARCHAR(255) NOT NULL
     signature_algorithm: VARCHAR(50) NOT NULL
     timestamp: DATETIME
     file_size: INTEGER
     signature_valid: BOOLEAN
     client_name: VARCHAR(255)
     client_cpf: VARCHAR(14)
     client_email: VARCHAR(255)
     client_phone: VARCHAR(20)
     client_birth_date: DATE
     client_address: TEXT
     ip_address: VARCHAR(45)
     mac_address: VARCHAR(17)
     user_agent: TEXT
     browser_name: VARCHAR(50)
     browser_version: VARCHAR(20)
     operating_system: VARCHAR(100)
     device_type: VARCHAR(20)
     screen_resolution: VARCHAR(20)
     timezone: VARCHAR(50)
     location_country: VARCHAR(100)
     location_city: VARCHAR(100)
     location_latitude: FLOAT
     location_longitude: FLOAT
     signature_method: VARCHAR(20)
     signature_duration: INTEGER
     verification_status: VARCHAR(20)
     verification_notes: TEXT
     created_at: DATETIME
     updated_at: DATETIME

   Total de registros: 0

✅ Todas as colunas de auditoria estão presentes!
```

## ⚠️ Importante

### ✅ **Antes de Executar:**
1. Certifique-se de que o banco foi inicializado (`python init_db.py`)
2. Faça backup do banco se houver dados importantes
3. Pare a aplicação Flask se estiver rodando

### 🔒 **Segurança:**
- O script é seguro e não remove dados existentes
- Todas as operações são reversíveis
- Rollback automático em caso de erro

### 📈 **Performance:**
- Adição de colunas é rápida no SQLite
- Não bloqueia o banco durante a operação
- Compatível com bancos grandes

## 🚨 Solução de Problemas

### Erro: "Banco não encontrado"
```bash
❌ Banco de dados não encontrado em: instance/assinador.db
```
**Solução:** Execute primeiro `python init_db.py`

### Erro: "Tabela não encontrada"
```bash
❌ Tabela 'signatures' não encontrada
```
**Solução:** Execute primeiro `python init_db.py`

### Erro: "Coluna já existe"
```bash
ℹ️ Coluna client_name já existe
```
**Solução:** Normal, a coluna já foi adicionada anteriormente

## 🎯 Resultado Esperado

Após executar `python update_database.py update`:

1. ✅ **34 colunas** na tabela `signatures`
2. ✅ **Todas as funcionalidades de auditoria** disponíveis
3. ✅ **Relatórios administrativos** funcionando
4. ✅ **Coleta de dados do dispositivo** ativa
5. ✅ **Sistema de assinatura** com fluxo completo

## 🔄 Próximos Passos

1. **Execute a atualização:** `python update_database.py update`
2. **Verifique o status:** `python update_database.py info`
3. **Teste a aplicação:** `python app.py`
4. **Acesse os relatórios:** `/admin/reports`

---

**🎉 Sistema de auditoria completo e funcional!**
