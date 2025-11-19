#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
import base64
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from io import BytesIO
import tempfile

class PDFValidator:
    """Validador de PDFs assinados pelo sistema"""
    
    def __init__(self, keys_dir="keys", certs_dir="certificates"):
        self.keys_dir = keys_dir
        self.certs_dir = certs_dir
        self.public_key_path = os.path.join(keys_dir, "public_key.pem")
        self.certificate_path = os.path.join(keys_dir, "public_key.pem")  # Usa a mesma chave pública
    
    def calculate_pdf_hash(self, pdf_content):
        """Calcula o hash SHA-256 do conteúdo do PDF"""
        from utils.crypto_utils import calculate_content_hash
        return calculate_content_hash(pdf_content)
    
    def extract_signature_metadata(self, pdf_path):
        """Extrai metadados de assinatura do PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                # Procura por metadados de assinatura
                metadata = {}
                if pdf_reader.metadata:
                    # Verifica se há metadados customizados
                    custom_metadata = pdf_reader.metadata.get('/Custom', {})
                    if custom_metadata:
                        # Tenta extrair informações de assinatura
                        for key, value in custom_metadata.items():
                            if isinstance(key, str) and 'signature' in key.lower():
                                metadata[key] = value
                
                # Procura por anotações ou campos de assinatura
                for page_num, page in enumerate(pdf_reader.pages):
                    if '/Annots' in page:
                        annotations = page['/Annots']
                        for annot in annotations:
                            annot_obj = annot.get_object()
                            if '/Contents' in annot_obj:
                                content = annot_obj['/Contents']
                                if isinstance(content, str) and 'signature' in content.lower():
                                    metadata[f'annotation_page_{page_num}'] = content
                
                return metadata
        except Exception as e:
            print(f"Erro ao extrair metadados: {e}")
            return {}
    
    def verify_signature_integrity(self, pdf_content, stored_hash):
        """Verifica se o hash do PDF corresponde ao hash armazenado"""
        current_hash = self.calculate_pdf_hash(pdf_content)
        return current_hash == stored_hash
    
    def verify_digital_signature(self, pdf_content, signature_info):
        """Verifica a assinatura digital do PDF
        Tenta primeiro com o certificado X.509 do sistema; se falhar, usa a chave pública legacy.
        """
        # Tentativa 1: verificar com o certificado X.509
        try:
            from services.certificate_manager import certificate_manager
            ok, _msg = certificate_manager.verify_signature_with_certificate(pdf_content, {
                'hash': signature_info.get('hash'),
                'signature_data': signature_info.get('signature') or signature_info.get('signature_data')
            })
            if ok:
                return True
        except Exception:
            pass
        # Tentativa 2: fallback legacy com chave pública
        try:
            from utils.crypto_utils import verify_pdf_signature_unified
            # Normaliza o formato para o verificador legacy
            legacy_sig = {
                'hash': signature_info.get('hash'),
                'signature': signature_info.get('signature') or signature_info.get('signature_data')
            }
            return verify_pdf_signature_unified(pdf_content, legacy_sig, self.public_key_path)
        except Exception:
            return False
    
    def verify_certificate_signature(self, pdf_content, signature_info):
        """Verifica a assinatura usando a chave pública do sistema"""
        from utils.crypto_utils import verify_pdf_signature_unified
        return verify_pdf_signature_unified(pdf_content, signature_info, self.public_key_path)
    
    def validate_pdf(self, pdf_path, signature_record=None):
        """
        Valida um PDF assinado pelo sistema
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            signature_record: Registro da assinatura no banco de dados (opcional)
        
        Returns:
            dict: Resultado da validação com status e detalhes
        """
        try:
            # Lê o conteúdo do PDF
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Calcula hash atual
            current_hash = self.calculate_pdf_hash(pdf_content)
            
            result = {
                'valid': False,
                'hash_match': False,
                'digital_signature_valid': False,
                'certificate_signature_valid': False,
                'current_hash': current_hash,
                'stored_hash': None,
                'signature_info': None,
                'certificate_subject': None,
                'certificate_issuer': None,
                'metadata': {},
                'errors': []
            }
            
            # Se temos um registro de assinatura, verifica contra ele
            if signature_record:
                result['stored_hash'] = signature_record.signature_hash
                # Verifica se o hash corresponde
                if current_hash == signature_record.signature_hash:
                    result['hash_match'] = True
                else:
                    # Hash diferente - arquivo foi adulterado ou corrompido
                    # SECURITY: Não sincronizamos automaticamente para evitar aceitar arquivos adulterados
                    print(f"⚠️  ALERTA DE SEGURANÇA: Hash diferente detectado - possível adulteração!")
                    print(f"   Hash armazenado: {signature_record.signature_hash[:16]}...")
                    print(f"   Hash atual:      {current_hash[:16]}...")
                    print(f"   Arquivo marcado como INVÁLIDO por violação de integridade.")
                    result['hash_match'] = False
                    result['errors'].append('Hash mismatch: arquivo pode ter sido adulterado')
                
                # Tenta verificar assinatura digital
                try:
                    # Constrói signature_info a partir do registro
                    signature_info = {
                        'hash': signature_record.signature_hash,
                        'algorithm': signature_record.signature_algorithm,
                        'signature': signature_record.signature_data
                    }
                    
                    if signature_info['signature']:
                        result['digital_signature_valid'] = self.verify_digital_signature(pdf_content, signature_info)
                        # Verificação com certificado do sistema (PKI interna)
                        ok_cert, msg_cert = False, ''
                        try:
                            from services.certificate_manager import certificate_manager
                            ok_cert, msg_cert = certificate_manager.verify_signature_with_certificate(pdf_content, {
                                'hash': signature_info.get('hash'),
                                'signature_data': signature_info.get('signature')
                            })
                        except Exception as e:
                            result['errors'].append(str(e))
                        result['certificate_signature_valid'] = ok_cert
                        result['signature_info'] = signature_info
                except Exception as e:
                    result['errors'].append(f"Erro na verificação da assinatura: {e}")
            
            # Extrai metadados do PDF
            result['metadata'] = self.extract_signature_metadata(pdf_path)
            
            # Determina se o PDF é válido
            # Para o sistema atual, consideramos válido se o hash confere e a assinatura digital é válida
            # A verificação de certificado é opcional e pode falhar se as chaves forem diferentes
            result['valid'] = (result['hash_match'] and result['digital_signature_valid'])
            
            return result
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Erro ao processar PDF: {e}",
                'errors': [str(e)]
            }
    
    def validate_pdf_by_file_id(self, file_id, pdf_path):
        """
        Valida um PDF usando o file_id para buscar o registro de assinatura
        
        Args:
            file_id: ID do arquivo no banco de dados
            pdf_path: Caminho para o arquivo PDF
        
        Returns:
            dict: Resultado da validação
        """
        try:
            # Importa aqui para evitar import circular
            from app import db
            from models import Signature
            
            # Busca o registro de assinatura
            signature_record = Signature.query.filter_by(file_id=file_id).first()
            
            if not signature_record:
                return {
                    'valid': False,
                    'error': 'Registro de assinatura não encontrado',
                    'file_id': file_id
                }
            
            return self.validate_pdf(pdf_path, signature_record)
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Erro ao buscar registro: {e}",
                'file_id': file_id
            }

# Instância global do validador
pdf_validator = PDFValidator()
