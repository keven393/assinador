import os
import hashlib
import base64
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import aiofiles

def calculate_pdf_hash(pdf_path):
    """
    Calcula o hash SHA-256 do conteúdo binário do PDF.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        str: Hash SHA-256 em formato hexadecimal
    """
    sha256_hash = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while chunk := f.read(4096):  # Lê em chunks para PDFs grandes
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def calculate_content_hash(pdf_content):
    """
    Calcula o hash SHA-256 do conteúdo binário do PDF (a partir de bytes).
    
    Args:
        pdf_content: Conteúdo binário do PDF
        
    Returns:
        str: Hash SHA-256 em formato hexadecimal
    """
    return hashlib.sha256(pdf_content).hexdigest()

async def calculate_pdf_hash_async(pdf_path):
    """
    Calcula hash SHA256 de forma assíncrona
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        str: Hash SHA-256 em formato hexadecimal
    """
    sha256_hash = hashlib.sha256()
    async with aiofiles.open(pdf_path, 'rb') as f:
        while chunk := await f.read(4096):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def calculate_pdf_hash_with_cache(pdf_path, file_id=None):
    """
    Calcula hash SHA256 com cache no banco
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        file_id: ID do arquivo no banco (opcional)
        
    Returns:
        str: Hash SHA-256 em formato hexadecimal
    """
    if file_id:
        from models import Signature
        sig = Signature.query.filter_by(file_id=file_id).first()
        if sig and sig.pdf_hash_cached:
            return sig.pdf_hash_cached
    
    hash_value = calculate_pdf_hash(pdf_path)
    
    # Atualiza cache
    if file_id:
        sig = Signature.query.filter_by(file_id=file_id).first()
        if sig:
            sig.pdf_hash_cached = hash_value
            from models import db
            db.session.commit()
    
    return hash_value

def verify_pdf_signature_unified(pdf_content, signature_info, public_key_path):
    """
    Função unificada de verificação de assinatura PDF
    
    Args:
        pdf_content: Conteúdo binário do PDF
        signature_info: Dicionário com hash, signature e algorithm
        public_key_path: Caminho para a chave pública
        
    Returns:
        bool: True se a assinatura for válida
    """
    try:
        # Carrega chave pública
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        
        # Decodifica a assinatura
        signature_data = base64.b64decode(signature_info['signature'])
        
        # Calcula o hash do PDF
        pdf_hash = calculate_content_hash(pdf_content)
        
        # Verifica se o hash corresponde
        if pdf_hash != signature_info['hash']:
            return False
        
        # Verifica a assinatura do hash
        public_key.verify(
            signature_data,
            pdf_hash.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Erro na verificação da assinatura: {e}")
        return False

class DigitalSignatureManager:
    def __init__(self, keys_dir="keys"):
        # Usa KEYS_DIR_SECURE se configurado, senão usa keys_dir padrão
        secure_dir = os.environ.get('KEYS_DIR_SECURE')
        if secure_dir and secure_dir.strip():
            self.keys_dir = secure_dir
        else:
            # Se não for um caminho absoluto, usa relativo ao projeto (raiz)
            if not os.path.isabs(keys_dir):
                # Sobe um nível do utils/ para a raiz do projeto
                project_root = os.path.dirname(os.path.dirname(__file__))
                self.keys_dir = os.path.join(project_root, keys_dir)
            else:
                self.keys_dir = keys_dir
        
        self.private_key_path = os.path.join(self.keys_dir, "private_key.pem")
        self.public_key_path = os.path.join(self.keys_dir, "public_key.pem")
        
        # SECURITY: Suporte para chave privada criptografada com passphrase
        # Use PRIVATE_KEY_PASSPHRASE em produção para proteger a chave privada
        self.key_passphrase = os.environ.get('PRIVATE_KEY_PASSPHRASE', '').encode('utf-8') if os.environ.get('PRIVATE_KEY_PASSPHRASE') else None
        
        # Cria diretório de chaves se não existir
        if not os.path.exists(self.keys_dir):
            os.makedirs(self.keys_dir, mode=0o700)
        
        # Gera chaves se não existirem
        if not self._keys_exist():
            self._generate_key_pair()
    
    def _keys_exist(self):
        """Verifica se as chaves já existem"""
        return os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path)
    
    def _generate_key_pair(self):
        """Gera um par de chaves RSA"""
        # Gera chave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Gera chave pública
        public_key = private_key.public_key()
        
        # SECURITY: Salva chave privada com criptografia se passphrase fornecida
        if self.key_passphrase:
            encryption_algorithm = serialization.BestAvailableEncryption(self.key_passphrase)
        else:
            # AVISO: Chave privada sem criptografia - use PRIVATE_KEY_PASSPHRASE em produção
            encryption_algorithm = serialization.NoEncryption()
        
        # Salva chave privada
        with open(self.private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption_algorithm
            ))
        
        # Salva chave pública
        with open(self.public_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    
    def calculate_hash(self, data):
        """Calcula o hash SHA-256 dos dados"""
        if data is None:
            data = ""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    def sign_data(self, data):
        """Assina os dados com a chave privada"""
        # Carrega chave privada (com suporte para passphrase)
        with open(self.private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=self.key_passphrase,
                backend=default_backend()
            )
        
        # Se os dados já são um hash (64 caracteres hex), usa diretamente
        if isinstance(data, str) and len(data) == 64 and all(c in '0123456789abcdef' for c in data.lower()):
            data_hash = data
        else:
            # Calcula hash dos dados
            data_hash = self.calculate_hash(data)
        
        # Assina o hash
        signature = private_key.sign(
            data_hash.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Codifica assinatura em base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return {
            'hash': data_hash,
            'signature': signature_b64,
            'timestamp': datetime.now().isoformat(),
            'algorithm': 'RSA-SHA256'
        }
    
    def verify_signature(self, data, signature_info):
        """Verifica a assinatura dos dados"""
        try:
            # Carrega chave pública
            with open(self.public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            
            # Se os dados já são um hash (64 caracteres hex), usa diretamente
            if isinstance(data, str) and len(data) == 64 and all(c in '0123456789abcdef' for c in data.lower()):
                data_hash = data
            else:
                # Calcula hash dos dados
                data_hash = self.calculate_hash(data)
            
            # Decodifica assinatura
            signature = base64.b64decode(signature_info['signature'])
            
            # Verifica assinatura
            public_key.verify(
                signature,
                data_hash.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Verifica se o hash corresponde
            return data_hash == signature_info['hash']
            
        except (InvalidSignature, Exception) as e:
            return False
    
    def get_public_key_info(self):
        """Retorna informações da chave pública"""
        with open(self.public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        
        # Extrai informações da chave
        public_numbers = public_key.public_numbers()
        
        return {
            'modulus': str(public_numbers.n),
            'exponent': public_numbers.e,
            'key_size': public_key.key_size,
            'algorithm': 'RSA'
        }
    
    def export_public_key(self):
        """Exporta a chave pública em formato PEM"""
        with open(self.public_key_path, "r") as f:
            return f.read()

# Instância global do gerenciador de assinaturas
signature_manager = DigitalSignatureManager()
