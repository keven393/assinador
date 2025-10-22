#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para promover um usuário do Active Directory como administrador do sistema.
Uso: python make_admin.py <username>
"""

import sys
import os
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório raiz ao path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Flask
from app import create_app, db
from models import User

def make_admin(username):
    """
    Promove um usuário para administrador.
    
    Args:
        username: Nome de usuário (sAMAccountName) do AD
    """
    app = create_app()
    
    with app.app_context():
        # Buscar usuário
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ Erro: Usuário '{username}' não encontrado no banco de dados.")
            print(f"\n📋 Possíveis causas:")
            print(f"   - O usuário ainda não fez login no sistema")
            print(f"   - O nome de usuário está incorreto")
            print(f"   - O usuário não existe no Active Directory")
            print(f"\n💡 Dica: O usuário precisa fazer login pelo menos uma vez para ser criado no banco.")
            return False
        
        # Verificar se já é admin
        if user.role == 'admin':
            print(f"✅ O usuário '{username}' já é administrador.")
            print(f"\n📊 Informações do usuário:")
            print(f"   - Nome: {user.full_name}")
            print(f"   - Email: {user.email}")
            print(f"   - Role: {user.role}")
            print(f"   - Status: {'Ativo' if user.is_active else 'Inativo'}")
            print(f"   - LDAP: {'Sim' if user.is_ldap_user else 'Não'}")
            return True
        
        # Promover para admin
        user.role = 'admin'
        user.is_active = True  # Ativar conta também
        
        try:
            db.session.commit()
            
            print(f"✅ Usuário '{username}' promovido a administrador com sucesso!")
            print(f"\n📊 Informações do usuário:")
            print(f"   - Nome: {user.full_name}")
            print(f"   - Email: {user.email}")
            print(f"   - Role: {user.role} (atualizado)")
            print(f"   - Status: {'Ativo' if user.is_active else 'Inativo'}")
            print(f"   - LDAP: {'Sim' if user.is_ldap_user else 'Não'}")
            print(f"\n🎉 O usuário agora tem acesso completo ao sistema!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao promover usuário: {str(e)}")
            return False

def list_users():
    """
    Lista todos os usuários do sistema.
    """
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("❌ Nenhum usuário encontrado no sistema.")
            return
        
        print(f"\n📋 Usuários cadastrados no sistema ({len(users)} total):\n")
        print(f"{'Username':<20} {'Nome':<30} {'Role':<10} {'Status':<10} {'LDAP':<6}")
        print("-" * 90)
        
        for user in users:
            status = "Ativo" if user.is_active else "Inativo"
            ldap = "Sim" if user.is_ldap_user else "Não"
            role_icon = "👑" if user.role == 'admin' else "👤"
            
            print(f"{user.username:<20} {user.full_name[:28]:<30} {role_icon} {user.role:<8} {status:<10} {ldap:<6}")
        
        print("\n")

def main():
    """
    Função principal do script.
    """
    print("=" * 70)
    print("🔧 Script de Gerenciamento de Administradores")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        print("\n❌ Erro: Nome de usuário não fornecido.")
        print("\n📖 Uso:")
        print("   python make_admin.py <username>     - Promover usuário a admin")
        print("   python make_admin.py --list         - Listar todos os usuários")
        print("\n📝 Exemplos:")
        print("   python make_admin.py keven")
        print("   python make_admin.py admin.ldap")
        print("   python make_admin.py --list")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == '--list' or command == '-l':
        list_users()
    else:
        username = command
        print(f"\n🔍 Procurando usuário: {username}\n")
        success = make_admin(username)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == '__main__':
    main()

