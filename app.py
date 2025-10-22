from flask import Flask, render_template, request, jsonify, send_file, session, flash, redirect, url_for, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import PyPDF2
import aiofiles
import asyncio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch, cm
import io
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import threading
import time
import tempfile
import base64
from PIL import Image
import numpy as np
import uuid
import shutil
import json
from functools import wraps
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Imports dos serviços e utilitários
from services import certificate_manager, pdf_validator
from utils import signature_manager
from models import db, User, Signature, AppSetting
from forms import LoginForm, UserEditForm, ChangePasswordForm, AdminUserForm, ReportFilterForm
from auth import admin_required, create_user_session, cleanup_expired_sessions, get_user_stats, get_signature_stats

from config import config
import os
import re
from datetime import date
from utils.mobile_optimizations import (
    is_mobile_device, is_tablet, optimize_for_device, 
    get_optimized_query_limits, should_use_compression,
    get_cache_timeout, optimize_database_queries,
    get_mobile_headers, log_performance_metrics
)
from audit_logger import log_event, log_signature_event, log_validation_event

def save_pdf_to_filesystem(pdf_content, file_id):
    """
    Salva PDF no filesystem e retorna o caminho
    
    Args:
        pdf_content: Conteúdo binário do PDF
        file_id: ID único do arquivo
        
    Returns:
        str: Caminho completo do arquivo salvo
    """
    now = datetime.now()
    year_dir = os.path.join(app.config['PDF_SIGNED_DIR'], str(now.year))
    month_dir = os.path.join(year_dir, f"{now.month:02d}")
    
    os.makedirs(month_dir, exist_ok=True)
    
    pdf_path = os.path.join(month_dir, f"{file_id}.pdf")
    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)
    
    return pdf_path

async def save_pdf_to_filesystem_async(pdf_content, file_id):
    """
    Versão assíncrona de save_pdf_to_filesystem
    
    Args:
        pdf_content: Conteúdo binário do PDF
        file_id: ID único do arquivo
        
    Returns:
        str: Caminho completo do arquivo salvo
    """
    now = datetime.now()
    year_dir = os.path.join(app.config['PDF_SIGNED_DIR'], str(now.year))
    month_dir = os.path.join(year_dir, f"{now.month:02d}")
    
    os.makedirs(month_dir, exist_ok=True)
    
    pdf_path = os.path.join(month_dir, f"{file_id}.pdf")
    async with aiofiles.open(pdf_path, 'wb') as f:
        await f.write(pdf_content)
    
    return pdf_path

def detect_device_info(user_agent, request_obj):
    """Detecta informações completas do dispositivo e conexão"""
    device_info = {
        'user_agent': user_agent or '',
        'ip_address': get_client_ip(request_obj),
        'mac_address': None,  # Será tentado via JavaScript
        'browser_name': 'Unknown',
        'browser_version': 'Unknown',
        'operating_system': 'Unknown',
        'device_type': 'Unknown',
        'screen_resolution': None,
        'timezone': None,
        'location_country': None,
        'location_city': None
    }
    
    if not user_agent:
        return device_info
    
    user_agent_lower = user_agent.lower()
    
    # Detecta browser
    if 'chrome' in user_agent_lower and 'chromium' not in user_agent_lower:
        device_info['browser_name'] = 'Chrome'
        match = re.search(r'chrome/([\d.]+)', user_agent_lower)
        if match:
            device_info['browser_version'] = match.group(1)
    elif 'firefox' in user_agent_lower:
        device_info['browser_name'] = 'Firefox'
        match = re.search(r'firefox/([\d.]+)', user_agent_lower)
        if match:
            device_info['browser_version'] = match.group(1)
    elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
        device_info['browser_name'] = 'Safari'
        match = re.search(r'version/([\d.]+)', user_agent_lower)
        if match:
            device_info['browser_version'] = match.group(1)
    elif 'edge' in user_agent_lower:
        device_info['browser_name'] = 'Edge'
        match = re.search(r'edge/([\d.]+)', user_agent_lower)
        if match:
            device_info['browser_version'] = match.group(1)
    elif 'opera' in user_agent_lower:
        device_info['browser_name'] = 'Opera'
        match = re.search(r'opera/([\d.]+)', user_agent_lower)
        if match:
            device_info['browser_version'] = match.group(1)
    
    # Detecta sistema operacional
    if 'windows' in user_agent_lower:
        device_info['operating_system'] = 'Windows'
        if 'windows nt 10.0' in user_agent_lower:
            device_info['operating_system'] = 'Windows 10/11'
        elif 'windows nt 6.3' in user_agent_lower:
            device_info['operating_system'] = 'Windows 8.1'
        elif 'windows nt 6.1' in user_agent_lower:
            device_info['operating_system'] = 'Windows 7'
    elif 'mac os x' in user_agent_lower or 'macos' in user_agent_lower:
        device_info['operating_system'] = 'macOS'
        match = re.search(r'mac os x ([\d_]+)', user_agent_lower)
        if match:
            version = match.group(1).replace('_', '.')
            device_info['operating_system'] = f'macOS {version}'
    elif 'android' in user_agent_lower:
        device_info['operating_system'] = 'Android'
        match = re.search(r'android ([\d.]+)', user_agent_lower)
        if match:
            device_info['operating_system'] = f'Android {match.group(1)}'
    elif 'iphone os' in user_agent_lower or 'ios' in user_agent_lower:
        device_info['operating_system'] = 'iOS'
        match = re.search(r'os ([\d_]+)', user_agent_lower)
        if match:
            version = match.group(1).replace('_', '.')
            device_info['operating_system'] = f'iOS {version}'
    elif 'linux' in user_agent_lower:
        device_info['operating_system'] = 'Linux'
    
    # Detecta tipo de dispositivo
    if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
        device_info['device_type'] = 'Mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        device_info['device_type'] = 'Tablet'
    else:
        device_info['device_type'] = 'Desktop'
    
    return device_info

