#!/usr/bin/env python3
"""
Gerenciador de Certificados Digitais X.509
Implementa geração de certificados e assinatura PKCS#7/CMS para PDFs
"""

import os
import hashlib
import base64
import json
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import pkcs7
import tempfile

class CertificateManager:
    def __init__(self, certs_dir="certificates"):
        """Inicializa o gerenciador de certificados"""
        self.certs_dir = certs_dir
        self.private_key_path = os.path.join(certs_dir, "private_key.pem")
        self.certificate_path = os.path.join(certs_dir, "certificate.pem")
        self.certificate_chain_path = os.path.join(certs_dir, "certificate_chain.pem")
        
        # Cria diretório se não existir
        if not os.path.exists(certs_dir):
            os.makedirs(certs_dir)
        
        # Gera certificado se não existir
        if not self._certificate_exists():
            self._generate_self_signed_certificate()
    
    def _certificate_exists(self):
        """Verifica se o certificado já existe"""
        return (os.path.exists(self.private_key_path) and 
                os.path.exists(self.certificate_path))
    
    def _generate_self_signed_certificate(self):
        """Gera um certificado auto-assinado X.509"""
        print("🔐 Gerando certificado digital X.509...")
        
        # Gera chave privada RSA-2048
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Salva chave privada
        with open(self.private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Cria o certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Goiás"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Senador Canedo"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Prefeitura Municipal de Senador Canedo - SITEC - SISTEMA"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Sistema de Assinatura"),
            x509.NameAttribute(NameOID.COMMON_NAME, "assinador-pdf.local.sitec.senadorcanedo.go.gov.br"),
        ])
        
        # Validade: 5 anos
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime(2029, 12, 31, 23, 59, 59)  # Válido até 31/12/2029
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("assinador-pdf.local.sitec.senadorcanedo.go.gov.br"),
            ]),
            critical=False,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Salva certificado
        with open(self.certificate_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Cria cadeia de certificados (apenas o certificado raiz por enquanto)
        with open(self.certificate_chain_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("✅ Certificado digital X.509 gerado com sucesso!")
        print(f"   📁 Chave privada: {self.private_key_path}")
        print(f"   📁 Certificado: {self.certificate_path}")
        print(f"   📁 Cadeia: {self.certificate_chain_path}")
    
    def get_certificate_info(self):
        """Retorna informações do certificado"""
        try:
            with open(self.certificate_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            return {
                'subject': self._format_name(cert.subject),
                'issuer': self._format_name(cert.issuer),
                'serial_number': str(cert.serial_number),
                'not_valid_before': cert.not_valid_before.isoformat(),
                'not_valid_after': cert.not_valid_after.isoformat(),
                'fingerprint_sha256': cert.fingerprint(hashes.SHA256()).hex(),
                'fingerprint_sha1': cert.fingerprint(hashes.SHA1()).hex(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _format_name(self, name):
        """Formata um nome X.509 de forma legível"""
        try:
            parts = []
            for attr in name:
                if attr.oid == NameOID.COUNTRY_NAME:
                    parts.append(f"País: {attr.value}")
                elif attr.oid == NameOID.STATE_OR_PROVINCE_NAME:
                    parts.append(f"Estado: {attr.value}")
                elif attr.oid == NameOID.LOCALITY_NAME:
                    parts.append(f"Cidade: {attr.value}")
                elif attr.oid == NameOID.ORGANIZATION_NAME:
                    parts.append(f"Organização: {attr.value}")
                elif attr.oid == NameOID.ORGANIZATIONAL_UNIT_NAME:
                    parts.append(f"Unidade: {attr.value}")
                elif attr.oid == NameOID.COMMON_NAME:
                    parts.append(f"CN: {attr.value}")
                else:
                    parts.append(f"{attr.oid._name}: {attr.value}")
            
            return " | ".join(parts)
        except Exception as e:
            return str(name)
    
    def sign_pdf_with_certificate(self, pdf_content):
        """Assina o conteúdo do PDF usando certificado X.509 e PKCS#7"""
        try:
            # Carrega chave privada
            with open(self.private_key_path, "rb") as f:
                private_key = load_pem_private_key(f.read(), password=None, backend=default_backend())
            
            # Carrega certificado
            with open(self.certificate_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Calcula hash do conteúdo
            content_hash = hashlib.sha256(pdf_content).hexdigest()
            
            # Assina o hash com a chave privada
            signature = private_key.sign(
                pdf_content,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Informações da assinatura
            signature_info = {
                'hash': content_hash,
                'timestamp': datetime.now().isoformat(),
                'algorithm': 'SHA256',
                'certificate_subject': str(cert.subject),
                'certificate_issuer': str(cert.issuer),
                'certificate_serial': str(cert.serial_number),
                'certificate_fingerprint': cert.fingerprint(hashes.SHA256()).hex(),
                'signature_format': 'RSA-SHA256',
                'signature_data': base64.b64encode(signature).decode('utf-8')
            }
            
            return signature_info
            
        except Exception as e:
            print(f"Erro ao assinar com certificado: {e}")
            return None
    
    def verify_signature_with_certificate(self, pdf_content, signature_info):
        """Verifica assinatura usando certificado X.509"""
        try:
            # Carrega certificado
            with open(self.certificate_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Decodifica dados da assinatura
            signature_data = base64.b64decode(signature_info['signature_data'])
            
            # Verifica assinatura RSA
            public_key = cert.public_key()
            public_key.verify(
                signature_data,
                pdf_content,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Verifica se o hash do conteúdo atual corresponde ao original
            current_hash = hashlib.sha256(pdf_content).hexdigest()
            original_hash = signature_info['hash']
            
            if current_hash != original_hash:
                return False, "Hash do conteúdo não corresponde ao original"
            
            # Verifica se o certificado usado na assinatura é o esperado (se informado)
            expected_fp = signature_info.get('certificate_fingerprint')
            if expected_fp:
                current_fp = cert.fingerprint(hashes.SHA256()).hex()
                if expected_fp != current_fp:
                    return False, "Certificado usado na assinatura não corresponde ao esperado"
            
            return True, "Assinatura válida"
            
        except Exception as e:
            return False, f"Erro na verificação: {str(e)}"
    
    def export_certificate_pem(self):
        """Exporta certificado em formato PEM"""
        try:
            with open(self.certificate_path, "rb") as f:
                return f.read().decode('utf-8')
        except Exception as e:
            return f"Erro ao exportar certificado: {str(e)}"
    
    def export_certificate_der(self):
        """Exporta certificado em formato DER"""
        try:
            with open(self.certificate_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            return cert.public_bytes(serialization.Encoding.DER)
        except Exception as e:
            return f"Erro ao exportar certificado DER: {str(e)}"
    
    def get_certificate_status(self):
        """Verifica status do certificado"""
        try:
            with open(self.certificate_path, "rb") as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            now = datetime.utcnow()
            
            if now < cert.not_valid_before:
                return "FUTURE", "Certificado ainda não é válido"
            elif now > cert.not_valid_after:
                return "EXPIRED", "Certificado expirado"
            else:
                days_left = (cert.not_valid_after - now).days
                return "VALID", f"Certificado válido por mais {days_left} dias"
                
        except Exception as e:
            return "ERROR", f"Erro ao verificar status: {str(e)}"

# Instância global do gerenciador de certificados
certificate_manager = CertificateManager()
