from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    __table_args__ = (
        db.Index('idx_users_username', 'username'),
        db.Index('idx_users_email', 'email'),
        db.Index('idx_users_role', 'role'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable para usuários LDAP
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' ou 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    signatures = db.relationship('Signature', backref='user', lazy='dynamic')
    
    # Campos do Active Directory
    ldap_dn = db.Column(db.String(500))  # Distinguished Name do LDAP
    department = db.Column(db.String(200))  # Departamento
    position = db.Column(db.String(200))  # Cargo
    phone = db.Column(db.String(50))  # Telefone
    mobile = db.Column(db.String(50))  # Celular
    city = db.Column(db.String(100))  # Cidade
    state = db.Column(db.String(100))  # Estado
    postal_code = db.Column(db.String(20))  # CEP
    country = db.Column(db.String(100))  # País
    street_address = db.Column(db.String(500))  # Endereço
    home_phone = db.Column(db.String(50))  # Telefone residencial
    work_address = db.Column(db.String(500))  # Endereço comercial
    fax = db.Column(db.String(50))  # Fax
    pager = db.Column(db.String(50))  # Pager
    is_ldap_user = db.Column(db.Boolean, default=False)  # Indica se é usuário LDAP
    
    def set_password(self, password):
        """Define a senha do usuário com hash bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Signature(db.Model):
    __tablename__ = 'signatures'
    
    __table_args__ = (
        db.Index('idx_signatures_user_id', 'user_id'),
        db.Index('idx_signatures_timestamp', 'timestamp'),
        db.Index('idx_signatures_file_id', 'file_id'),
        db.Index('idx_signatures_status', 'status'),
        db.Index('idx_signatures_hash', 'signature_hash'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    signature_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hex = 64 chars
    signature_algorithm = db.Column(db.String(50), nullable=False)
    signature_data = db.Column(db.Text)  # Dados da assinatura digital (base64)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    file_size = db.Column(db.Integer)
    signature_valid = db.Column(db.Boolean, default=True)
    # Armazenamento opcional do PDF assinado
    signed_pdf = db.Column(db.LargeBinary)
    # Novos campos para otimização
    pdf_hash_cached = db.Column(db.String(64), index=True)  # Cache do hash para evitar recalcular
    pdf_file_path = db.Column(db.String(500))  # Caminho do PDF no filesystem
    
    # Tipo de Documento
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_types.id'))
    
    # Informações do Cliente/Assinante
    client_name = db.Column(db.String(255))
    client_cpf = db.Column(db.String(14))
    client_email = db.Column(db.String(255))
    client_phone = db.Column(db.String(20))
    client_birth_date = db.Column(db.Date)
    client_address = db.Column(db.Text)
    
    # Informações do Dispositivo e Conexão
    ip_address = db.Column(db.String(45))
    mac_address = db.Column(db.String(17))  # Formato XX:XX:XX:XX:XX:XX
    user_agent = db.Column(db.Text)
    browser_name = db.Column(db.String(50))
    browser_version = db.Column(db.String(20))
    operating_system = db.Column(db.String(100))
    device_type = db.Column(db.String(20))  # Desktop, Mobile, Tablet
    screen_resolution = db.Column(db.String(20))
    timezone = db.Column(db.String(50))
    
    # Informações de Localização (se disponível)
    location_country = db.Column(db.String(100))
    location_city = db.Column(db.String(100))
    location_latitude = db.Column(db.Float)
    location_longitude = db.Column(db.Float)
    
    # Informações da Assinatura
    signature_method = db.Column(db.String(20), default='drawing')  # drawing, upload, etc.
    signature_duration = db.Column(db.Integer)  # Tempo gasto na assinatura em segundos
    verification_status = db.Column(db.String(20), default='verified')
    verification_notes = db.Column(db.Text)
    
    # Status da assinatura
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Signature {self.file_id} by {self.client_name}>'

class DocumentType(db.Model):
    __tablename__ = 'document_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    signatures = db.relationship('Signature', backref='document_type', lazy='dynamic')

    def __repr__(self):
        return f'<DocumentType {self.name}>'

class AppSetting(db.Model):
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f'<AppSetting {self.key}={self.value}>'

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    __table_args__ = (
        db.Index('idx_sessions_user_id', 'user_id'),
        db.Index('idx_sessions_expires_at', 'expires_at'),
        db.Index('idx_sessions_session_id', 'session_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='sessions')
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'
