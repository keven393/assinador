#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para validação e gerenciamento de senhas
"""

import re
from typing import List, Tuple

class PasswordValidator:
    """Validador de requisitos de senha"""
    
    def __init__(self):
        self.min_length = 8
        self.require_lowercase = True  # Pelo menos uma letra minúscula
        self.require_uppercase = True  # Pelo menos uma letra maiúscula
        self.require_number = True     # Pelo menos um número
        self.require_special = True   # Pelo menos um caractere especial
        
        # Caracteres especiais permitidos
        self.special_chars = r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?~`]'
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """
        Valida uma senha contra os requisitos
        
        Args:
            password: Senha a ser validada
            
        Returns:
            Tuple[bool, List[str]]: (é_válida, lista_de_erros)
        """
        errors = []
        
        # Verifica comprimento mínimo
        if len(password) < self.min_length:
            errors.append(f"A senha deve ter pelo menos {self.min_length} caracteres")
        
        # Verifica se tem pelo menos uma letra minúscula
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("A senha deve conter pelo menos uma letra minúscula")
        
        # Verifica se tem pelo menos uma letra maiúscula
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("A senha deve conter pelo menos uma letra maiúscula")
        
        # Verifica se tem pelo menos um número
        if self.require_number and not re.search(r'\d', password):
            errors.append("A senha deve conter pelo menos um número")
        
        # Verifica se tem pelo menos um caractere especial
        if self.require_special and not re.search(self.special_chars, password):
            errors.append("A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        
        return len(errors) == 0, errors
    
    def get_requirements_text(self) -> str:
        """Retorna texto com os requisitos de senha"""
        requirements = [f"Pelo menos {self.min_length} caracteres"]
        
        if self.require_lowercase:
            requirements.append("pelo menos uma letra minúscula")
        
        if self.require_uppercase:
            requirements.append("pelo menos uma letra maiúscula")
        
        if self.require_number:
            requirements.append("pelo menos um número")
        
        if self.require_special:
            requirements.append("pelo menos um caractere especial")
        
        return ", ".join(requirements)
    
    def get_requirements_html(self) -> str:
        """Retorna HTML com os requisitos de senha para exibição"""
        return f"""
        <div class="password-requirements">
            <small class="text-muted">
                <strong>Requisitos da senha:</strong><br>
                • Pelo menos {self.min_length} caracteres<br>
                • Pelo menos uma letra minúscula (a-z)<br>
                • Pelo menos uma letra maiúscula (A-Z)<br>
                • Pelo menos um número (0-9)<br>
                • Pelo menos um caractere especial (!@#$%^&*()_+-=[]{{}}|;:,.<>?)
            </small>
        </div>
        """

# Instância global do validador
password_validator = PasswordValidator()
