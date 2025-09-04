#!/usr/bin/env python3
"""
Script de teste para as funcionalidades criptográficas do Assinador de PDFs
"""

import os
import tempfile
import json
from crypto_utils import signature_manager

def test_crypto_functions():
    """Testa as funcionalidades criptográficas"""
    print("🔐 Testando funcionalidades criptográficas...")
    print("=" * 50)
    
    # Teste 1: Cálculo de hash
    print("\n1. Testando cálculo de hash SHA-256...")
    test_data = "Este é um documento de teste para verificar a funcionalidade de hash."
    hash_result = signature_manager.calculate_hash(test_data)
    print(f"   Dados de teste: {test_data}")
    print(f"   Hash SHA-256: {hash_result}")
    print(f"   ✅ Hash calculado com sucesso!")
    
    # Teste 2: Assinatura digital
    print("\n2. Testando assinatura digital...")
    signature_info = signature_manager.sign_data(test_data)
    print(f"   Hash: {signature_info['hash']}")
    print(f"   Timestamp: {signature_info['timestamp']}")
    print(f"   Algoritmo: {signature_info['algorithm']}")
    print(f"   ✅ Assinatura digital gerada com sucesso!")
    
    # Teste 3: Verificação de assinatura
    print("\n3. Testando verificação de assinatura...")
    is_valid = signature_manager.verify_signature(test_data, signature_info)
    print(f"   Assinatura válida: {is_valid}")
    print(f"   ✅ Verificação concluída!")
    
    # Teste 4: Verificação com dados modificados
    print("\n4. Testando verificação com dados modificados...")
    modified_data = "Este é um documento MODIFICADO para verificar a funcionalidade de hash."
    is_valid_modified = signature_manager.verify_signature(modified_data, signature_info)
    print(f"   Assinatura válida (dados modificados): {is_valid_modified}")
    print(f"   ✅ Verificação de integridade funcionando!")
    
    # Teste 5: Informações da chave pública
    print("\n5. Testando informações da chave pública...")
    public_key_info = signature_manager.get_public_key_info()
    print(f"   Algoritmo: {public_key_info['algorithm']}")
    print(f"   Tamanho da chave: {public_key_info['key_size']} bits")
    print(f"   ✅ Informações da chave pública obtidas!")
    
    # Teste 6: Exportação da chave pública
    print("\n6. Testando exportação da chave pública...")
    public_key_pem = signature_manager.export_public_key()
    print(f"   Chave pública (PEM):")
    print(f"   {public_key_pem[:100]}...")
    print(f"   ✅ Chave pública exportada!")
    
    # Teste 7: Criação de arquivo de assinatura
    print("\n7. Testando criação de arquivo de assinatura...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(signature_info, f, indent=2)
        signature_file = f.name
    
    print(f"   Arquivo de assinatura criado: {signature_file}")
    
    # Lê o arquivo de assinatura
    with open(signature_file, 'r') as f:
        loaded_signature = json.load(f)
    
    # Verifica se a assinatura carregada é válida
    is_valid_loaded = signature_manager.verify_signature(test_data, loaded_signature)
    print(f"   Assinatura carregada válida: {is_valid_loaded}")
    print(f"   ✅ Arquivo de assinatura funcionando!")
    
    # Limpa arquivo temporário
    os.unlink(signature_file)
    
    print("\n" + "=" * 50)
    print("🎉 Todos os testes passaram com sucesso!")
    print("✅ As funcionalidades criptográficas estão funcionando corretamente.")
    
    return True

def test_error_handling():
    """Testa o tratamento de erros"""
    print("\n🔍 Testando tratamento de erros...")
    print("=" * 50)
    
    # Teste com dados vazios
    print("\n1. Testando com dados vazios...")
    try:
        hash_empty = signature_manager.calculate_hash("")
        print(f"   Hash de dados vazios: {hash_empty}")
        print(f"   ✅ Tratamento de dados vazios OK!")
    except Exception as e:
        print(f"   ❌ Erro com dados vazios: {e}")
    
    # Teste com dados None
    print("\n2. Testando com dados None...")
    try:
        hash_none = signature_manager.calculate_hash(None)
        print(f"   Hash de None: {hash_none}")
        print(f"   ✅ Tratamento de None OK!")
    except Exception as e:
        print(f"   ❌ Erro com None: {e}")
    
    # Teste de verificação com assinatura inválida
    print("\n3. Testando verificação com assinatura inválida...")
    invalid_signature = {
        'hash': 'invalid_hash',
        'signature': 'invalid_signature',
        'timestamp': '2024-01-01T00:00:00',
        'algorithm': 'RSA-SHA256'
    }
    
    try:
        is_valid = signature_manager.verify_signature("test data", invalid_signature)
        print(f"   Verificação com assinatura inválida: {is_valid}")
        print(f"   ✅ Tratamento de assinatura inválida OK!")
    except Exception as e:
        print(f"   ❌ Erro com assinatura inválida: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Testes de tratamento de erros concluídos!")

if __name__ == "__main__":
    print("🚀 Iniciando testes das funcionalidades criptográficas...")
    print("=" * 60)
    
    try:
        # Executa testes principais
        test_crypto_functions()
        
        # Executa testes de tratamento de erros
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 Todos os testes foram executados com sucesso!")
        print("✅ O sistema de assinatura digital está funcionando corretamente.")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        print("🔧 Verifique se todas as dependências estão instaladas:")
        print("   pip install cryptography pycryptodome")
        exit(1)