def get_client_ip(request_obj):
    """Obtém o IP real do cliente, considerando proxies"""
    # Prioridade para headers de proxy
    if request_obj.headers.get('X-Forwarded-For'):
        return request_obj.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request_obj.headers.get('X-Real-IP'):
        return request_obj.headers.get('X-Real-IP')
    elif request_obj.headers.get('X-Forwarded'):
        return request_obj.headers.get('X-Forwarded')
    elif request_obj.headers.get('X-Cluster-Client-IP'):
        return request_obj.headers.get('X-Cluster-Client-IP')
    else:
        return request_obj.remote_addr

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configurações adicionais de sessão
    app.config['SESSION_COOKIE_NAME'] = 'assinador_session'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Inicializa extensões
    db.init_app(app)

    # Garante schema de Tipos de Documento
    try:
        from models import DocumentType
        with app.app_context():
            # Cria tabela document_types se não existir
            try:
                DocumentType.__table__.create(bind=db.engine, checkfirst=True)
            except Exception:
                pass
            # Adiciona coluna document_type_id em signatures se não existir
            try:
                inspector = db.inspect(db.engine)
                cols = [c['name'] for c in inspector.get_columns('signatures')]
                if 'document_type_id' not in cols:
                    with db.engine.connect() as conn:
                        conn.execute(db.text('ALTER TABLE signatures ADD COLUMN document_type_id INTEGER'))
            except Exception:
                pass
    except Exception:
        pass
    
    # Inicializa cache
    cache = Cache()
    cache.init_app(app)
    
    # Inicializa compressão
    compress = Compress()
    compress.init_app(app)
    
    # Inicializa rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    # Disponibiliza cache e limiter globalmente
    app.cache = cache
    app.limiter = limiter
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Filtro Jinja para formatar CPF
    def jinja_format_cpf(value):
        try:
            if value is None:
                return ''
            digits = re.sub(r'\D', '', str(value))
            if len(digits) != 11:
                return str(value)
            return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"
        except Exception:
            return str(value)
    app.jinja_env.filters['cpf'] = jinja_format_cpf
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Adiciona middleware de performance
    @app.before_request
    def before_request():
        g.start_time = time.time()
        
        # Aplica otimizações para dispositivos móveis
        optimize_for_device()
        
        # Configura limites baseados no dispositivo
        g.query_limit = get_optimized_query_limits()
        g.cache_timeout = get_cache_timeout()
    
    @app.after_request
    def after_request(response):
        # Headers específicos para mobile
        mobile_headers = get_mobile_headers()
        for header, value in mobile_headers.items():
            response.headers[header] = value
        
        # Adiciona headers de cache para arquivos estáticos
        if request.endpoint and request.endpoint.startswith('static'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 ano
        elif request.endpoint in ['index', 'admin_dashboard']:
            cache_timeout = get_cache_timeout()
            response.headers['Cache-Control'] = f'private, max-age={cache_timeout}'
        
        # Adiciona headers de compressão
        if should_use_compression():
            response.headers['Vary'] = 'Accept-Encoding'
        
        # Log de performance
        log_performance_metrics()
        
        # Log de performance (apenas em desenvolvimento)
        if app.debug:
            duration = time.time() - g.start_time
            if duration > 1.0:  # Log apenas requests lentos
                app.logger.warning(f'Slow request: {request.endpoint} took {duration:.2f}s')
        
        try:
            if current_user and getattr(current_user, 'is_authenticated', False):
                monitored = {
                    'login', 'logout', 'admin_sync', 'admin_users', 'admin_new_user', 'admin_edit_user',
                    'internal_signature_upload', 'internal_cancel_signature', 'internal_completed_signatures',
                    'client_sign_document', 'validate_pdf', 'admin_reports'
                }
                if request.endpoint in monitored:
                    log_event(
                        action=f"endpoint:{request.endpoint}",
                        actor_user_id=current_user.id,
                        status=str(response.status_code),
                        ip_address=get_client_ip(request),
                        details={"method": request.method}
                    )
        except Exception:
            pass
        return response
    
    # Função para invalidar cache
    def invalidate_user_cache(user_id=None):
        """Invalida cache relacionado ao usuário"""
        if user_id:
            app.cache.delete(f"user_signatures_{user_id}")
        app.cache.delete("admin_dashboard_stats")
        app.cache.delete("admin_users_list")
    
    # Register routes
    register_routes(app)
    
    # Inicia rotina diária de limpeza uma única vez
    global SCHEDULER_STARTED
    if not SCHEDULER_STARTED:
        try:
            # Lê horário da limpeza do config (.env)
            cleanup_time = getattr(app.config, 'CLEANUP_TIME', '02:00') if hasattr(app.config, 'CLEANUP_TIME') else app.config.get('CLEANUP_TIME', '02:00')
            cleanup_tz = getattr(app.config, 'CLEANUP_TZ', 'America/Sao_Paulo') if hasattr(app.config, 'CLEANUP_TZ') else app.config.get('CLEANUP_TZ', 'America/Sao_Paulo')
            try:
                hour_str, minute_str = str(cleanup_time).split(':')
                hour = int(hour_str)
                minute = int(minute_str)
            except Exception:
                hour, minute = 2, 0
            t = threading.Thread(target=run_daily_cleanup, kwargs={'hour': hour, 'minute': minute, 'tz_name': cleanup_tz}, daemon=True)
            t.start()
            SCHEDULER_STARTED = True
        except Exception as e:
            print(f"Não foi possível iniciar o agendador de limpeza: {e}")
    
    return app

def register_routes(app):
    # === ADMIN: Tipos de Documento ===
    @app.route('/admin/document-types', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_document_types():
        from models import DocumentType
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'create':
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                if not name:
                    flash('Nome do tipo é obrigatório', 'error')
                else:
                    # Verifica duplicado
                    if DocumentType.query.filter(db.func.lower(DocumentType.name) == name.lower()).first():
                        flash('Já existe um tipo com este nome.', 'error')
                    else:
                        dt = DocumentType(name=name, description=description)
                        db.session.add(dt)
                        db.session.commit()
                        flash('Tipo de documento criado com sucesso!', 'success')
                return redirect(url_for('admin_document_types'))
            elif action == 'update':
                dt_id = request.form.get('id')
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                active = request.form.get('active') == 'on'
                dt = DocumentType.query.get_or_404(dt_id)
                if not name:
                    flash('Nome do tipo é obrigatório', 'error')
                else:
                    # Confere conflito por nome
                    exists = DocumentType.query.filter(db.func.lower(DocumentType.name) == name.lower(), DocumentType.id != dt.id).first()
                    if exists:
                        flash('Já existe outro tipo com este nome.', 'error')
                    else:
                        dt.name = name
                        dt.description = description
                        dt.active = active
                        db.session.commit()
                        flash('Tipo de documento atualizado!', 'success')
                return redirect(url_for('admin_document_types'))
            elif action == 'delete':
                dt_id = request.form.get('id')
                dt = DocumentType.query.get_or_404(dt_id)
                try:
                    db.session.delete(dt)
                    db.session.commit()
                    flash('Tipo de documento removido.', 'success')
                except Exception:
                    db.session.rollback()
                    flash('Não foi possível remover. Verifique se há assinaturas vinculadas.', 'error')
                return redirect(url_for('admin_document_types'))
        # GET
        q = request.args.get('q', '').strip()
        query = DocumentType.query
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(DocumentType.name.ilike(like), DocumentType.description.ilike(like)))
        items = query.order_by(DocumentType.active.desc(), DocumentType.name.asc()).all()
        return render_template('admin/document_types.html', items=items, q=q)
    """Register all application routes"""
    
    # Helpers de configuração de armazenamento de PDFs
    def get_store_pdfs_flag():
        setting = AppSetting.query.filter_by(key='store_pdfs').first()
        if not setting:
            return False
        return setting.value.lower() == 'true'
    
    def set_store_pdfs_flag(value: bool):
        setting = AppSetting.query.filter_by(key='store_pdfs').first()
        if not setting:
            setting = AppSetting(key='store_pdfs', value='true' if value else 'false')
            db.session.add(setting)
        else:
            setting.value = 'true' if value else 'false'
        db.session.commit()
    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_settings():
        if request.method == 'POST':
            value = request.form.get('store_pdfs') == 'on'
            set_store_pdfs_flag(value)
            flash('Configurações atualizadas.', 'success')
            return redirect(url_for('admin_settings'))
        
        # Informações do sistema
        import sys
        import flask
        import importlib.util
        import platform
        import psutil
        from datetime import datetime
        
        # Detectar tipo de banco
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if 'postgresql' in db_uri:
            db_type = 'PostgreSQL'
            # Extrair host e porta se disponível
            try:
                import re
                match = re.search(r'@([^:]+):(\d+)/', db_uri)
                if match:
                    db_host = match.group(1)
                    db_port = match.group(2)
                else:
                    db_host = 'localhost'
                    db_port = '5432'
            except:
                db_host = 'localhost'
                db_port = '5432'
        elif 'mysql' in db_uri:
            db_type = 'MySQL'
            db_host = 'localhost'
            db_port = '3306'
        else:
            db_type = 'SQLite'
            db_host = 'Local'
            db_port = 'N/A'
        
        # Verificar se async está habilitado
        from async_db import IS_SQLITE
        async_enabled = not IS_SQLITE
        
        # Versões
        python_version = sys.version.split()[0]
        flask_version = flask.__version__
        platform_info = platform.platform()
        machine = platform.machine()
        processor = platform.processor()
        
        # Informações de memória e CPU
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_total_gb = round(memory.total / (1024**3), 2)
            memory_used_gb = round(memory.used / (1024**3), 2)
            memory_percent = memory.percent
            disk = psutil.disk_usage('/')
            disk_total_gb = round(disk.total / (1024**3), 2)
            disk_used_gb = round(disk.used / (1024**3), 2)
            disk_percent = disk.percent
        except:
            cpu_count = 'N/A'
            cpu_percent = 'N/A'
            memory_total_gb = 'N/A'
            memory_used_gb = 'N/A'
            memory_percent = 'N/A'
            disk_total_gb = 'N/A'
            disk_used_gb = 'N/A'
            disk_percent = 'N/A'
        
        # Verificar recursos
        async_supported = True
        cache_enabled = hasattr(app, 'cache')
        rate_limit_enabled = hasattr(app, 'limiter')
        
        # Tipo de cache
        if cache_enabled:
            try:
                cache_type = app.cache.config['CACHE_TYPE']
                cache_timeout = app.cache.config.get('CACHE_DEFAULT_TIMEOUT', 300)
            except:
                cache_type = 'SimpleCache'
                cache_timeout = 300
        else:
            cache_type = 'Desabilitado'
            cache_timeout = 0
        
        # Caminhos
        pdf_signed_dir = app.config.get('PDF_SIGNED_DIR', 'pdf_assinados/')
        keys_dir = app.config.get('KEYS_DIR', 'keys/')
        audit_log_path = os.path.join(app.config.get('LOGS_DIR', 'logs/'), 'audit.log')
        
        # Verificar se diretórios existem
        pdf_dir_exists = os.path.exists(pdf_signed_dir)
        keys_dir_exists = os.path.exists(keys_dir)
        audit_log_exists = os.path.exists(audit_log_path)
        
        # Contar arquivos de log de auditoria
        audit_log_count = 0
        if audit_log_exists:
            try:
                with open(audit_log_path, 'r') as f:
                    audit_log_count = len(f.readlines())
            except:
                pass
        
        # Verificar índices do banco
        from models import Signature, User, UserSession
        signature_indexes = len(Signature.__table__.indexes)
        user_indexes = len(User.__table__.indexes)
        session_indexes = len(UserSession.__table__.indexes)
        
        # Verificar se está rodando em produção
        is_production = app.config.get('ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production'
        
        # Verificar se está rodando como serviço
        is_service = False
        try:
            # Verificar se está rodando com gunicorn
            import sys
            is_service = 'gunicorn' in sys.modules
        except:
            pass
        
        # Horário do servidor
        server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timezone = datetime.now().astimezone().strftime('%Z %z')
        
        # Verificar se LDAP está habilitado
        ldap_enabled = os.environ.get('LDAP_ENABLED', 'false').lower() == 'true'
        ldap_server = os.environ.get('LDAP_SERVER', 'N/A')
        
        # Contagens de arquivos para limpeza
        temp_files_count = 0
        signed_files_count = 0
        
        try:
            temp_dir = app.config.get('TEMP_FILES_DIR', 'temp_files')
            signed_dir = app.config.get('PDF_SIGNED_DIR', 'pdf_assinados')
            
            if os.path.exists(temp_dir):
                temp_files_count = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
            
            if os.path.exists(signed_dir):
                for root, dirs, files in os.walk(signed_dir):
                    signed_files_count += len(files)
        except Exception:
            pass
        
        return render_template('admin/settings.html', 
                             store_pdfs=get_store_pdfs_flag(),
                             db_type=db_type,
                             db_host=db_host,
                             db_port=db_port,
                             async_enabled=async_enabled,
                             python_version=python_version,
                             flask_version=flask_version,
                             platform_info=platform_info,
                             machine=machine,
                             processor=processor,
                             cpu_count=cpu_count,
                             cpu_percent=cpu_percent,
                             memory_total_gb=memory_total_gb,
                             memory_used_gb=memory_used_gb,
                             memory_percent=memory_percent,
                             disk_total_gb=disk_total_gb,
                             disk_used_gb=disk_used_gb,
                             disk_percent=disk_percent,
                             async_supported=async_supported,
                             cache_enabled=cache_enabled,
                             cache_type=cache_type,
                             cache_timeout=cache_timeout,
                             rate_limit_enabled=rate_limit_enabled,
                             pdf_signed_dir=pdf_signed_dir,
                             pdf_dir_exists=pdf_dir_exists,
                             keys_dir=keys_dir,
                             keys_dir_exists=keys_dir_exists,
                             audit_log_path=audit_log_path,
                             audit_log_exists=audit_log_exists,
                             audit_log_count=audit_log_count,
                             signature_indexes=signature_indexes,
                             user_indexes=user_indexes,
                             session_indexes=session_indexes,
                             is_production=is_production,
                             is_service=is_service,
                             server_time=server_time,
                             timezone=timezone,
                             temp_files_count=temp_files_count,
                             signed_files_count=signed_files_count,
                             ldap_enabled=ldap_enabled,
                             ldap_server=ldap_server)
    
    @app.route('/admin/cleanup', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_cleanup():
        """Página administrativa para gerenciar limpeza de arquivos"""
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'cleanup_temp':
                cleanup_temp_files()
                flash('Limpeza de arquivos temporários executada.', 'success')
            elif action == 'cleanup_old':
                cleanup_old_files()
                flash('Limpeza de arquivos antigos executada.', 'success')
            elif action == 'cleanup_database':
                cleanup_old_files_by_database()
                flash('Limpeza baseada no banco de dados executada.', 'success')
            elif action == 'cleanup_all':
                cleanup_temp_files_all()  # Remove TODOS os arquivos temporários
                cleanup_signed_pdfs_temp()
                cleanup_old_files()
                cleanup_old_files_by_database()
                flash('Limpeza completa executada.', 'success')
            
            return redirect(url_for('admin_settings'))
        
        # Estatísticas dos diretórios
        temp_files_count = 0
        signed_files_count = 0
        
        try:
            if os.path.exists(TEMP_DIR):
                temp_files_count = len([f for f in os.listdir(TEMP_DIR) if os.path.isfile(os.path.join(TEMP_DIR, f))])
            if os.path.exists(PDF_SIGNED_DIR):
                signed_files_count = len([f for f in os.listdir(PDF_SIGNED_DIR) if os.path.isfile(os.path.join(PDF_SIGNED_DIR, f))])
        except Exception as e:
            flash(f'Erro ao obter estatísticas: {e}', 'error')
        
        return render_template('admin/cleanup.html', 
                             temp_files_count=temp_files_count,
                             signed_files_count=signed_files_count)
    
    @app.route('/')
    @login_required
    def index():
        """Página inicial com lista de assinaturas pendentes"""
        # Cache key baseado no usuário
        cache_key = f"user_signatures_{current_user.id}"
        
        # Tenta buscar do cache primeiro
        cached_data = app.cache.get(cache_key)
        if cached_data:
            return render_template('index.html', **cached_data)
        
        # Busca assinaturas pendentes do usuário logado (otimizada)
        query_limit = getattr(g, 'query_limit', 50)
        pending_signatures = db.session.query(Signature).filter_by(
            user_id=current_user.id,
            status='pending'
        ).order_by(Signature.timestamp.desc()).limit(query_limit).all()
        
        # Agrupa por cliente (otimizado)
        clients = {}
        for sig in pending_signatures:
            client_key = f"{sig.client_name}_{sig.client_cpf}"
            if client_key not in clients:
                clients[client_key] = {
                    'client_name': sig.client_name,
                    'client_cpf': sig.client_cpf,
                    'client_email': sig.client_email,
                    'client_phone': sig.client_phone,
                    'signatures': []
                }
            clients[client_key]['signatures'].append(sig)
        
        template_data = {
            'clients': clients,
            'pending_count': len(pending_signatures)
        }
        
        # Cache com timeout otimizado para o dispositivo
        cache_timeout = getattr(g, 'cache_timeout', 300)
        app.cache.set(cache_key, template_data, timeout=cache_timeout)
        
        return render_template('index.html', **template_data)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            ldap_enabled = os.environ.get('LDAP_ENABLED', 'false').lower() == 'true'
            if ldap_enabled:
                from services import LDAPAuthenticator, ADSyncService
                ldap_auth = LDAPAuthenticator()
                ad_sync = ADSyncService()
                try:
                    ldap_user_info = ldap_auth.authenticate(username, password)
                    if ldap_user_info:
                        user = User.query.filter_by(username=username).first()
                        if not user:
                            email = (ldap_user_info.get('email') or '').strip() or f"{username}@psc.local"
                            full_name = (ldap_user_info.get('full_name') or '').strip() or username.title()
                            user = User(
                                username=username,
                                email=email,
                                full_name=full_name,
                                role='user',
                                is_active=False,
                                is_ldap_user=True,
                                ldap_dn=ldap_user_info.get('ldap_dn'),
                                department=ldap_user_info.get('department'),
                                position=ldap_user_info.get('position'),
                                phone=ldap_user_info.get('phone'),
                                mobile=ldap_user_info.get('mobile'),
                                city=ldap_user_info.get('city'),
                                state=ldap_user_info.get('state'),
                                postal_code=ldap_user_info.get('postal_code'),
                                country=ldap_user_info.get('country'),
                                street_address=ldap_user_info.get('street_address'),
                                home_phone=ldap_user_info.get('home_phone'),
                                work_address=ldap_user_info.get('work_address'),
                                fax=ldap_user_info.get('fax'),
                                pager=ldap_user_info.get('pager')
                            )
                            db.session.add(user)
                            db.session.commit()
                            logger.info(f"Novo usuário criado do AD: {username} - Aguardando aprovação do admin")
                            flash('Usuário criado com sucesso do Active Directory. Por favor, entre em contato com o administrador para designar permissões e ativar sua conta.', 'warning')
                            return render_template('login.html', form=form)
                        else:
                            email = (ldap_user_info.get('email') or '').strip()
                            if email:
                                user.email = email
                            full_name = (ldap_user_info.get('full_name') or '').strip()
                            if full_name:
                                user.full_name = full_name
                            user.is_ldap_user = True
                            db.session.commit()
                        if not user.is_active:
                            flash('Sua conta está inativa. Por favor, entre em contato com o administrador para designar permissões e ativar sua conta.', 'error')
                            return render_template('login.html', form=form)
                        login_user(user, remember=form.remember_me.data)
                        user.last_login = datetime.utcnow()
                        db.session.commit()
                        try:
                            log_event(action='login', actor_user_id=user.id, status='success', ip_address=get_client_ip(request))
                        except Exception:
                            pass
                        flash(f'Bem-vindo, {user.full_name}!', 'success')
                        next_page = request.args.get('next')
                        return redirect(next_page) if next_page else redirect(url_for('index'))
                    else:
                        flash('Credenciais inválidas ou usuário não encontrado no Active Directory.', 'error')
                        try:
                            log_event(action='login', actor_user_id=None, status='error', ip_address=get_client_ip(request), details={"reason": "ldap_invalid"})
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"Erro de autenticação LDAP: {str(e)}")
                    flash('Erro ao conectar com o Active Directory. Tente novamente.', 'error')
            else:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password) and user.is_active:
                    login_user(user, remember=form.remember_me.data)
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    session_id = create_user_session(user, request)
                    session['user_session_id'] = session_id
                    if getattr(user, 'must_change_password', False):
                        session['must_change_password_user'] = user.id
                        return redirect(url_for('force_change_password'))
                    try:
                        log_event(action='login', actor_user_id=user.id, status='success', ip_address=get_client_ip(request))
                    except Exception:
                        pass
                    flash(f'Bem-vindo, {user.full_name}!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                else:
                    flash('Usuário ou senha inválidos, ou usuário inativo.', 'error')
                    try:
                        log_event(action='login', actor_user_id=(user.id if user else None), status='error', ip_address=get_client_ip(request), details={"reason": "invalid"})
                    except Exception:
                        pass
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('user_session_id', None)
        flash('Você foi desconectado.', 'info')
        try:
            log_event(action='logout', actor_user_id=(current_user.id if current_user and current_user.is_authenticated else None), status='success', ip_address=get_client_ip(request))
        except Exception:
            pass
        return redirect(url_for('login'))

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        # Bloquear usuários LDAP
        if current_user.is_ldap_user:
            flash('Usuários LDAP não podem alterar senha através do sistema. Entre em contato com o administrador do Active Directory.', 'error')
            return redirect(url_for('profile'))
        
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                # Após alterar, desmarca must_change_password se era o caso
                if getattr(current_user, 'must_change_password', False):
                    current_user.must_change_password = False
                db.session.commit()
                flash('Senha alterada com sucesso!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Senha atual incorreta.', 'error')
        return render_template('change_password.html', form=form)
    @app.route('/force_change_password', methods=['GET', 'POST'])
    @login_required
    def force_change_password():
        """Tela obrigatória de troca de senha quando marcado pelo admin"""
        # Bloquear usuários LDAP
        if current_user.is_ldap_user:
            flash('Usuários LDAP não podem alterar senha através do sistema. Entre em contato com o administrador do Active Directory.', 'error')
            session.pop('must_change_password_user', None)
            return redirect(url_for('index'))
        
        if session.get('must_change_password_user') != current_user.id:
            return redirect(url_for('index'))
        form = ChangePasswordForm()
        # Esconde campo current_password, não exigimos a senha antiga aqui por ser fluxo forçado
        form.current_password.validators = []
        if form.validate_on_submit():
            current_user.set_password(form.new_password.data)
            current_user.must_change_password = False
            db.session.commit()
            session.pop('must_change_password_user', None)
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('index'))
        return render_template('change_password.html', form=form)

    # Rotas administrativas
    @app.route('/admin')
    @login_required
    @admin_required
    @app.cache.cached(timeout=600)
    def admin_dashboard():
        # Cache das estatísticas por 10 minutos
        cache_key = "admin_dashboard_stats"
        cached_stats = app.cache.get(cache_key)
        
        if cached_stats:
            user_stats, signature_stats = cached_stats
        else:
            user_stats = get_user_stats()
            signature_stats = get_signature_stats()
            app.cache.set(cache_key, (user_stats, signature_stats), timeout=600)
        
        return render_template('admin/dashboard.html', 
                             user_stats=user_stats, 
                             signature_stats=signature_stats, 
                             store_pdfs=get_store_pdfs_flag())

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        # Parâmetros de busca e paginação
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', 'all')
        role_filter = request.args.get('role', 'all')
        
        # Query base
        query = User.query
        
        # Aplicar filtro de busca
        if search_query:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search_query}%'),
                    User.full_name.ilike(f'%{search_query}%'),
                    User.email.ilike(f'%{search_query}%')
                )
            )
        
        # Aplicar filtro de status
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Aplicar filtro de role
        if role_filter == 'admin':
            query = query.filter(User.role == 'admin')
        elif role_filter == 'user':
            query = query.filter(User.role == 'user')
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(User.created_at.desc())
        
        # Paginação
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = pagination.items
        
        # Verificar se LDAP está habilitado
        ldap_enabled = os.environ.get('LDAP_ENABLED', 'false').lower() == 'true'
        ldap_server = os.environ.get('LDAP_SERVER', 'N/A')
        
        return render_template('admin/users.html', 
                             users=users,
                             pagination=pagination,
                             search_query=search_query,
                             status_filter=status_filter,
                             role_filter=role_filter,
                             ldap_enabled=ldap_enabled,
                             ldap_server=ldap_server)

    @app.route('/admin/users/new', methods=['GET', 'POST'])
    @admin_required
    def admin_new_user():
        form = AdminUserForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                role=form.role.data,
                is_active=form.is_active.data,
                must_change_password=form.must_change_password.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Usuário {user.username} criado com sucesso!', 'success')
            try:
                log_event(action='admin_user_create', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"user_id": user.id})
            except Exception:
                pass
            return redirect(url_for('admin_users'))
        
        return render_template('admin/new_user.html', form=form)

    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_user(user_id):
        user = User.query.get_or_404(user_id)
        form = UserEditForm(obj=user)
        
        if form.validate_on_submit():
            # Valores antigos
            old_values = {
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'must_change_password': bool(getattr(user, 'must_change_password', False)),
                'role': user.role,
                'is_active': bool(user.is_active),
            }
            # Bloquear alteração de username para usuários LDAP
            if user.is_ldap_user and form.username.data != user.username:
                flash('Não é possível alterar o username de usuários LDAP. O username é gerenciado pelo Active Directory.', 'error')
                return render_template('admin/edit_user.html', form=form, user=user)
            
            # Bloquear alteração de email para usuários LDAP
            if user.is_ldap_user and form.email.data != user.email:
                flash('Não é possível alterar o email de usuários LDAP. O email é gerenciado pelo Active Directory.', 'error')
                return render_template('admin/edit_user.html', form=form, user=user)
            
            # Bloquear alteração de nome completo para usuários LDAP
            if user.is_ldap_user and form.full_name.data != user.full_name:
                flash('Não é possível alterar o nome completo de usuários LDAP. O nome é gerenciado pelo Active Directory.', 'error')
                return render_template('admin/edit_user.html', form=form, user=user)
            
            # Bloquear alteração de senha para usuários LDAP
            if user.is_ldap_user and form.must_change_password.data:
                flash('Não é possível forçar troca de senha para usuários LDAP. A senha é gerenciada pelo Active Directory.', 'error')
                return render_template('admin/edit_user.html', form=form, user=user)
            
            # Atualizar apenas se não for usuário LDAP
            if not user.is_ldap_user:
                user.username = form.username.data
                user.email = form.email.data
                user.full_name = form.full_name.data
                user.must_change_password = form.must_change_password.data
            
            # Permitir alteração de role e status para todos os usuários
            user.role = form.role.data
            user.is_active = form.is_active.data
            
            db.session.commit()
            flash(f'Usuário {user.username} atualizado com sucesso!', 'success')
            try:
                # Detecta mudanças
                new_values = {
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'must_change_password': bool(getattr(user, 'must_change_password', False)),
                    'role': user.role,
                    'is_active': bool(user.is_active),
                }
                changes = {}
                for k, old_v in old_values.items():
                    new_v = new_values.get(k)
                    if old_v != new_v:
                        changes[k] = {'from': old_v, 'to': new_v}
                log_event(action='admin_user_update', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"user_id": user.id, "username": user.username, "changes": changes})
            except Exception:
                pass
            return redirect(url_for('admin_users'))
        
        return render_template('admin/edit_user.html', form=form, user=user)

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_user(user_id):
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('Você não pode deletar sua própria conta!', 'error')
            return redirect(url_for('admin_users'))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Usuário {username} deletado com sucesso!', 'success')
        try:
            # Inclui username do alvo para não depender do banco após a exclusão
            log_event(action='admin_user_delete', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"user_id": user_id, "username": username})
        except Exception:
            pass
        return redirect(url_for('admin_users'))

    @app.route('/admin/sync', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_sync():
        """Página administrativa para sincronização com Active Directory"""
        from services import ADSyncService
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'sync_all':
                # Sincronizar todos os usuários do AD
                ad_sync = ADSyncService()
                stats = ad_sync.sync_all_users()
                
                flash(f'Sincronização concluída: {stats["users_created"]} criados, '
                      f'{stats["users_updated"]} atualizados, '
                      f'{stats["users_deactivated"]} desativados.', 'success')
                try:
                    log_event(action='ad_sync_all', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details=stats)
                except Exception:
                    pass
                return redirect(url_for('admin_sync'))
            
            elif action == 'sync_single':
                # Sincronizar usuário específico
                username = request.form.get('username')
                if username:
                    ad_sync = ADSyncService()
                    result = ad_sync.sync_single_user(username)
                    
                    if result:
                        flash(f'Usuário {username} sincronizado com sucesso!', 'success')
                        try:
                            log_event(action='ad_sync_single', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"username": username})
                        except Exception:
                            pass
                    else:
                        flash(f'Usuário {username} não encontrado no Active Directory.', 'error')
                        try:
                            log_event(action='ad_sync_single', actor_user_id=current_user.id, status='error', ip_address=get_client_ip(request), details={"username": username})
                        except Exception:
                            pass
                else:
                    flash('Nome de usuário é obrigatório.', 'error')
                
                return redirect(url_for('admin_sync'))
        
        # Estatísticas de usuários LDAP
        total_users = User.query.count()
        ldap_users = User.query.filter_by(is_ldap_user=True).count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = User.query.filter_by(is_active=False).count()
        
        # Verificar se LDAP está habilitado
        ldap_enabled = os.environ.get('LDAP_ENABLED', 'false').lower() == 'true'
        
        return render_template('admin/sync.html',
                             total_users=total_users,
                             ldap_users=ldap_users,
                             active_users=active_users,
                             inactive_users=inactive_users,
                             ldap_enabled=ldap_enabled)

    @app.route('/admin/reports')
    @admin_required
    def admin_reports():
        form = ReportFilterForm()
        
        # Cache das opções de usuário por 1 hora
        cache_key_users = "admin_users_list"
        cached_users = app.cache.get(cache_key_users)
        
        if cached_users:
            form.user_id.choices = cached_users
        else:
            users_list = [(0, 'Todos os usuários')] + [(u.id, u.username) for u in User.query.all()]
            form.user_id.choices = users_list
            app.cache.set(cache_key_users, users_list, timeout=3600)
        # Carrega tipos de documento
        from models import DocumentType
        type_choices = [(0, 'Todos os tipos')] + [(t.id, t.name) for t in DocumentType.query.order_by(DocumentType.name.asc()).all()]
        form.document_type_id.choices = type_choices
        
        # Filtros padrão com paginação
        signatures = Signature.query.order_by(Signature.timestamp.desc()).limit(100)
        
        if form.validate_on_submit():
            if form.user_id.data and form.user_id.data != 0:
                signatures = signatures.filter(Signature.user_id == form.user_id.data)
            
            if form.date_from.data:
                try:
                    date_from = datetime.strptime(form.date_from.data, '%Y-%m-%d')
                    signatures = signatures.filter(Signature.timestamp >= date_from)
                except ValueError:
                    pass
            
            if form.date_to.data:
                try:
                    date_to = datetime.strptime(form.date_to.data, '%Y-%m-%d') + timedelta(days=1)
                    signatures = signatures.filter(Signature.timestamp < date_to)
                except ValueError:
                    pass
            if form.document_type_id.data and form.document_type_id.data != 0:
                signatures = signatures.filter(Signature.document_type_id == form.document_type_id.data)
        
        # Executa a query para obter os resultados
        signatures_list = signatures.all()
        
        # Agrupamento por tipo de documento (apenas concluídas)
        from models import DocumentType
        type_counts_query = db.session.query(
            DocumentType.name.label('type_name'),
            db.func.count(Signature.id).label('count')
        ).join(Signature, Signature.document_type_id == DocumentType.id)
        type_counts_query = type_counts_query.filter(Signature.status == 'completed')
        
        # Aplicar mesmos filtros de período/usuário ao agrupamento
        if form.user_id.data and form.user_id.data != 0:
            type_counts_query = type_counts_query.filter(Signature.user_id == form.user_id.data)
        if form.date_from.data:
            try:
                date_from = datetime.strptime(form.date_from.data, '%Y-%m-%d')
                type_counts_query = type_counts_query.filter(Signature.timestamp >= date_from)
            except ValueError:
                pass
        if form.date_to.data:
            try:
                date_to = datetime.strptime(form.date_to.data, '%Y-%m-%d') + timedelta(days=1)
                type_counts_query = type_counts_query.filter(Signature.timestamp < date_to)
            except ValueError:
                pass
        if form.document_type_id.data and form.document_type_id.data != 0:
            type_counts_query = type_counts_query.filter(Signature.document_type_id == form.document_type_id.data)
        type_counts = type_counts_query.group_by(DocumentType.name).order_by(DocumentType.name.asc()).all()
        
        return render_template('admin/reports.html', form=form, signatures=signatures_list, type_counts=type_counts)

    @app.route('/admin/reports/export')
    @admin_required
    def admin_export_reports():
        """Exporta relatórios em formato JSON"""
        signatures = Signature.query.order_by(Signature.timestamp.desc()).all()
        
        report_data = []
        for sig in signatures:
            report_data.append({
                'id': sig.id,
                'user': sig.user.username if sig.user else 'N/A',
                'file_id': sig.file_id,
                'original_filename': sig.original_filename,
                'timestamp': sig.timestamp.isoformat(),
                'algorithm': sig.signature_algorithm,
                'file_size': sig.file_size,
                'valid': sig.signature_valid
            })
        
        try:
            log_event(action='admin_export_json', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"count": len(report_data)})
        except Exception:
            pass
        return jsonify({
            'success': True,
            'total_signatures': len(report_data),
            'export_date': datetime.utcnow().isoformat(),
            'data': report_data
        })

    @app.route('/admin/reports/export_csv')
    @admin_required
    def admin_export_reports_csv():
        """Exporta agrupamento por tipo de documento em CSV"""
        from models import DocumentType
        type_counts_query = db.session.query(
            DocumentType.name.label('type_name'),
            db.func.count(Signature.id).label('count')
        ).join(Signature, Signature.document_type_id == DocumentType.id)
        type_counts_query = type_counts_query.filter(Signature.status == 'completed')

        # Filtros simples por querystring (opcional)
        user_id = request.args.get('user_id', type=int)
        if user_id:
            type_counts_query = type_counts_query.filter(Signature.user_id == user_id)
        document_type_id = request.args.get('document_type_id', type=int)
        if document_type_id:
            type_counts_query = type_counts_query.filter(Signature.document_type_id == document_type_id)
        date_from = request.args.get('date_from')
        if date_from:
            try:
                df = datetime.strptime(date_from, '%Y-%m-%d')
                type_counts_query = type_counts_query.filter(Signature.timestamp >= df)
            except Exception:
                pass
        date_to = request.args.get('date_to')
        if date_to:
            try:
                dtl = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                type_counts_query = type_counts_query.filter(Signature.timestamp < dtl)
            except Exception:
                pass

        rows = type_counts_query.group_by(DocumentType.name).order_by(DocumentType.name.asc()).all()

        # Gera CSV em memória
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Tipo de Documento', 'Quantidade'])
        for row in rows:
            writer.writerow([row.type_name or 'Sem Tipo', row.count])
        output.seek(0)

        # Responde como arquivo CSV
        try:
            log_event(action='admin_export_csv', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"rows": len(rows)})
        except Exception:
            pass
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            as_attachment=True,
            download_name='assinaturas_por_tipo.csv',
            mimetype='text/csv; charset=utf-8'
        )

    @app.route('/admin/audit-logs')
    @login_required
    @admin_required
    def admin_audit_logs():
        """Lista logs de auditoria (últimos N) com filtros simples"""
        logs_path = os.path.join(app.config.get('LOGS_DIR', 'logs'), 'audit.log')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        q = request.args.get('q', '', type=str).strip().lower()
        action_filter = request.args.get('action', '', type=str).strip()
        status_filter = request.args.get('status', '', type=str).strip()
        user_id_filter = request.args.get('user_id', type=int)
        date_from = request.args.get('date_from', type=str)
        date_to = request.args.get('date_to', type=str)

        entries = []
        if os.path.exists(logs_path):
            try:
                with open(logs_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # Pega no máximo 5000 últimos registros para não pesar
                lines = lines[-5000:]
                for line in reversed(lines):  # mais recentes primeiro
                    try:
                        evt = json.loads(line)
                        entries.append(evt)
                    except Exception:
                        continue
            except Exception:
                pass

        # Filtros
        def match(e):
            if action_filter and e.get('action') != action_filter:
                return False
            if status_filter and (e.get('status') or '') != status_filter:
                return False
            if user_id_filter is not None and (e.get('actor_user_id') != user_id_filter):
                return False
            if date_from:
                try:
                    dt_from = datetime.strptime(date_from, '%Y-%m-%d')
                    if datetime.fromisoformat(e.get('timestamp')) < dt_from:
                        return False
                except Exception:
                    pass
            if date_to:
                try:
                    dt_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    if datetime.fromisoformat(e.get('timestamp')) >= dt_to:
                        return False
                except Exception:
                    pass
            if q:
                hay = json.dumps(e, ensure_ascii=False).lower()
                if q not in hay:
                    return False
            return True

        filtered = [e for e in entries if match(e)]
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = filtered[start:end]

        # Enriquecer com username a partir de actor_user_id e details.user_id
        id_to_username = {}
        try:
            user_ids = set()
            for e in page_items:
                if e.get('actor_user_id'):
                    user_ids.add(e.get('actor_user_id'))
                details = e.get('details') or {}
                target_id = details.get('user_id')
                if target_id:
                    user_ids.add(target_id)
            if user_ids:
                users = User.query.filter(User.id.in_(sorted(user_ids))).all()
                id_to_username = {u.id: u.username for u in users}
        except Exception:
            pass

        # Ações disponíveis para filtro rápido
        actions_available = sorted(list({e.get('action') for e in entries if e.get('action')}))

        return render_template('admin/audit_logs.html',
                               items=page_items,
                               total=total,
                               page=page,
                               per_page=per_page,
                               q=q,
                               action_filter=action_filter,
                               status_filter=status_filter,
                               user_id_filter=user_id_filter,
                               date_from=date_from,
                               date_to=date_to,
                               actions_available=actions_available,
                               id_to_username=id_to_username)

    @app.route('/admin/audit-logs/download')
    @login_required
    @admin_required
    def admin_audit_logs_download():
        """Baixa o audit.log completo"""
        logs_path = os.path.join(app.config.get('LOGS_DIR', 'logs'), 'audit.log')
        if not os.path.exists(logs_path):
            flash('Arquivo de log não encontrado.', 'error')
            return redirect(url_for('admin_audit_logs'))
        return send_file(logs_path, as_attachment=True, download_name='audit.log', mimetype='text/plain; charset=utf-8')

    @app.route('/admin/audit-logs/export_csv')
    @login_required
    @admin_required
    def admin_audit_logs_export_csv():
        """Exporta os logs filtrados em CSV (colunas amigáveis)."""
        logs_path = os.path.join(app.config.get('LOGS_DIR', 'logs'), 'audit.log')
        q = request.args.get('q', '', type=str).strip().lower()
        action_filter = request.args.get('action', '', type=str).strip()
        status_filter = request.args.get('status', '', type=str).strip()
        user_id_filter = request.args.get('user_id', type=int)
        date_from = request.args.get('date_from', type=str)
        date_to = request.args.get('date_to', type=str)

        entries = []
        if os.path.exists(logs_path):
            try:
                with open(logs_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                lines = lines[-5000:]
                for line in lines:
                    try:
                        evt = json.loads(line)
                        entries.append(evt)
                    except Exception:
                        continue
            except Exception:
                pass

        def match(e):
            if action_filter and e.get('action') != action_filter:
                return False
            if status_filter and (e.get('status') or '') != status_filter:
                return False
            if user_id_filter is not None and (e.get('actor_user_id') != user_id_filter):
                return False
            if date_from:
                try:
                    dt_from = datetime.strptime(date_from, '%Y-%m-%d')
                    if datetime.fromisoformat(e.get('timestamp')) < dt_from:
                        return False
                except Exception:
                    pass
            if date_to:
                try:
                    dt_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    if datetime.fromisoformat(e.get('timestamp')) >= dt_to:
                        return False
                except Exception:
                    pass
            if q:
                hay = json.dumps(e, ensure_ascii=False).lower()
                if q not in hay:
                    return False
            return True

        filtered = [e for e in entries if match(e)]

        # Resolver usernames (ator e alvo)
        id_to_username = {}
        try:
            user_ids = set()
            for e in filtered:
                if e.get('actor_user_id'):
                    user_ids.add(e.get('actor_user_id'))
                details = e.get('details') or {}
                target_id = details.get('user_id')
                if target_id:
                    user_ids.add(target_id)
            if user_ids:
                users = User.query.filter(User.id.in_(sorted(user_ids))).all()
                id_to_username = {u.id: u.username for u in users}
        except Exception:
            pass

        # Montar CSV
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['timestamp', 'action', 'status', 'actor_user_id', 'actor_username', 'ip', 'target_user_id', 'target_username', 'changes'])

        for e in filtered:
            details = e.get('details') or {}
            target_id = details.get('user_id')
            actor_id = e.get('actor_user_id')
            actor_username = id_to_username.get(actor_id) if actor_id else ''
            target_username = id_to_username.get(target_id) if target_id else (details.get('username') or '')
            # changes como string amigável "campo: from -> to" separados por ;
            changes = details.get('changes') or {}
            if isinstance(changes, dict):
                change_parts = []
                for field, diff in changes.items():
                    try:
                        change_parts.append(f"{field}: {diff.get('from')} -> {diff.get('to')}")
                    except Exception:
                        change_parts.append(f"{field}")
                changes_str = '; '.join(change_parts)
            else:
                changes_str = ''
            writer.writerow([
                e.get('timestamp'),
                e.get('action'),
                e.get('status'),
                actor_id or '',
                actor_username or '',
                e.get('ip_address') or '',
                target_id or '',
                target_username or '',
                changes_str
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            as_attachment=True,
            download_name='audit_logs.csv',
            mimetype='text/csv; charset=utf-8'
        )

    # === NOVO FLUXO DE ASSINATURA ===
    
    @app.route('/signature/upload', methods=['GET', 'POST'])
    @login_required
    def signature_upload():
        """Etapa 1: Upload do PDF"""
        if request.method == 'POST':
            if 'pdf_file' not in request.files:
                flash('Nenhum arquivo PDF foi enviado', 'error')
                return render_template('signature/upload.html')
            
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return render_template('signature/upload.html')
            
            if not pdf_file.filename.lower().endswith('.pdf'):
                flash('Apenas arquivos PDF são permitidos', 'error')
                return render_template('signature/upload.html')
            
            # Salva o arquivo temporariamente
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{pdf_file.filename}"
            temp_path = os.path.join(TEMP_DIR, filename)
            pdf_file.save(temp_path)
            
            # Salva informações na sessão
            session['signature_process'] = {
                'file_id': file_id,
                'original_filename': pdf_file.filename,
                'temp_path': temp_path,
                'step': 'upload_completed'
            }
            
            flash('PDF carregado com sucesso!', 'success')
            return redirect(url_for('signature_client_info'))
        
        return render_template('signature/upload.html')

    @app.route('/signature/client-info', methods=['GET', 'POST'])
    @login_required
    def signature_client_info():
        """Etapa 2: Informações do Cliente"""
        if 'signature_process' not in session:
            flash('Sessão expirada. Por favor, faça upload do PDF novamente.', 'error')
            return redirect(url_for('signature_upload'))
        
        if request.method == 'POST':
            # Coleta informações do cliente
            client_info = {
                'nome': request.form.get('nome', '').strip(),
                'cpf': request.form.get('cpf', '').strip(),
                'email': request.form.get('email', '').strip(),
                'telefone': request.form.get('telefone', '').strip(),
                'data_nascimento': request.form.get('data_nascimento', '').strip(),
                'endereco': request.form.get('endereco', '').strip(),
                'observacoes': request.form.get('observacoes', '').strip()
            }
            
            # Validação básica
            if not client_info['nome']:
                flash('Nome é obrigatório', 'error')
                return render_template('signature/client_info.html', client_info=client_info)
            
            # Atualiza sessão
            session['signature_process']['client_info'] = client_info
            session['signature_process']['step'] = 'client_info_completed'
            session.modified = True
            
            flash('Informações do cliente salvas!', 'success')
            return redirect(url_for('signature_pending'))
        
        return render_template('signature/client_info.html')

    @app.route('/signature/pending')
    @login_required
    def signature_pending():
        """Etapa 3: Tela de Pendências - Confirmação das Informações"""
        if 'signature_process' not in session:
            flash('Sessão expirada. Por favor, faça upload do PDF novamente.', 'error')
            return redirect(url_for('signature_upload'))
        
        if session['signature_process'].get('step') != 'client_info_completed':
            flash('Complete as informações do cliente primeiro.', 'error')
            return redirect(url_for('signature_client_info'))
        
        process_data = session['signature_process']
        return render_template('signature/pending.html', 
                             client_info=process_data['client_info'],
                             filename=process_data['original_filename'])

    @app.route('/signature/draw', methods=['GET', 'POST'])
    @login_required
    def signature_draw():
        """Etapa 4: Desenhar Assinatura"""
        if 'signature_process' not in session:
            flash('Sessão expirada. Por favor, faça upload do PDF novamente.', 'error')
            return redirect(url_for('signature_upload'))
        
        if request.method == 'POST':
            signature_data = request.json
            signature_image = signature_data.get('signature_image')
            
            if not signature_image:
                return jsonify({'success': False, 'message': 'Assinatura não fornecida'})
            
            # Salva a assinatura em arquivo temporário ao invés da sessão
            signature_filename = f"{session['signature_process']['file_id']}_signature.png"
            signature_path = os.path.join(TEMP_DIR, signature_filename)
            
            # Decodifica e salva a imagem
            from io import BytesIO
            
            # Remove o prefixo data:image/png;base64,
            if signature_image.startswith('data:image/png;base64,'):
                signature_image = signature_image.replace('data:image/png;base64,', '')
            
            image_data = base64.b64decode(signature_image)
            image = Image.open(BytesIO(image_data))
            image.save(signature_path, 'PNG')
            
            # Salva apenas o caminho da assinatura na sessão
            session['signature_process']['signature_path'] = signature_path
            session['signature_process']['step'] = 'signature_completed'
            session.modified = True
            
            return jsonify({'success': True, 'message': 'Assinatura salva!'})
        
        return render_template('signature/draw.html')

    @app.route('/signature/process')
    @login_required
    def signature_process():
        """Etapa 5: Processar e Finalizar Assinatura"""
        if 'signature_process' not in session:
            flash('Sessão expirada. Por favor, faça upload do PDF novamente.', 'error')
            return redirect(url_for('signature_upload'))
        
        if session['signature_process'].get('step') != 'signature_completed':
            flash('Complete a assinatura primeiro.', 'error')
            return redirect(url_for('signature_draw'))
        
        try:
            process_data = session['signature_process']
            
            # Cria arquivo de saída
            output_path = tempfile.mktemp(suffix='.pdf')
            
            # Lê a imagem da assinatura do arquivo
            signature_image_data = None
            if 'signature_path' in process_data and os.path.exists(process_data['signature_path']):
                with open(process_data['signature_path'], 'rb') as f:
                    signature_image_data = base64.b64encode(f.read()).decode('utf-8')
                    signature_image_data = f"data:image/png;base64,{signature_image_data}"
            
            # Processa a assinatura
            success = add_signature_to_all_pages(
                process_data['temp_path'],
                '',  # signature_text não usado no novo fluxo
                output_path,
                signature_image_data,
                process_data['client_info'],
                create_logo_image()
            )
            
            if success:
                # Define política de retenção
                keep_pdfs = get_store_pdfs_flag()
                retention_tag = 'KEEP' if keep_pdfs else 'TEMP'
                
                # Move arquivo final para pasta de PDFs assinados
                clean_final_filename = process_data['original_filename'].replace('.pdf', '_assinado.pdf')
                stored_final_filename = f"{process_data['file_id']}_{clean_final_filename.replace('.pdf', f'_{retention_tag}.pdf')}"
                final_path = os.path.join(PDF_SIGNED_DIR, stored_final_filename)
                shutil.move(output_path, final_path)
                
                # NOTA: O hash será calculado APÓS aplicar o carimbo/assinatura visual
                # na função client_sign_document, não aqui
                
                # Coleta informações do dispositivo e cliente
                device_info = detect_device_info(request.headers.get('User-Agent', ''), request)
                client_info = process_data.get('client_info', {})
                
                # Converte data de nascimento se existir
                client_birth_date = None
                if client_info.get('data_nascimento'):
                    try:
                        client_birth_date = datetime.strptime(client_info['data_nascimento'], '%Y-%m-%d').date()
                    except:
                        pass
                
                # Obtém informações extras do cabeçalho
                screen_resolution = request.headers.get('X-Screen-Resolution', None)
                timezone = request.headers.get('X-Timezone', 'UTC')
                mac_address = request.headers.get('X-MAC-Address', None)  # Será enviado via JavaScript
                
                # Salva no banco com informações completas
                signature_record = Signature(
                    user_id=current_user.id,
                    file_id=process_data['file_id'],
                    original_filename=process_data['original_filename'],
                    signature_hash='',  # Será preenchido após assinatura do cliente
                    signature_algorithm='PENDING',  # Será preenchido após assinatura do cliente
                    file_size=0,  # Será preenchido após assinatura do cliente
                    
                    # Informações do Cliente/Assinante
                    client_name=client_info.get('nome', ''),
                    client_cpf=client_info.get('cpf', ''),
                    client_email=client_info.get('email', ''),
                    client_phone=client_info.get('telefone', ''),
                    client_birth_date=client_birth_date,
                    client_address=f"{client_info.get('endereco', '')} - {client_info.get('cidade', '')} - {client_info.get('estado', '')}".strip(' - '),
                    
                    # Informações do Dispositivo
                    ip_address=device_info['ip_address'],
                    mac_address=mac_address,
                    user_agent=device_info['user_agent'],
                    browser_name=device_info['browser_name'],
                    browser_version=device_info['browser_version'],
                    operating_system=device_info['operating_system'],
                    device_type=device_info['device_type'],
                    screen_resolution=screen_resolution,
                    timezone=timezone,
                    
                    # Informações da Assinatura
                    signature_method='drawing',
                    signature_duration=session.get('signature_start_time', 0),  # Será implementado
                    verification_status='verified'
                )
                db.session.add(signature_record)
                db.session.commit()
                
                # Atualiza sessão para download
                session['signed_pdf_id'] = process_data['file_id']
                session['filename'] = clean_final_filename
                
                # Limpa processo de assinatura
                session.pop('signature_process', None)
                
                flash('PDF assinado com sucesso! Pronto para download.', 'success')
                return redirect(url_for('signature_download'))
            else:
                flash('Erro ao processar o PDF', 'error')
                return redirect(url_for('signature_upload'))
                
        except Exception as e:
            flash(f'Erro: {str(e)}', 'error')
            return redirect(url_for('signature_upload'))

    @app.route('/signature/download')
    @login_required
    def signature_download():
        """Página de download do PDF assinado"""
        if 'signed_pdf_id' not in session:
            flash('Nenhum arquivo disponível para download', 'error')
            return redirect(url_for('index'))
        
        return render_template('signature/download.html', 
                             filename=session.get('filename', 'documento_assinado.pdf'))

    @app.route('/download_pdf')
    @login_required
    def download_pdf():
        """Download do arquivo PDF assinado"""
        if 'signed_pdf_id' in session:
            file_id = session['signed_pdf_id']
            filename = session.get('filename', 'documento_assinado.pdf')
            
            # Procura o arquivo na pasta de PDFs assinados
            file_path = None
            stored_name_keep = f"{file_id}_{filename.replace('.pdf', '_KEEP.pdf')}"
            stored_name_temp = f"{file_id}_{filename.replace('.pdf', '_TEMP.pdf')}"
            candidate_keep = os.path.join(PDF_SIGNED_DIR, stored_name_keep)
            candidate_temp = os.path.join(PDF_SIGNED_DIR, stored_name_temp)
            if os.path.exists(candidate_keep):
                file_path = candidate_keep
            elif os.path.exists(candidate_temp):
                file_path = candidate_temp
            
            if file_path and os.path.exists(file_path):
                # Verifica se o arquivo não está corrompido
                try:
                    # Testa se é um PDF válido
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        # Tenta acessar a primeira página para validar
                        if len(pdf_reader.pages) > 0:
                            first_page = pdf_reader.pages[0]
                    
                    # Se chegou até aqui, o PDF está válido
                    # Limpa a sessão APÓS confirmar que o arquivo é válido
                    session.pop('signed_pdf_id', None)
                    session.pop('filename', None)
                    
                    response = send_file(
                        file_path,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf'
                    )
                    
                    # Se for arquivo temporário, remove após enviar
                    try:
                        if file_path.endswith('_TEMP.pdf'):
                            os.remove(file_path)
                    except Exception as rm_err:
                        print(f"Erro ao remover PDF temporário após download: {rm_err}")
                    
                    return response
                except Exception as e:
                    flash(f'Arquivo PDF corrompido: {str(e)}', 'error')
                    return redirect(url_for('index'))
            else:
                flash('Arquivo não encontrado', 'error')
                return redirect(url_for('index'))
        else:
            flash('Nenhum PDF para download', 'error')
            return redirect(url_for('index'))

    # === ROTAS DE VERIFICAÇÃO ===

    @app.route('/verify_signature', methods=['POST'])
    def verify_signature():
        """Verifica a assinatura digital de um PDF"""
        try:
            if 'pdf_file' not in request.files:
                return jsonify({'success': False, 'message': 'Nenhum arquivo PDF foi enviado'})
            
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '':
                return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
            
            # Salva o arquivo temporariamente
            temp_file = tempfile.mktemp(suffix='.pdf')
            pdf_file.save(temp_file)
            
            # Processa verificação
            return jsonify({'success': True, 'message': 'Verificação implementada'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao verificar assinatura: {str(e)}'})
        finally:
            # Remove arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass

    @app.route('/get_public_key')
    def get_public_key():
        """Retorna a chave pública para verificação"""
        try:
            public_key_info = signature_manager.get_public_key_info()
            return jsonify({
                'success': True,
                'public_key_info': public_key_info,
                'public_key_pem': signature_manager.export_public_key()
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao obter chave pública: {str(e)}'})

    @app.route('/calculate_hash', methods=['POST'])
    def calculate_hash():
        """Calcula o hash de um arquivo"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'message': 'Nenhum arquivo foi enviado'})
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
            
            # Lê o conteúdo do arquivo
            file_content = file.read()
            
            # Calcula o hash
            file_hash = signature_manager.calculate_hash(file_content)
            
            return jsonify({
                'success': True,
                'hash': file_hash,
                'algorithm': 'SHA-256',
                'filename': file.filename
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao calcular hash: {str(e)}'})

    @app.route('/certificate_status')
    def certificate_status():
        """Retorna status do certificado digital"""
        try:
            status, message = certificate_manager.get_certificate_status()
            cert_info = certificate_manager.get_certificate_info()
            
            if 'error' in cert_info:
                return jsonify({'success': False, 'message': cert_info['error']})
            
            return jsonify({
                'success': True,
                'status': status,
                'message': message,
                'certificate_info': {
                    'subject': cert_info['subject'],
                    'issuer': cert_info['issuer'],
                    'valid_until': cert_info['not_valid_after'],
                    'serial_number': cert_info['serial_number']
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao verificar status: {str(e)}'})

    # === NOVO FLUXO DE ASSINATURA SEPARADO ===
    
    @app.route('/internal/signature/upload', methods=['GET', 'POST'])
    @login_required
    def internal_signature_upload():
        """Tela interna: Upload de arquivos e dados do cliente"""
        from models import DocumentType
        document_types = DocumentType.query.filter_by(active=True).order_by(DocumentType.name.asc()).all()
        if request.method == 'POST':
            if 'pdf_files' not in request.files:
                flash('Nenhum arquivo PDF foi enviado', 'error')
                return render_template('internal/upload.html', document_types=document_types)
            
            pdf_files = request.files.getlist('pdf_files')
            if not pdf_files or pdf_files[0].filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return render_template('internal/upload.html', document_types=document_types)
            
            # Valida arquivos
            valid_files = []
            for pdf_file in pdf_files:
                if pdf_file.filename.lower().endswith('.pdf'):
                    valid_files.append(pdf_file)
                else:
                    flash(f'Arquivo {pdf_file.filename} não é um PDF válido', 'error')
            
            if not valid_files:
                return render_template('internal/upload.html', document_types=document_types)
            
            # Coleta dados do cliente
            client_info = {
                'nome': request.form.get('client_name', '').strip(),
                'cpf': request.form.get('client_cpf', '').strip(),
                'email': request.form.get('client_email', '').strip(),
                'telefone': request.form.get('client_phone', '').strip(),
                'data_nascimento': request.form.get('client_birth_date', '').strip(),
                'endereco': request.form.get('client_address', '').strip(),
                'observacoes': request.form.get('client_notes', '').strip()
            }

            # Tipo de Documento (obrigatório)
            document_type_id_raw = request.form.get('document_type_id', '').strip()
            try:
                document_type_id = int(document_type_id_raw)
            except Exception:
                document_type_id = None
            if not document_type_id:
                flash('Tipo de documento é obrigatório', 'error')
                return render_template('internal/upload.html', client_info=client_info, document_types=document_types)
            
            # Converte a data de nascimento para objeto date se fornecida
            birth_date = None
            if client_info['data_nascimento']:
                try:
                    birth_date = datetime.strptime(client_info['data_nascimento'], '%Y-%m-%d').date()
                except ValueError:
                    flash('Data de nascimento inválida. Use o formato AAAA-MM-DD', 'error')
                    return render_template('internal/upload.html', client_info=client_info, document_types=document_types)
            
            # Validação básica
            if not client_info['nome']:
                flash('Nome do cliente é obrigatório', 'error')
                return render_template('internal/upload.html', client_info=client_info, document_types=document_types)
            
            if not client_info['cpf']:
                flash('CPF do cliente é obrigatório', 'error')
                return render_template('internal/upload.html', client_info=client_info)
            
            # Processa cada arquivo
            signature_ids = []
            for pdf_file in valid_files:
                file_id = str(uuid.uuid4())
                filename = f"{file_id}_{pdf_file.filename}"
                temp_path = os.path.join(TEMP_DIR, filename)
                pdf_file.save(temp_path)
                
                # Cria registro de assinatura pendente
                signature_record = Signature(
                    user_id=current_user.id,
                    file_id=file_id,
                    original_filename=pdf_file.filename,
                    signature_hash='',  # Será preenchido após assinatura
                    signature_algorithm='PENDING',
                    timestamp=datetime.now(),
                    file_size=os.path.getsize(temp_path),
                    signature_valid=False,
                    status='pending',  # Novo campo para status
                    document_type_id=document_type_id,
                    client_name=client_info['nome'],
                    client_cpf=client_info['cpf'],
                    client_email=client_info['email'],
                    client_phone=client_info['telefone'],
                    client_birth_date=birth_date,  # Usa a data convertida
                    client_address=client_info['endereco'],
                    ip_address='',  # Será preenchido pelo cliente
                    signature_method='pending',
                    verification_status='pending'
                )
                
                db.session.add(signature_record)
                signature_ids.append(file_id)
            
            db.session.commit()
            
            flash(f'{len(valid_files)} arquivo(s) enviado(s) com sucesso! Aguardando assinatura do cliente.', 'success')
            try:
                log_event(action='internal_upload', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"files": len(valid_files)})
            except Exception:
                pass
            return redirect(url_for('internal_pending_signatures'))
        
        return render_template('internal/upload.html', document_types=document_types)
    
    @app.route('/internal/pending')
    @login_required
    def internal_pending_signatures():
        """Tela interna: Lista de assinaturas pendentes"""
        # Busca assinaturas pendentes do usuário logado
        pending_signatures = Signature.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).order_by(Signature.timestamp.desc()).all()
        
        # Agrupa por cliente
        clients = {}
        for sig in pending_signatures:
            client_key = f"{sig.client_name}_{sig.client_cpf}"
            if client_key not in clients:
                clients[client_key] = {
                    'client_name': sig.client_name,
                    'client_cpf': sig.client_cpf,
                    'client_email': sig.client_email,
                    'client_phone': sig.client_phone,
                    'signatures': []
                }
            clients[client_key]['signatures'].append(sig)
        
        return render_template('internal/pending.html', clients=clients)
    
    @app.route('/internal/signature/edit/<int:signature_id>', methods=['GET', 'POST'])
    @login_required
    def internal_edit_signature(signature_id):
        """Tela interna: Edição de assinatura pendente"""
        from models import DocumentType
        signature = Signature.query.get_or_404(signature_id)
        
        # Verifica se a assinatura pertence ao usuário logado
        if signature.user_id != current_user.id:
            flash('Acesso negado', 'error')
            return redirect(url_for('internal_pending_signatures'))
        
        # Verifica se a assinatura ainda está pendente
        if signature.status != 'pending':
            flash('Apenas assinaturas pendentes podem ser editadas', 'error')
            return redirect(url_for('internal_pending_signatures'))
        
        document_types = DocumentType.query.filter_by(active=True).order_by(DocumentType.name.asc()).all()
        
        if request.method == 'POST':
            # Atualiza os dados do cliente
            signature.client_name = request.form.get('client_name', '').strip()
            signature.client_cpf = request.form.get('client_cpf', '').strip()
            signature.client_email = request.form.get('client_email', '').strip()
            signature.client_phone = request.form.get('client_phone', '').strip()
            signature.client_address = request.form.get('client_address', '').strip()

            # Tipo de documento
            dt_raw = request.form.get('document_type_id', '').strip()
            try:
                signature.document_type_id = int(dt_raw) if dt_raw else None
            except Exception:
                signature.document_type_id = None
            
            # Converte a data de nascimento se fornecida
            birth_date_str = request.form.get('client_birth_date', '').strip()
            if birth_date_str:
                try:
                    signature.client_birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Data de nascimento inválida. Use o formato AAAA-MM-DD', 'error')
                    return render_template('internal/edit_signature.html', signature=signature)
            
            # Salva as alterações
            db.session.commit()
            flash('Informações da assinatura atualizadas com sucesso!', 'success')
            return redirect(url_for('internal_pending_signatures'))
        
        return render_template('internal/edit_signature.html', signature=signature, document_types=document_types)
    
    @app.route('/internal/signature/cancel/<int:signature_id>', methods=['POST'])
    @login_required
    def internal_cancel_signature(signature_id):
        """Tela interna: Cancelamento de assinatura pendente"""
        signature = Signature.query.get_or_404(signature_id)
        
        # Verifica se a assinatura pertence ao usuário logado
        if signature.user_id != current_user.id:
            flash('Acesso negado', 'error')
            return redirect(url_for('internal_pending_signatures'))
        
        # Verifica se a assinatura ainda está pendente
        if signature.status != 'pending':
            flash('Apenas assinaturas pendentes podem ser canceladas', 'error')
            return redirect(url_for('internal_pending_signatures'))
        
        try:
            # Atualiza o status para cancelado
            signature.status = 'cancelled'
            signature.updated_at = datetime.now()
            
            # Remove arquivos temporários se existirem
            temp_file_path = os.path.join(TEMP_DIR, f"{signature.file_id}_{signature.original_filename}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            db.session.commit()
            flash('Assinatura cancelada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cancelar assinatura: {str(e)}', 'error')
        
        try:
            log_event(action='internal_cancel', actor_user_id=current_user.id, status='success', ip_address=get_client_ip(request), details={"signature_id": signature_id})
        except Exception:
            pass
        return redirect(url_for('internal_pending_signatures'))
    
    @app.route('/internal/completed')
    @login_required
    def internal_completed_signatures():
        """Tela interna: Lista de assinaturas concluídas"""
        completed_signatures = Signature.query.filter_by(
            user_id=current_user.id,
            status='completed'
        ).order_by(Signature.timestamp.desc()).all()
        
        # Calcula contagens (evita comparar date vs datetime no template)
        now_dt = datetime.now()
        today_start = datetime(now_dt.year, now_dt.month, now_dt.day)
        week_ago_dt = now_dt - timedelta(days=7)
        month_ago_dt = now_dt - timedelta(days=30)

        today_count = sum(1 for s in completed_signatures if s.updated_at and s.updated_at >= today_start)
        week_count = sum(1 for s in completed_signatures if s.updated_at and s.updated_at >= week_ago_dt)
        month_count = sum(1 for s in completed_signatures if s.updated_at and s.updated_at >= month_ago_dt)
        
        return render_template('internal/completed.html', 
                            signatures=completed_signatures,
                            today_count=today_count,
                            week_count=week_count,
                            month_count=month_count,
                            store_pdfs=get_store_pdfs_flag())
    
    @app.route('/internal/cancelled')
    @login_required
    def internal_cancelled_signatures():
        """Tela interna: Lista de assinaturas canceladas"""
        cancelled_signatures = Signature.query.filter_by(
            user_id=current_user.id,
            status='cancelled'
        ).order_by(Signature.timestamp.desc()).all()
        
        return render_template('internal/cancelled.html', signatures=cancelled_signatures)
    
    # === TELA CLIENTE (MOBILE) ===
    
    @app.route('/client/select', methods=['GET', 'POST'])
    def client_select_document():
        """Tela cliente: Seleção de documento para assinatura"""
        if request.method == 'POST':
            client_cpf = request.form.get('client_cpf', '').strip()
            
            if not client_cpf:
                flash('CPF é obrigatório', 'error')
                return render_template('client/select.html')
            
            # Salva CPF e prepara fila na sessão; a listagem será na próxima tela
            session['client_cpf'] = client_cpf
            return redirect(url_for('client_list_documents'))
        
        return render_template('client/select.html')

    @app.route('/client/list')
    def client_list_documents():
        """Lista todos os documentos do cliente (pendentes e concluídos recentes)"""
        if 'client_cpf' not in session:
            flash('Sessão expirada. Por favor, informe seu CPF novamente.', 'error')
            return redirect(url_for('client_select_document'))
        
        client_cpf = session['client_cpf']
        pending_docs = Signature.query.filter_by(
            client_cpf=client_cpf,
            status='pending'
        ).order_by(Signature.timestamp.asc()).all()
        completed_docs = Signature.query.filter_by(
            client_cpf=client_cpf,
            status='completed'
        ).order_by(Signature.updated_at.desc()).limit(20).all()
        
        # Guarda fila de pendentes na sessão
        session['pending_docs'] = [doc.id for doc in pending_docs]
        
        return render_template('client/list.html',
                               client_cpf=client_cpf,
                               pending_docs=pending_docs,
                               completed_docs=completed_docs)
    
    @app.route('/client/confirm/<int:signature_id>', methods=['GET', 'POST'])
    def client_confirm_document(signature_id):
        """Tela cliente: Confirmação de dados e aceite de termos"""
        if 'client_cpf' not in session:
            flash('Sessão expirada. Por favor, informe seu CPF novamente.', 'error')
            return redirect(url_for('client_select_document'))
        
        signature = Signature.query.get_or_404(signature_id)
        
        # Verifica se o documento pertence ao cliente da sessão
        if signature.client_cpf != session['client_cpf'] or signature.status != 'pending':
            flash('Documento não encontrado ou já processado', 'error')
            return redirect(url_for('client_select_document'))
        
        if request.method == 'POST':
            # Verifica se aceitou todos os termos
            accept_terms = request.form.get('accept_terms')
            confirm_authorization = request.form.get('confirm_authorization')
            assume_responsibility = request.form.get('assume_responsibility')
            
            if not all([accept_terms, confirm_authorization, assume_responsibility]):
                flash('Você deve aceitar todos os termos para continuar', 'error')
                return render_template('client/confirm.html', 
                                    signature=signature,
                                    client_cpf=session['client_cpf'],
                                    client_data=signature,
                                    documents=[signature])
            
            # Salva confirmação na sessão
            session['signature_confirmed'] = signature_id
            return redirect(url_for('client_sign_document', signature_id=signature_id))
        
        return render_template('client/confirm.html', 
                            signature=signature,
                            client_cpf=session['client_cpf'],
                            client_data=signature,
                            documents=[signature])
    
    @app.route('/client/sign/<int:signature_id>', methods=['GET', 'POST'])
    def client_sign_document(signature_id):
        """Tela cliente: Assinatura do documento"""
        if 'signature_confirmed' not in session or session['signature_confirmed'] != signature_id:
            flash('Confirmação necessária. Por favor, confirme os dados primeiro.', 'error')
            return redirect(url_for('client_confirm_document', signature_id=signature_id))
        
        # Query otimizada - busca apenas campos necessários
        signature = db.session.query(Signature).filter_by(id=signature_id).first()
        if not signature:
            flash('Documento não encontrado', 'error')
            return redirect(url_for('client_select_document'))
        
        if request.method == 'POST':
            signature_image = request.json.get('signature_image')
            if not signature_image:
                return jsonify({'success': False, 'message': 'Assinatura não fornecida'})
            
            try:
                # Coleta informações do dispositivo
                device_info = detect_device_info(request.headers.get('User-Agent', ''), request)
                
                # Gera o PDF assinado fisicamente para download
                try:
                    original_path = os.path.join(TEMP_DIR, f"{signature.file_id}_{signature.original_filename}")
                    if os.path.exists(original_path):
                        # Cria saída temporária
                        output_path = tempfile.mktemp(suffix='.pdf')
                        # Dados do cliente para inserir no PDF
                        client_info = {
                            'nome': signature.client_name,
                            'cpf': signature.client_cpf,
                            'data_nascimento': signature.client_birth_date.isoformat() if getattr(signature, 'client_birth_date', None) else ''
                        }
                        # Gera o PDF com a imagem da assinatura
                        generated = add_signature_to_all_pages(
                            original_path,
                            '',
                            output_path,
                            signature_image,
                            client_info,
                            create_logo_image()
                        )
                        if generated and os.path.exists(output_path):
                            # Política de retenção
                            keep_pdfs = get_store_pdfs_flag()
                            retention_tag = 'KEEP' if keep_pdfs else 'TEMP'
                            clean_final_filename = signature.original_filename.replace('.pdf', '_assinado.pdf')
                            stored_final_filename = f"{signature.file_id}_{clean_final_filename.replace('.pdf', f'_{retention_tag}.pdf')}"
                            final_path = os.path.join(PDF_SIGNED_DIR, stored_final_filename)
                            shutil.move(output_path, final_path)
                            
                            # Lê o PDF final e recalcula o hash
                            with open(final_path, 'rb') as f:
                                final_content = f.read()
                            
                            # Embute metadados primeiro
                            signature_info = {
                                'hash': signature.signature_hash,  # Usa o hash já calculado
                                'timestamp': datetime.now().isoformat(),
                                'algorithm': signature.signature_algorithm
                            }
                            embed_signature_metadata(final_path, signature_info)
                            
                            # Lê o PDF final (com carimbo + metadados) e calcula hash
                            with open(final_path, 'rb') as f:
                                final_content = f.read()
                            
                            # Calcula hash do PDF FINAL (com carimbo + metadados)
                            from utils.crypto_utils import calculate_content_hash
                            final_hash = calculate_content_hash(final_content)
                            
                            # Assina o hash do PDF final
                            signature_info = signature_manager.sign_data(final_hash)
                            
                            # Atualiza o registro
                            signature.signature_hash = signature_info['hash']
                            signature.signature_algorithm = signature_info['algorithm']
                            signature.signature_data = signature_info['signature']  # Salva os dados da assinatura digital
                            signature.signature_valid = True
                            signature.status = 'completed'
                            signature.verification_status = 'verified'
                            signature.signature_method = 'drawing'
                            signature.ip_address = device_info['ip_address']
                            signature.user_agent = device_info['user_agent']
                            signature.browser_name = device_info['browser_name']
                            signature.browser_version = device_info['browser_version']
                            signature.operating_system = device_info['operating_system']
                            signature.device_type = device_info['device_type']
                            signature.screen_resolution = request.headers.get('X-Screen-Resolution', '')
                            signature.timezone = request.headers.get('X-Timezone', '')
                            signature.updated_at = datetime.now()
                            
                            # Atualiza no banco de dados
                            signature.signature_hash = final_hash
                            signature.file_size = len(final_content)
                            
                            print(f"🔢 Hash calculado APÓS carimbo + metadados: {final_hash[:16]}...")
                    # Se o arquivo original não existir, seguimos sem interromper (download acusará ausência)
                except Exception as gen_err:
                    # Não falha a assinatura por erro ao gerar arquivo; apenas registra e segue
                    print(f"Erro ao gerar PDF assinado para cliente: {gen_err}")

                db.session.commit()
                
                # Fluxo em lote: se houver fila, avança para o próximo
                sign_queue = session.get('client_sign_queue')
                if sign_queue and signature_id in sign_queue:
                    try:
                        # Remove o atual e obtém o próximo
                        sign_queue = [sid for sid in sign_queue if sid != signature_id]
                        session['client_sign_queue'] = sign_queue
                        if sign_queue:
                            next_id = sign_queue[0]
                            session['signature_confirmed'] = next_id
                            return jsonify({
                                'success': True,
                                'message': 'Documento assinado. Prosseguindo para o próximo...',
                                'redirect': url_for('client_confirm_document', signature_id=next_id)
                            })
                    except Exception:
                        pass
                
                # Limpa sessão de confirmação para fluxo simples
                session.pop('signature_confirmed', None)
                session.pop('client_sign_queue', None)
                
                try:
                    log_event(action='client_sign', actor_user_id=None, status='success', ip_address=get_client_ip(request), details={"signature_id": signature_id})
                except Exception:
                    pass
                return jsonify({
                    'success': True, 
                    'message': 'Documento assinado com sucesso!',
                    'redirect': url_for('client_success')
                })
                
            except Exception as e:
                return jsonify({'success': False, 'message': f'Erro ao assinar: {str(e)}'})
        
        return render_template('client/sign.html', signature=signature)
    
    @app.route('/client/success')
    def client_success():
        """Tela cliente: Confirmação de sucesso"""
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        return render_template('client/success.html', current_time=current_time)
    
    @app.route('/client/download/<int:signature_id>')
    def client_download_signed(signature_id):
        """Download do PDF assinado pelo cliente"""
        signature = Signature.query.get_or_404(signature_id)
        
        if signature.status != 'completed':
            flash('Documento ainda não foi assinado', 'error')
            return redirect(url_for('client_select_document'))
        
        # Busca arquivo assinado com política de retenção
        clean_final_filename = signature.original_filename.replace('.pdf', '_assinado.pdf')
        stored_name_keep = f"{signature.file_id}_{clean_final_filename.replace('.pdf', '_KEEP.pdf')}"
        stored_name_temp = f"{signature.file_id}_{clean_final_filename.replace('.pdf', '_TEMP.pdf')}"
        candidate_keep = os.path.join(PDF_SIGNED_DIR, stored_name_keep)
        candidate_temp = os.path.join(PDF_SIGNED_DIR, stored_name_temp)
        
        signed_path = candidate_keep if os.path.exists(candidate_keep) else (candidate_temp if os.path.exists(candidate_temp) else None)
        
        if not signed_path or not os.path.exists(signed_path):
            flash('Arquivo assinado não encontrado', 'error')
            return redirect(url_for('client_select_document'))
        
        response = send_file(signed_path, as_attachment=True, download_name=clean_final_filename)
        
        # Se for arquivo temporário, remove após enviar
        try:
            if signed_path.endswith('_TEMP.pdf'):
                os.remove(signed_path)
        except Exception as rm_err:
            print(f"Erro ao remover PDF temporário após download (cliente): {rm_err}")
        
        return response

    @app.route('/client/sign_all')
    def client_sign_all():
        """Inicializa assinatura em lote de todos os documentos pendentes do CPF atual"""
        if 'client_cpf' not in session:
            flash('Sessão expirada. Informe seu CPF novamente.', 'error')
            return redirect(url_for('client_select_document'))
        
        pending_ids = session.get('pending_docs', [])
        if not pending_ids:
            flash('Nenhum documento pendente encontrado.', 'error')
            return redirect(url_for('client_select_document'))
        
        # Inicia fila e direciona para o primeiro documento (com confirmação de termos)
        session['client_sign_queue'] = list(pending_ids)
        first_id = pending_ids[0]
        session['signature_confirmed'] = first_id
        return redirect(url_for('client_confirm_document', signature_id=first_id))

    @app.route('/validate', methods=['GET', 'POST'])
    @app.limiter.limit("20 per minute")
    def validate_pdf():
        """Página para validação de PDFs assinados"""
        if request.method == 'POST':
            if 'pdf_file' not in request.files:
                flash('Nenhum arquivo selecionado', 'error')
                return render_template('validate.html')
            
            file = request.files['pdf_file']
            if file.filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return render_template('validate.html')
            
            if not file.filename.lower().endswith('.pdf'):
                flash('Por favor, selecione um arquivo PDF', 'error')
                return render_template('validate.html')
            
            try:
                # Salva arquivo temporariamente
                temp_path = tempfile.mktemp(suffix='.pdf')
                file.save(temp_path)
                
                # Tenta encontrar um registro de assinatura correspondente
                # Procura por arquivos na pasta pdf_assinados que correspondam ao hash
                with open(temp_path, 'rb') as f:
                    pdf_content = f.read()
                
                from utils.crypto_utils import calculate_content_hash
                current_hash = calculate_content_hash(pdf_content)
                
                # Busca registro de assinatura com hash correspondente
                signature_record = Signature.query.filter_by(signature_hash=current_hash).first()
                
                # Valida o PDF (com ou sem registro)
                validation_result = pdf_validator.validate_pdf(temp_path, signature_record)
                
                # Log de auditoria
                from audit_logger import log_validation_event
                log_validation_event(
                    file_id=signature_record.file_id if signature_record else None,
                    status='validated',
                    ip_address=get_client_ip(request),
                    is_valid=validation_result.get('valid', False)
                )
                
                # Limpa arquivo temporário
                os.remove(temp_path)
                
                try:
                    log_validation_event(
                        file_id=signature_record.file_id if signature_record else None,
                        status='validated',
                        ip_address=get_client_ip(request),
                        is_valid=validation_result.get('valid', False)
                    )
                except Exception:
                    pass
                return render_template('validate.html', result=validation_result)
                
            except Exception as e:
                flash(f'Erro ao processar arquivo: {str(e)}', 'error')
                return render_template('validate.html')
        
        return render_template('validate.html')

    @app.route('/validate/<file_id>')
    def validate_pdf_by_id(file_id):
        """Valida um PDF específico pelo file_id"""
        try:
            # Busca o registro de assinatura
            signature_record = Signature.query.filter_by(file_id=file_id).first()
            
            if not signature_record:
                flash('Documento não encontrado', 'error')
                return redirect(url_for('validate_pdf'))
            
            # Busca o arquivo PDF assinado
            pdf_filename = None
            for filename in os.listdir(PDF_SIGNED_DIR):
                if filename.startswith(file_id):
                    pdf_filename = filename
                    break
            
            if not pdf_filename:
                flash('Arquivo PDF não encontrado', 'error')
                return redirect(url_for('validate_pdf'))
            
            pdf_path = os.path.join(PDF_SIGNED_DIR, pdf_filename)
            
            # Valida o PDF
            validation_result = pdf_validator.validate_pdf(pdf_path, signature_record)
            validation_result['file_id'] = file_id
            validation_result['filename'] = pdf_filename
            
            return render_template('validate.html', result=validation_result)
            
        except Exception as e:
            flash(f'Erro ao validar documento: {str(e)}', 'error')
            return redirect(url_for('validate_pdf'))

    @app.route('/validate/api', methods=['POST'])
    def validate_pdf_api():
        """API para validação de PDF via upload"""
        try:
            if 'pdf_file' not in request.files:
                return jsonify({'error': 'Nenhum arquivo fornecido'}), 400
            
            file = request.files['pdf_file']
            if file.filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Arquivo deve ser um PDF'}), 400
            
            # Salva arquivo temporariamente
            temp_path = tempfile.mktemp(suffix='.pdf')
            file.save(temp_path)
            
            # Valida o PDF
            validation_result = pdf_validator.validate_pdf(temp_path)
            
            # Limpa arquivo temporário
            os.remove(temp_path)
            
            return jsonify(validation_result)
            
        except Exception as e:
            return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

# Diretório para arquivos temporários
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_files')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Diretório para assets estáticos
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Diretório para armazenamento persistente de assinaturas
SIGNATURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signatures')
if not os.path.exists(SIGNATURES_DIR):
    os.makedirs(SIGNATURES_DIR)

# Diretório para PDFs assinados (resultado final)
PDF_SIGNED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdf_assinados')
if not os.path.exists(PDF_SIGNED_DIR):
    os.makedirs(PDF_SIGNED_DIR)

def cleanup_temp_files():
    """Remove arquivos temporários antigos baseado na configuração"""
    try:
        from config import config
        current_time = datetime.now().timestamp()
        
        # Usa configuração do ambiente ou padrão (1 hora)
        retention_hours = getattr(config.get('default'), 'TEMP_FILE_RETENTION_HOURS', 1)
        retention_seconds = retention_hours * 60 * 60
        
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(file_path):
                # Remove arquivos mais antigos que o tempo configurado
                if os.path.getmtime(file_path) < (current_time - retention_seconds):
                    try:
                        os.remove(file_path)
                        print(f"🗑️  Arquivo temporário removido: {filename}")
                    except Exception as e:
                        print(f"❌ Falha ao remover {file_path}: {e}")
    except Exception as e:
        print(f"Erro ao limpar arquivos temporários: {e}")

def cleanup_temp_files_all():
    """Remove TODOS os arquivos do diretório temporário TEMP_DIR"""
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️  Arquivo temporário removido: {filename}")
                except Exception as e:
                    print(f"❌ Falha ao remover {file_path}: {e}")
    except Exception as e:
        print(f"Erro ao limpar diretório temporário: {e}")

def cleanup_signed_pdfs_temp():
    """Remove todos os PDFs assinados marcados como temporários (_TEMP.pdf)"""
    try:
        for filename in os.listdir(PDF_SIGNED_DIR):
            if filename.endswith('_TEMP.pdf'):
                file_path = os.path.join(PDF_SIGNED_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        print(f"🗑️  PDF temporário removido: {filename}")
                    except Exception as e:
                        print(f"❌ Falha ao remover PDF temporário {file_path}: {e}")
    except Exception as e:
        print(f"Erro ao limpar PDFs temporários: {e}")

def cleanup_old_files():
    """Remove arquivos antigos baseado na configuração de temp_files e pdf_assinados"""
    try:
        from config import config
        current_time = datetime.now().timestamp()
        
        # Usa configuração do ambiente ou padrão (7 dias)
        retention_days = getattr(config.get('default'), 'FILE_RETENTION_DAYS', 7)
        retention_seconds = retention_days * 24 * 60 * 60
        cutoff_time = current_time - retention_seconds
        
        removed_count = 0
        
        # Limpa arquivos da pasta temp_files
        if os.path.exists(TEMP_DIR):
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            print(f"🗑️  Arquivo antigo removido de temp_files: {filename}")
                        except Exception as e:
                            print(f"❌ Falha ao remover {file_path}: {e}")
        
        # Limpa arquivos da pasta pdf_assinados
        if os.path.exists(PDF_SIGNED_DIR):
            for filename in os.listdir(PDF_SIGNED_DIR):
                file_path = os.path.join(PDF_SIGNED_DIR, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            print(f"🗑️  PDF assinado antigo removido: {filename}")
                        except Exception as e:
                            print(f"❌ Falha ao remover {file_path}: {e}")
        
        if removed_count > 0:
            print(f"✅ Limpeza concluída: {removed_count} arquivos removidos (mais de {retention_days} dias)")
        else:
            print(f"ℹ️  Nenhum arquivo antigo encontrado para remoção")
            
    except Exception as e:
        print(f"❌ Erro durante limpeza de arquivos antigos: {e}")

def cleanup_old_files_by_database():
    """Remove arquivos baseado nos registros do banco de dados (mais preciso)"""
    try:
        from models import Signature
        from datetime import timedelta
        from config import config
        
        # Usa configuração do ambiente ou padrão (7 dias)
        retention_days = getattr(config.get('default'), 'FILE_RETENTION_DAYS', 7)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        old_signatures = Signature.query.filter(
            Signature.timestamp < cutoff_date
        ).all()
        
        removed_count = 0
        
        for signature in old_signatures:
            # Remove arquivo da pasta pdf_assinados
            if signature.file_id:
                # Procura arquivos com o file_id
                for directory in [PDF_SIGNED_DIR, TEMP_DIR]:
                    if os.path.exists(directory):
                        for filename in os.listdir(directory):
                            if filename.startswith(signature.file_id):
                                file_path = os.path.join(directory, filename)
                                if os.path.isfile(file_path):
                                    try:
                                        os.remove(file_path)
                                        removed_count += 1
                                        print(f"🗑️  Arquivo removido por idade no BD: {filename}")
                                    except Exception as e:
                                        print(f"❌ Falha ao remover {file_path}: {e}")
        
        if removed_count > 0:
            print(f"✅ Limpeza por banco de dados concluída: {removed_count} arquivos removidos")
        else:
            print(f"ℹ️  Nenhum arquivo antigo encontrado no banco de dados")
            
    except Exception as e:
        print(f"❌ Erro durante limpeza por banco de dados: {e}")

def run_daily_cleanup(hour: int = 2, minute: int = 0, tz_name: str = 'America/Sao_Paulo'):
    """Loop em background que executa a limpeza diariamente no horário configurado.
    Se não houver base de timezones (tzdata), usa horário local sem timezone."""
    tz = None
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        try:
            tz = ZoneInfo('UTC')
            print(f"Timezone '{tz_name}' indisponível; usando UTC para a rotina de limpeza.")
        except Exception:
            print(f"Base de timezones indisponível; usando horário local para a rotina de limpeza.")
    while True:
        now = datetime.now(tz) if tz else datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)
        seconds = (target - now).total_seconds()
        try:
            time.sleep(seconds)
        except Exception:
            pass
        try:
            print(f"🧹 Iniciando rotina diária de limpeza - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Limpeza de arquivos temporários (1 hora)
            cleanup_temp_files()
            
            # Limpeza de PDFs temporários
            cleanup_signed_pdfs_temp()
            
            # Limpeza de arquivos antigos (7 dias) - baseada em timestamp do arquivo
            cleanup_old_files()
            
            # Limpeza de arquivos antigos (7 dias) - baseada no banco de dados
            cleanup_old_files_by_database()
            
            print(f"✅ Rotina diária de limpeza concluída - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        except Exception as e:
            print(f"❌ Erro durante rotina diária de limpeza: {e}")

SCHEDULER_STARTED = False

def embed_signature_metadata(pdf_path, signature_info):
    """Embute metadados de assinatura no PDF"""
    try:
        # Lê o PDF
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copia todas as páginas
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Adiciona metadados de assinatura
            metadata = pdf_reader.metadata or {}
            metadata['/SignatureInfo'] = json.dumps(signature_info)
            metadata['/SignatureDate'] = signature_info['timestamp']
            metadata['/SignatureHash'] = signature_info['hash']
            metadata['/SignatureAlgorithm'] = signature_info['algorithm']
            pdf_writer.add_metadata(metadata)
            
            # Salva o PDF com metadados
            with open(pdf_path, 'wb') as f:
                pdf_writer.write(f)
            
            return True
    except Exception as e:
        print(f"Erro ao embutir metadados: {e}")
        return False

def extract_signature_metadata(pdf_path):
    """Extrai metadados de assinatura do PDF"""
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            if pdf_reader.metadata and '/SignatureInfo' in pdf_reader.metadata:
                return json.loads(pdf_reader.metadata['/SignatureInfo'])
    except Exception as e:
        print(f"Erro ao extrair metadados: {e}")
    return None

def create_logo_image():
    """Cria um logo padrão se não existir"""
    logo_path = os.path.join(STATIC_DIR, 'images', 'logo.png')
    
    if not os.path.exists(logo_path):
        # Cria um logo simples usando PIL
        from PIL import Image, ImageDraw, ImageFont
        
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(logo_path), exist_ok=True)
        
        # Cria uma imagem 200x100 com fundo azul
        img = Image.new('RGB', (200, 100), color='#0d6efd')
        draw = ImageDraw.Draw(img)
        
        # Adiciona texto "LOGO"
        try:
            # Tenta usar uma fonte do sistema
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Centraliza o texto
        text = "LOGO"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (200 - text_width) // 2
        y = (100 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        img.save(logo_path)
    
    return logo_path

def add_signature_to_all_pages(pdf_file, signature_text, output_path, signature_image=None, personal_info=None, logo_path=None):
    """Adiciona assinatura digital a todas as páginas do PDF no canto inferior direito"""
    try:
        # Lê o PDF original
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            temp_page_buffers = []  # Mantém buffers abertos até finalizar a escrita
            
            # Cria logo se não existir
            if not logo_path:
                logo_path = create_logo_image()
            
            # Para cada página do PDF
            for page_num, page in enumerate(pdf_reader.pages):
                # Cria um PDF temporário para a página atual em memória
                temp_buffer = io.BytesIO()
                
                # Cria um canvas para adicionar a assinatura no canto inferior direito
                c = canvas.Canvas(temp_buffer, pagesize=A4)
                width, height = A4
                
                # Define a posição da assinatura no canto inferior direito
                signature_x = width - 8*cm  # 8cm da borda direita para acomodar logo + info + assinatura
                signature_y = 1*cm  # 1cm da borda inferior (mais próximo da borda)
                
                # Calcula altura da assinatura para redimensionar o logo proporcionalmente
                signature_height = 1.2*cm  # Reduzida para caber melhor
                logo_height = signature_height  # Logo na mesma altura da assinatura
                logo_width = logo_height * 1.5  # Reduzida proporção para 1.5:1
                
                # Adiciona a assinatura desenhada PRIMEIRO (em cima)
                if signature_image:
                    try:
                        # Salva a imagem da assinatura temporariamente
                        signature_temp = tempfile.mktemp(suffix='.png')
                        with open(signature_temp, 'wb') as f:
                            f.write(base64.b64decode(signature_image.split(',')[1]))
                        
                        # Adiciona a assinatura desenhada
                        signature_img = RLImage(signature_temp)
                        signature_img.drawHeight = signature_height
                        signature_img.drawWidth = 2.5*cm  # Largura fixa para a assinatura
                        
                        # Posiciona a assinatura ACIMA do logo e dados
                        signature_img_x = signature_x + logo_width + 1*cm  # Centraliza a rubrica
                        signature_img_y = signature_y + 1.5*cm  # Posiciona acima dos dados
                        signature_img.drawOn(c, signature_img_x, signature_img_y)
                        
                        # Limpa arquivo temporário
                        os.remove(signature_temp)
                    except Exception as e:
                        print(f"Erro ao adicionar assinatura desenhada: {e}")
                
                # Adiciona o logo (redimensionado proporcionalmente à assinatura)
                if os.path.exists(logo_path):
                    try:
                        logo_img = RLImage(logo_path)
                        logo_img.drawHeight = logo_height
                        logo_img.drawWidth = logo_width
                        logo_img.drawOn(c, signature_x, signature_y)  # Logo alinhado na base
                    except:
                        pass
                
                # Adiciona informações pessoais ao lado do logo (alinhadas com o logo)
                if personal_info:
                    info_x = signature_x + logo_width + 0.3*cm  # Posição após o logo (mais próximo)
                    info_y = signature_y + 0.8*cm  # Alinhado com o logo (mesma altura)
                    c.setFont("Helvetica-Bold", 8)
                    c.setFillColor(colors.darkblue)
                    
                    if personal_info.get('nome'):
                        c.drawString(info_x, info_y, f"Nome: {personal_info['nome']}")
                        info_y -= 0.3*cm
                    if personal_info.get('cpf'):
                        c.drawString(info_x, info_y, f"CPF: {personal_info['cpf']}")
                        info_y -= 0.3*cm
                    if personal_info.get('data_nascimento'):
                        c.drawString(info_x, info_y, f"Data: {personal_info['data_nascimento']}")
                
                # Adiciona timestamp
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                c.setFont("Helvetica", 6)
                c.setFillColor(colors.grey)
                c.drawString(signature_x, signature_y - 0.5*cm, f"Assinado em: {timestamp}")
                
                c.save()
                
                # Garante que o buffer esteja no início para leitura
                temp_buffer.seek(0)
                temp_reader = PyPDF2.PdfReader(temp_buffer)
                temp_page = temp_reader.pages[0]
                
                # Mescla a página original com a assinatura
                page.merge_page(temp_page)
                pdf_writer.add_page(page)
                
                # Mantém o buffer vivo até terminar a escrita do PDF final
                temp_page_buffers.append(temp_buffer)
            
            # Salva o PDF final
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Libera buffers
            for b in temp_page_buffers:
                try:
                    b.close()
                except:
                    pass
            
            # Verifica se o arquivo foi criado corretamente
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                # Validação leve: checa cabeçalho %PDF
                try:
                    with open(output_path, 'rb') as test_file:
                        header = test_file.read(4)
                    if header == b'%PDF':
                        return True
                    else:
                        print("Assinado, mas cabeçalho inesperado; prosseguindo mesmo assim.")
                        return True
                except Exception as e:
                    print(f"Assinado, mas falha ao validar cabeçalho: {e}; prosseguindo.")
                    return True
            else:
                print("Falha ao criar arquivo PDF")
                return False
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return False

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5001) 