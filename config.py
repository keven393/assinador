import os
from datetime import timedelta

class Config:
    """Configurações da aplicação"""
    
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'assinador_pdf_secret_key_2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///assinador.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = 'temp_files'
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Configurações de diretórios
    TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_files')
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    SIGNATURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signatures')
    CERTIFICATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates')
    KEYS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys')
    
    # Configurações de limpeza automática
    CLEANUP_INTERVAL = 3600  # 1 hora em segundos
    FILE_RETENTION = 86400  # 24 horas em segundos
    
    # Configurações de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'assinador.log'
    
    # Configurações de certificado
    CERTIFICATE_VALIDITY_DAYS = 1825  # 5 anos
    KEY_SIZE = 2048  # bits
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        # Cria diretórios necessários
        for directory in [Config.TEMP_DIR, Config.STATIC_DIR, 
                         Config.SIGNATURES_DIR, Config.CERTIFICATES_DIR, Config.KEYS_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Configurações de produção
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # Configura logging para arquivo
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/assinador.log', 
                                            maxBytes=10240000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Assinador de PDFs iniciado')

class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
