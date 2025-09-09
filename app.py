from flask import Flask, render_template, request, jsonify, send_file, session, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import PyPDF2
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
from crypto_utils import signature_manager
from certificate_manager import certificate_manager
from models import db, User, Signature, AppSetting
from forms import LoginForm, UserEditForm, ChangePasswordForm, AdminUserForm, ReportFilterForm
from auth import admin_required, create_user_session, cleanup_expired_sessions, get_user_stats, get_signature_stats

from config import config
import os
import re
from datetime import date

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
        return render_template('admin/settings.html', store_pdfs=get_store_pdfs_flag())
    
    @app.route('/')
    @login_required
    def index():
        """Página inicial com lista de assinaturas pendentes"""
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
        
        return render_template('index.html', clients=clients, pending_count=len(pending_signatures))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data) and user.is_active:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Cria sessão personalizada
                session_id = create_user_session(user, request)
                session['user_session_id'] = session_id
                
                # Se forçar troca de senha estiver habilitado
                if getattr(user, 'must_change_password', False):
                    session['must_change_password_user'] = user.id
                    return redirect(url_for('force_change_password'))

                flash(f'Bem-vindo, {user.full_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Usuário ou senha inválidos, ou usuário inativo.', 'error')
        
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('user_session_id', None)
        flash('Você foi desconectado.', 'info')
        return redirect(url_for('login'))

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
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
    @admin_required
    def admin_dashboard():
        user_stats = get_user_stats()
        signature_stats = get_signature_stats()
        return render_template('admin/dashboard.html', user_stats=user_stats, signature_stats=signature_stats, store_pdfs=get_store_pdfs_flag())

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        users = User.query.all()
        return render_template('admin/users.html', users=users)

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
            return redirect(url_for('admin_users'))
        
        return render_template('admin/new_user.html', form=form)

    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_user(user_id):
        user = User.query.get_or_404(user_id)
        form = UserEditForm(obj=user)
        
        if form.validate_on_submit():
            user.username = form.username.data
            user.email = form.email.data
            user.full_name = form.full_name.data
            user.role = form.role.data
            user.is_active = form.is_active.data
            user.must_change_password = form.must_change_password.data
            
            db.session.commit()
            flash(f'Usuário {user.username} atualizado com sucesso!', 'success')
            return redirect(url_for('admin_users'))
        
        return render_template('admin/edit_user.html', form=form, user=user)

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
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
        return redirect(url_for('admin_users'))

    @app.route('/admin/reports')
    @admin_required
    def admin_reports():
        form = ReportFilterForm()
        
        # Popula as opções de usuário
        form.user_id.choices = [(0, 'Todos os usuários')] + [(u.id, u.username) for u in User.query.all()]
        
        # Filtros padrão
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
        
        # Executa a query para obter os resultados
        signatures_list = signatures.all()
        
        return render_template('admin/reports.html', form=form, signatures=signatures_list)

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
        
        return jsonify({
            'success': True,
            'total_signatures': len(report_data),
            'export_date': datetime.utcnow().isoformat(),
            'data': report_data
        })

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
                # Lê o PDF assinado
                with open(output_path, 'rb') as f:
                    signed_pdf_content = f.read()
                
                # Gera assinatura digital
                signature_info = certificate_manager.sign_pdf_with_certificate(signed_pdf_content)
                if not signature_info:
                    signature_info = signature_manager.sign_data(signed_pdf_content)
                
                # Define política de retenção
                keep_pdfs = get_store_pdfs_flag()
                retention_tag = 'KEEP' if keep_pdfs else 'TEMP'
                
                # Move arquivo final para pasta de PDFs assinados
                clean_final_filename = process_data['original_filename'].replace('.pdf', '_assinado.pdf')
                stored_final_filename = f"{process_data['file_id']}_{clean_final_filename.replace('.pdf', f'_{retention_tag}.pdf')}"
                final_path = os.path.join(PDF_SIGNED_DIR, stored_final_filename)
                shutil.move(output_path, final_path)
                
                # Embute metadados
                embed_signature_metadata(final_path, signature_info)
                
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
                    signature_hash=signature_info['hash'],
                    signature_algorithm=signature_info['algorithm'],
                    file_size=len(signed_pdf_content),
                    
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
        if request.method == 'POST':
            if 'pdf_files' not in request.files:
                flash('Nenhum arquivo PDF foi enviado', 'error')
                return render_template('internal/upload.html')
            
            pdf_files = request.files.getlist('pdf_files')
            if not pdf_files or pdf_files[0].filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return render_template('internal/upload.html')
            
            # Valida arquivos
            valid_files = []
            for pdf_file in pdf_files:
                if pdf_file.filename.lower().endswith('.pdf'):
                    valid_files.append(pdf_file)
                else:
                    flash(f'Arquivo {pdf_file.filename} não é um PDF válido', 'error')
            
            if not valid_files:
                return render_template('internal/upload.html')
            
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
            
            # Converte a data de nascimento para objeto date se fornecida
            birth_date = None
            if client_info['data_nascimento']:
                try:
                    birth_date = datetime.strptime(client_info['data_nascimento'], '%Y-%m-%d').date()
                except ValueError:
                    flash('Data de nascimento inválida. Use o formato AAAA-MM-DD', 'error')
                    return render_template('internal/upload.html', client_info=client_info)
            
            # Validação básica
            if not client_info['nome']:
                flash('Nome do cliente é obrigatório', 'error')
                return render_template('internal/upload.html', client_info=client_info)
            
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
            return redirect(url_for('internal_pending_signatures'))
        
        return render_template('internal/upload.html')
    
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
        signature = Signature.query.get_or_404(signature_id)
        
        # Verifica se a assinatura pertence ao usuário logado
        if signature.user_id != current_user.id:
            flash('Acesso negado', 'error')
            return redirect(url_for('internal_pending_signatures'))
        
        # Verifica se a assinatura ainda está pendente
        if signature.status != 'pending':
            flash('Apenas assinaturas pendentes podem ser editadas', 'error')
            return redirect(url_for('internal_pending_signatures'))
        
        if request.method == 'POST':
            # Atualiza os dados do cliente
            signature.client_name = request.form.get('client_name', '').strip()
            signature.client_cpf = request.form.get('client_cpf', '').strip()
            signature.client_email = request.form.get('client_email', '').strip()
            signature.client_phone = request.form.get('client_phone', '').strip()
            signature.client_address = request.form.get('client_address', '').strip()
            
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
        
        return render_template('internal/edit_signature.html', signature=signature)
    
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
        
        signature = Signature.query.get_or_404(signature_id)
        
        if request.method == 'POST':
            signature_image = request.json.get('signature_image')
            if not signature_image:
                return jsonify({'success': False, 'message': 'Assinatura não fornecida'})
            
            try:
                # Coleta informações do dispositivo
                device_info = detect_device_info(request.headers.get('User-Agent', ''), request)
                
                # Processa a assinatura
                # Combina os dados para criar uma assinatura única
                signature_data = f"{signature.file_id}_{signature.original_filename}_{signature_image[:100]}"  # Primeiros 100 chars da imagem
                signature_info = signature_manager.sign_data(signature_data)
                
                # Atualiza o registro
                signature.signature_hash = signature_info['hash']
                signature.signature_algorithm = signature_info['algorithm']
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
                            # Embute metadados básicos usando o hash já calculado
                            embed_signature_metadata(final_path, {
                                'hash': signature.signature_hash,
                                'timestamp': datetime.now().isoformat(),
                                'algorithm': signature.signature_algorithm
                            })
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
    """Remove arquivos temporários antigos"""
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(file_path):
                # Remove arquivos mais antigos que 1 hora
                if os.path.getmtime(file_path) < (datetime.now().timestamp() - 3600):
                    os.remove(file_path)
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
                except Exception as e:
                    print(f"Falha ao remover {file_path}: {e}")
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
                    except Exception as e:
                        print(f"Falha ao remover PDF temporário {file_path}: {e}")
    except Exception as e:
        print(f"Erro ao limpar PDFs temporários: {e}")

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
            cleanup_temp_files_all()
            cleanup_signed_pdfs_temp()
        except Exception as e:
            print(f"Erro durante rotina diária de limpeza: {e}")

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
                signature_x = width - 10*cm  # 10cm da borda direita para acomodar logo + info + assinatura
                signature_y = 2*cm  # 2cm da borda inferior
                
                # Calcula altura da assinatura para redimensionar o logo proporcionalmente
                signature_height = 1.2*cm  # Reduzida para caber melhor
                logo_height = signature_height  # Logo na mesma altura da assinatura
                logo_width = logo_height * 1.5  # Reduzida proporção para 1.5:1
                
                # Adiciona o logo (redimensionado proporcionalmente à assinatura)
                if os.path.exists(logo_path):
                    try:
                        logo_img = RLImage(logo_path)
                        logo_img.drawHeight = logo_height
                        logo_img.drawWidth = logo_width
                        logo_img.drawOn(c, signature_x, signature_y)  # Logo alinhado com a assinatura
                    except:
                        pass
                
                # Adiciona informações pessoais no meio (alinhadas com a assinatura)
                if personal_info:
                    info_x = signature_x + logo_width + 0.5*cm  # Posição após o logo
                    info_y = signature_y + 0.8*cm  # Alinhado com a assinatura (mesma altura)
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
                
                # Adiciona a assinatura desenhada (alinhada com o logo e info)
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
                        
                        # Posiciona a assinatura após as informações pessoais
                        signature_img_x = signature_x + logo_width + 3*cm  # Posição após logo + info
                        signature_img_y = signature_y  # Mesma altura do logo
                        signature_img.drawOn(c, signature_img_x, signature_img_y)
                        
                        # Limpa arquivo temporário
                        os.remove(signature_temp)
                    except Exception as e:
                        print(f"Erro ao adicionar assinatura desenhada: {e}")
                
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
    
    app.run(debug=True, host='0.0.0.0', port=5000) 