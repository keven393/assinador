from functools import wraps
from flask import request, redirect, url_for, flash, session
from flask_login import current_user, login_required
from models import db, User, UserSession
from datetime import datetime, timedelta
import uuid

def admin_required(f):
    """Decorator para rotas que requerem privilégios de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Acesso negado. Privilégios de administrador necessários.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def create_user_session(user, request):
    """Cria uma nova sessão para o usuário"""
    # Remove sessões antigas do usuário
    UserSession.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
    
    # Cria nova sessão
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)  # Sessão expira em 24 horas
    
    user_session = UserSession(
        user_id=user.id,
        session_id=session_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        expires_at=expires_at
    )
    
    db.session.add(user_session)
    db.session.commit()
    
    return session_id

def validate_session(session_id):
    """Valida se uma sessão ainda é válida"""
    user_session = UserSession.query.filter_by(
        session_id=session_id,
        is_active=True
    ).first()
    
    if not user_session:
        return None
    
    # Verifica se a sessão expirou
    if datetime.utcnow() > user_session.expires_at:
        user_session.is_active = False
        db.session.commit()
        return None
    
    return user_session.user

def cleanup_expired_sessions():
    """Remove sessões expiradas"""
    expired_sessions = UserSession.query.filter(
        UserSession.expires_at < datetime.utcnow(),
        UserSession.is_active == True
    ).all()
    
    for session in expired_sessions:
        session.is_active = False
    
    db.session.commit()

def get_user_stats():
    """Retorna estatísticas dos usuários para relatórios"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(role='admin').count()
    regular_users = User.query.filter_by(role='user').count()
    
    # Usuários ativos nas últimas 24 horas
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_logins = User.query.filter(User.last_login >= last_24h).count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'regular_users': regular_users,
        'recent_logins': recent_logins
    }

def get_signature_stats():
    """Retorna estatísticas das assinaturas para relatórios"""
    from models import Signature
    
    total_signatures = Signature.query.count()
    today = datetime.utcnow().date()
    today_signatures = Signature.query.filter(
        db.func.date(Signature.timestamp) == today
    ).count()
    
    # Assinaturas por usuário
    signatures_by_user = db.session.query(
        Signature.user_id,
        User.username,
        db.func.count(Signature.id).label('count')
    ).join(User).group_by(Signature.user_id, User.username).all()
    
    return {
        'total_signatures': total_signatures,
        'today_signatures': today_signatures,
        'signatures_by_user': signatures_by_user
    }
