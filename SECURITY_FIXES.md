# Correções de Segurança Implementadas

Este documento descreve as correções de segurança críticas implementadas no sistema.

## 1. ✅ Injeção LDAP (Crítica) - CORRIGIDO

**Arquivo:** `services/ldap_service.py`

**Problema:** O código construía filtros LDAP concatenando strings diretamente, permitindo injeção de filtros maliciosos.

**Correção:**
- Adicionado import de `escape_filter_chars` da biblioteca `ldap3`
- Implementado escape de caracteres especiais LDAP no método `_search_user` antes de formatar o filtro
- O username agora é sanitizado antes de ser inserido na query LDAP

**Código alterado:**
```python
from ldap3.utils.conv import escape_filter_chars

# No método _search_user:
escaped_username = escape_filter_chars(username)
search_filter = self.user_search_filter.format(username=escaped_username)
```

## 2. ✅ Quebra de Integridade na Validação de PDF (Crítica) - CORRIGIDO

**Arquivo:** `services/pdf_validator.py`

**Problema:** O sistema "sincronizava automaticamente" o hash quando detectava diferença, aceitando arquivos adulterados.

**Correção:**
- Removida a lógica de auto-sincronização
- Arquivos com hash diferente são marcados como INVÁLIDOS imediatamente
- Adicionado alerta de segurança quando hash mismatch é detectado
- Erro é registrado no resultado da validação

**Impacto:** Arquivos adulterados não são mais aceitos automaticamente pelo sistema.

## 3. ✅ Uso Inseguro de Arquivos Temporários (Race Condition) - CORRIGIDO

**Arquivo:** `app.py` (linhas 2765 e 3565)

**Problema:** Uso de `tempfile.mktemp()` que cria uma janela de tempo onde um atacante pode criar o arquivo antes da aplicação.

**Correção:**
- Substituído `tempfile.mktemp()` por `tempfile.mkstemp()`
- `mkstemp()` cria o arquivo atomicamente e retorna um descritor seguro
- Descritor é fechado imediatamente, mas o arquivo permanece para uso posterior

**Código alterado:**
```python
# Antes:
output_path = tempfile.mktemp(suffix='.pdf')

# Depois:
fd, output_path = tempfile.mkstemp(suffix='.pdf')
os.close(fd)  # Fecha o descritor, mantém o arquivo
```

## 4. ✅ Gerenciamento de Chaves Criptográficas - MELHORADO

**Arquivo:** `utils/crypto_utils.py`

**Problema:** Chaves privadas armazenadas sem criptografia no sistema de arquivos.

**Correção:**
- Adicionado suporte para chaves privadas criptografadas com passphrase
- Nova variável de ambiente: `PRIVATE_KEY_PASSPHRASE`
- Se a passphrase for fornecida, a chave privada é criptografada usando `BestAvailableEncryption`
- Chaves existentes continuam funcionando (backward compatible)
- Chaves novas serão criptografadas se `PRIVATE_KEY_PASSPHRASE` estiver definida

**Configuração:**
```bash
# Adicione ao .env em produção:
PRIVATE_KEY_PASSPHRASE=your_strong_passphrase_here
```

**Recomendação:** Use uma passphrase forte e armazene de forma segura (gerenciador de senhas).

## 5. ✅ Risco de DoS (Negação de Serviço) via Upload - MITIGADO

**Arquivo:** `app.py` - função `scan_pdf_safeness`

**Problema:** PDFs complexos ou com muitas páginas podiam causar DoS consumindo recursos excessivos.

**Correção:**
- Adicionado limite máximo de páginas: **1000 páginas**
- Implementado timeout de **30 segundos** para processamento
- PDFs que excedem os limites são rejeitados com mensagem clara
- Timeout funciona em sistemas Unix/Linux (signal.SIGALRM)

**Limites implementados:**
- `MAX_PAGES = 1000`
- `TIMEOUT_SECONDS = 30`

## 6. ✅ Exposição de Dados Sensíveis (LGPD/Privacidade) - MITIGADO

**Arquivo:** `audit_logger.py`

**Problema:** Dados pessoais sensíveis (CPF, email, telefone, endereço) eram logados em texto plano.

**Correção:**
- Implementada função `mask_sensitive_data()` que mascara dados sensíveis
- CPF: `123.456.789-00` → `123.***.***-**`
- Email: `user@example.com` → `u***@example.com`
- Telefone: `(11) 98765-4321` → `*******4321`
- Senhas, endereços e dados de assinatura são completamente mascarados
- Função aplicada automaticamente em todos os logs de auditoria

**Campos mascarados:**
- CPF (client_cpf, signer_cpf, etc.)
- Senhas (password, password_hash, etc.)
- Emails (client_email, signer_email, etc.)
- Telefones (phone, mobile, telephone, etc.)
- Endereços (address, street_address, etc.)
- Dados de assinatura (signature_data, signature_image)

**Nota:** A criptografia de colunas no banco de dados requer uma mudança arquitetural maior (ex: SQLAlchemy encryption extensions ou database-level encryption). A mitigação de logs é o primeiro passo crítico para conformidade LGPD.

---

## Resumo das Mudanças

| Vulnerabilidade | Status | Arquivo(s) Afetado(s) |
|----------------|--------|----------------------|
| Injeção LDAP | ✅ Corrigido | `services/ldap_service.py` |
| Validação de Integridade PDF | ✅ Corrigido | `services/pdf_validator.py` |
| Race Condition (tempfile) | ✅ Corrigido | `app.py` |
| Gerenciamento de Chaves | ✅ Melhorado | `utils/crypto_utils.py` |
| DoS via Upload | ✅ Mitigado | `app.py` |
| Exposição de Dados (Logs) | ✅ Mitigado | `audit_logger.py` |

## Próximos Passos Recomendados

1. **Criptografia de Banco de Dados:**
   - Considerar criptografia de colunas sensíveis (especialmente CPF) no banco de dados
   - Avaliar uso de SQLAlchemy encryption extensions ou database-level encryption

2. **HSM/KMS para Chaves:**
   - Em ambientes de alta segurança, considerar migração para HSM (Hardware Security Module) ou KMS (Key Management Service)

3. **Testes de Segurança:**
   - Realizar testes de penetração para validar as correções
   - Testar cenários de ataque LDAP injection
   - Validar limites de DoS em ambiente de teste

4. **Monitoramento:**
   - Implementar alertas para tentativas de injeção LDAP
   - Monitorar tentativas de upload de PDFs maliciosos
   - Alertar sobre hash mismatches em validações

## Configuração de Produção

Certifique-se de configurar as seguintes variáveis de ambiente em produção:

```bash
# Criptografia de chave privada (recomendado)
PRIVATE_KEY_PASSPHRASE=your_strong_passphrase_here

# Diretório seguro para chaves (opcional, mas recomendado)
KEYS_DIR_SECURE=/secure/path/to/keys
```

---

**Data das Correções:** 2024
**Versão:** Todas as vulnerabilidades críticas corrigidas

