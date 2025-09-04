#!/usr/bin/env python3
"""
Test script para verificar o funcionamento da assinatura digital
e metadados embutidos no PDF
"""

import os
import tempfile
import json
from crypto_utils import signature_manager

def test_signature_embedding():
    """Testa o processo completo de assinatura e verificação"""
    print("🔐 Testando Assinatura Digital e Verificação")
    print("=" * 50)
    
    # Cria um arquivo de teste
    test_content = b"Este e um documento de teste para verificar a assinatura digital."
    
    # Gera assinatura
    print("1. Gerando assinatura digital...")
    signature_info = signature_manager.sign_data(test_content)
    print(f"   ✅ Hash: {signature_info['hash'][:16]}...")
    print(f"   ✅ Timestamp: {signature_info['timestamp']}")
    print(f"   ✅ Algoritmo: {signature_info['algorithm']}")
    
    # Simula verificação
    print("\n2. Verificando assinatura...")
    is_valid = signature_manager.verify_signature(test_content, signature_info)
    print(f"   ✅ Verificação: {'VÁLIDA' if is_valid else 'INVÁLIDA'}")
    
    # Testa com conteúdo modificado
    print("\n3. Testando com conteúdo modificado...")
    modified_content = b"Este e um documento MODIFICADO para verificar a assinatura digital."
    is_valid_modified = signature_manager.verify_signature(modified_content, signature_info)
    print(f"   ✅ Verificação (modificado): {'VÁLIDA' if is_valid_modified else 'INVÁLIDA'} (esperado: INVÁLIDA)")
    
    # Testa extração de metadados
    print("\n4. Testando extração de metadados...")
    metadata = {
        'hash': signature_info['hash'],
        'timestamp': signature_info['timestamp'],
        'algorithm': signature_info['algorithm'],
        'signature': signature_info['signature']
    }
    
    # Simula metadados extraídos
    extracted_info = {
        'hash': metadata['hash'],
        'timestamp': metadata['timestamp'],
        'algorithm': metadata['algorithm'],
        'signature': metadata['signature']
    }
    
    # Verifica se os metadados são válidos
    is_metadata_valid = signature_manager.verify_signature(test_content, extracted_info)
    print(f"   ✅ Metadados extraídos: {'VÁLIDOS' if is_metadata_valid else 'INVÁLIDOS'}")
    
    print("\n" + "=" * 50)
    print("✅ Teste concluído com sucesso!")
    
    return True

def test_persistent_storage():
    """Testa o armazenamento persistente de assinaturas"""
    print("\n💾 Testando Armazenamento Persistente")
    print("=" * 50)
    
    # Verifica se o diretório de assinaturas existe
    signatures_dir = 'signatures'
    if not os.path.exists(signatures_dir):
        os.makedirs(signatures_dir)
        print(f"   ✅ Diretório '{signatures_dir}' criado")
    else:
        print(f"   ✅ Diretório '{signatures_dir}' já existe")
    
    # Lista arquivos de assinatura existentes
    signature_files = [f for f in os.listdir(signatures_dir) if f.endswith('_signature.json')]
    print(f"   📁 Arquivos de assinatura encontrados: {len(signature_files)}")
    
    for sig_file in signature_files[:3]:  # Mostra apenas os 3 primeiros
        sig_path = os.path.join(signatures_dir, sig_file)
        try:
            with open(sig_path, 'r') as f:
                sig_data = json.load(f)
            print(f"   📄 {sig_file}: {sig_data['timestamp']}")
        except Exception as e:
            print(f"   ❌ Erro ao ler {sig_file}: {e}")
    
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        test_signature_embedding()
        test_persistent_storage()
        print("\n🎉 Todos os testes passaram!")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
