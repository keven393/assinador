"""
Módulo de queries assíncronas para o banco de dados
"""
from datetime import datetime
from sqlalchemy import select, func
from async_db import AsyncSessionLocal, IS_SQLITE
from models import Signature, User, UserSession

async def get_signature_stats_async():
    """
    Versão async de auth.get_signature_stats - APENAS para PostgreSQL/MySQL
    
    Returns:
        dict: Estatísticas de assinaturas
    """
    if IS_SQLITE:
        raise NotImplementedError("SQLite não suporta operações assíncronas. Use PostgreSQL em produção.")
    async with AsyncSessionLocal() as session:
        # Total
        total_result = await session.execute(select(func.count(Signature.id)))
        total_signatures = total_result.scalar()
        
        # Hoje
        today = datetime.utcnow().date()
        today_result = await session.execute(
            select(func.count(Signature.id))
            .where(func.date(Signature.timestamp) == today)
        )
        today_signatures = today_result.scalar()
        
        # Por usuário
        signatures_by_user_result = await session.execute(
            select(Signature.user_id, User.username, func.count(Signature.id).label('count'))
            .join(User)
            .group_by(Signature.user_id, User.username)
        )
        signatures_by_user = signatures_by_user_result.all()
        
        return {
            'total_signatures': total_signatures,
            'today_signatures': today_signatures,
            'signatures_by_user': signatures_by_user
        }

async def get_user_stats_async():
    """
    Versão async de auth.get_user_stats - APENAS para PostgreSQL/MySQL
    
    Returns:
        dict: Estatísticas de usuários
    """
    if IS_SQLITE:
        raise NotImplementedError("SQLite não suporta operações assíncronas. Use PostgreSQL em produção.")
    async with AsyncSessionLocal() as session:
        # Total de usuários
        total_result = await session.execute(select(func.count(User.id)))
        total_users = total_result.scalar()
        
        # Usuários ativos
        active_result = await session.execute(
            select(func.count(User.id))
            .where(User.is_active == True)
        )
        active_users = active_result.scalar()
        
        # Administradores
        admin_result = await session.execute(
            select(func.count(User.id))
            .where(User.role == 'admin')
        )
        admin_count = admin_result.scalar()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_count': admin_count
        }

async def get_recent_signatures_async(limit=10):
    """
    Busca assinaturas recentes
    
    Args:
        limit: Número máximo de assinaturas a retornar
        
    Returns:
        list: Lista de assinaturas recentes
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Signature)
            .order_by(Signature.timestamp.desc())
            .limit(limit)
        )
        signatures = result.scalars().all()
        return signatures

async def get_signature_by_file_id_async(file_id):
    """
    Busca assinatura por file_id
    
    Args:
        file_id: ID do arquivo
        
    Returns:
        Signature ou None
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Signature)
            .where(Signature.file_id == file_id)
        )
        return result.scalar_one_or_none()

async def get_user_signatures_async(user_id, limit=None):
    """
    Busca assinaturas de um usuário
    
    Args:
        user_id: ID do usuário
        limit: Número máximo de assinaturas a retornar
        
    Returns:
        list: Lista de assinaturas do usuário
    """
    async with AsyncSessionLocal() as session:
        query = select(Signature).where(Signature.user_id == user_id).order_by(Signature.timestamp.desc())
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()

async def get_expired_sessions_async():
    """
    Busca sessões expiradas
    
    Returns:
        list: Lista de sessões expiradas
    """
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(UserSession)
            .where(UserSession.expires_at < now)
            .where(UserSession.is_active == True)
        )
        return result.scalars().all()

async def get_signature_count_by_status_async():
    """
    Conta assinaturas por status
    
    Returns:
        dict: Contagem de assinaturas por status
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Signature.status, func.count(Signature.id))
            .group_by(Signature.status)
        )
        return dict(result.all())

async def get_signature_count_by_date_range_async(start_date, end_date):
    """
    Conta assinaturas em um intervalo de datas
    
    Args:
        start_date: Data inicial
        end_date: Data final
        
    Returns:
        int: Número de assinaturas no período
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count(Signature.id))
            .where(Signature.timestamp >= start_date)
            .where(Signature.timestamp <= end_date)
        )
        return result.scalar()

