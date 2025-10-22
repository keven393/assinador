import os
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações da aplicação - Todas as configurações vêm do arquivo .env"""
    
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'assinador_pdf_secret_key_2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///assinador.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Async database URI
    ASYNC_SQLALCHEMY_DATABASE_URI = os.environ.get('ASYNC_DATABASE_URL') or \
        os.environ.get('DATABASE_URL', 'sqlite:///assinador.db').replace('postgresql://', 'postgresql+asyncpg://')
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', '3600'))
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get('SESSION_LIFETIME_HOURS', '24')))
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', str(50 * 1024 * 1024)))  # bytes
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'temp_files')
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Configurações de diretórios
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMP_DIR = os.path.join(BASE_DIR, os.environ.get('TEMP_DIR', 'temp_files'))
    STATIC_DIR = os.path.join(BASE_DIR, os.environ.get('STATIC_DIR', 'static'))
    SIGNATURES_DIR = os.path.join(BASE_DIR, os.environ.get('SIGNATURES_DIR', 'signatures'))
    CERTIFICATES_DIR = os.path.join(BASE_DIR, os.environ.get('CERTIFICATES_DIR', 'certificates'))
    KEYS_DIR = os.path.join(BASE_DIR, os.environ.get('KEYS_DIR', 'keys'))
    PDF_SIGNED_DIR = os.path.join(BASE_DIR, os.environ.get('PDF_SIGNED_DIR', 'pdf_assinados'))
    LOGS_DIR = os.path.join(BASE_DIR, os.environ.get('LOGS_DIR', 'logs'))
    
    # Configurações de limpeza automática
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', '3600'))  # segundos
    FILE_RETENTION = int(os.environ.get('FILE_RETENTION', '86400'))  # segundos
    CLEANUP_TIME = os.environ.get('CLEANUP_TIME', '02:00')  # HH:MM
    CLEANUP_TZ = os.environ.get('CLEANUP_TZ', 'America/Sao_Paulo')
    
    # Configurações de retenção de arquivos
    FILE_RETENTION_DAYS = int(os.environ.get('FILE_RETENTION_DAYS', '7'))  # dias
    TEMP_FILE_RETENTION_HOURS = int(os.environ.get('TEMP_FILE_RETENTION_HOURS', '1'))  # horas
    
    # Configurações de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'assinador.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', '10240000'))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '10'))
    
    # Configurações de certificado
    CERTIFICATE_VALIDITY_DAYS = int(os.environ.get('CERTIFICATE_VALIDITY_DAYS', '1825'))  # 5 anos
    KEY_SIZE = int(os.environ.get('KEY_SIZE', '2048'))  # bits
    
    # Configurações de servidor
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5001'))
    WORKERS = int(os.environ.get('WORKERS', '4'))
    
    # Configurações de cache
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # Configurações de compressão
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript'
    ]
    COMPRESS_LEVEL = int(os.environ.get('COMPRESS_LEVEL', '6'))
    COMPRESS_MIN_SIZE = int(os.environ.get('COMPRESS_MIN_SIZE', '500'))
    
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
    
    # Otimizações de performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de compressão
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # Configurações de sessão otimizadas
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Reduzido para melhor performance
    
    # Configurações de upload otimizadas
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB para produção
    UPLOAD_FOLDER = 'temp_files'
    
    # Configurações de limpeza mais agressivas
    CLEANUP_INTERVAL = 1800  # 30 minutos
    FILE_RETENTION = 7200  # 2 horas
    
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
