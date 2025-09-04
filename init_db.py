from app import create_app
from models import db, User
from datetime import datetime, timezone

def init_database():
    """Inicializa o banco de dados e cria usuário administrador padrão"""
    app = create_app()
    
    with app.app_context():
        # Cria todas as tabelas
        db.create_all()
        
        # Verifica se já existe um usuário administrador
        admin_user = User.query.filter_by(role='admin').first()
        
        if not admin_user:
            # Cria usuário administrador padrão
            admin = User(
                username='admin',
                email='admin@assinador.com',
                full_name='Administrador do Sistema',
                role='admin',
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            admin.set_password('admin123')  # Senha padrão - deve ser alterada em produção
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário administrador criado com sucesso!")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("   ⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!")
        else:
            print("✅ Usuário administrador já existe no sistema")
        
        print("✅ Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_database()
