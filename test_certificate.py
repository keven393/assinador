#!/usr/bin/env python3
"""
Test script para verificar o funcionamento do certificado digital X.509
"""

import os
import tempfile
import json
from certificate_manager import certificate_manager

def test_certificate_functionality():
    """Testa o funcionamento completo do certificado digital"""
    print("🔐 Testando Certificado Digital X.509")
    print("=" * 50)
    
    # Testa informações do certificado
    print("1. Verificando informações do certificado...")
    cert_info = certificate_manager.get_certificate_info()
    if 'error' not in cert_info:
        print(f"   ✅ Emissor: {cert_info['issuer']}")
        print(f"   ✅ Assunto: {cert_info['subject']}")
        print(f"   ✅ Número de Série: {cert_info['serial_number']}")
        print(f"   ✅ Fingerprint SHA-256: {cert_info['fingerprint_sha256'][:16]}...")
    else:
        print(f"   ❌ Erro: {cert_info['error']}")
        return False
    
    # Testa status do certificado
    print("\n2. Verificando status do certificado...")
    status, message = certificate_manager.get_certificate_status()
    print(f"   ✅ Status: {status} - {message}")
    
    # Testa assinatura com certificado
    print("\n3. Testando assinatura com certificado...")
    test_content = b"Este e um documento de teste para verificar a assinatura digital com certificado X.509."
    
    signature_info = certificate_manager.sign_pdf_with_certificate(test_content)
    if signature_info:
        print(f"   ✅ Hash: {signature_info['hash'][:16]}...")
        print(f"   ✅ Timestamp: {signature_info['timestamp']}")
        print(f"   ✅ Formato: {signature_info['signature_format']}")
        print(f"   ✅ Certificado: {signature_info['certificate_subject']}")
    else:
        print("   ❌ Erro ao assinar com certificado")
        return False
    
    # Testa verificação da assinatura
    print("\n4. Testando verificação da assinatura...")
    is_valid, message = certificate_manager.verify_signature_with_certificate(test_content, signature_info)
    if is_valid:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        return False
    
    # Testa verificação com conteúdo modificado
    print("\n5. Testando verificação com conteúdo modificado...")
    modified_content = b"Este e um documento MODIFICADO para verificar a assinatura digital com certificado X.509."
    is_valid, message = certificate_manager.verify_signature_with_certificate(modified_content, signature_info)
    if not is_valid:
        print(f"   ✅ {message} (esperado para conteúdo modificado)")
    else:
        print(f"   ❌ Assinatura válida para conteúdo modificado (não esperado)")
        return False
    
    # Testa exportação do certificado
    print("\n6. Testando exportação do certificado...")
    cert_pem = certificate_manager.export_certificate_pem()
    if cert_pem and not cert_pem.startswith("Erro"):
        print(f"   ✅ Certificado exportado ({len(cert_pem)} caracteres)")
    else:
        print(f"   ❌ Erro ao exportar certificado: {cert_pem}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Todos os testes do certificado digital passaram!")
    return True

def test_certificate_files():
    """Verifica se os arquivos do certificado foram criados"""
    print("\n📁 Verificando arquivos do certificado...")
    
    files_to_check = [
        certificate_manager.private_key_path,
        certificate_manager.certificate_path,
        certificate_manager.certificate_chain_path
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {os.path.basename(file_path)} ({size} bytes)")
        else:
            print(f"   ❌ {os.path.basename(file_path)} não encontrado")
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 Iniciando testes do certificado digital X.509\n")
    
    # Testa criação dos arquivos
    if not test_certificate_files():
        print("❌ Falha na verificação dos arquivos do certificado")
        exit(1)
    
    # Testa funcionalidade
    if not test_certificate_functionality():
        print("❌ Falha nos testes de funcionalidade do certificado")
        exit(1)
    
    print("\n🎉 Todos os testes passaram com sucesso!")
    print("\n📋 Resumo:")
    print("   • Certificado X.509 auto-assinado gerado")
    print("   • Assinatura PKCS#7/CMS funcionando")
    print("   • Verificação de integridade funcionando")
    print("   • Exportação do certificado funcionando")
    print("\n🔐 O sistema está pronto para assinar PDFs com certificado digital!")
