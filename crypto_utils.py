import os
import hashlib
import base64
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

class DigitalSignatureManager:
    def __init__(self, keys_dir="keys"):
        self.keys_dir = keys_dir
        self.private_key_path = os.path.join(keys_dir, "private_key.pem")
        self.public_key_path = os.path.join(keys_dir, "public_key.pem")
        
        # Cria diretório de chaves se não existir
        if not os.path.exists(keys_dir):
            os.makedirs(keys_dir)
        
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
        
        # Salva chave privada
        with open(self.private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
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
        # Carrega chave privada
        with open(self.private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
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
