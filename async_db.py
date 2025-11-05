"""
Módulo de configuração para SQLAlchemy Async
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import Config

# Base para models async
Base = declarative_base()

# Verifica se está usando SQLite
DATABASE_URL = Config.ASYNC_SQLALCHEMY_DATABASE_URI or Config.SQLALCHEMY_DATABASE_URI
IS_SQLITE = DATABASE_URL.startswith('sqlite') if DATABASE_URL else True

# Async engine (apenas para PostgreSQL/MySQL)
if IS_SQLITE:
    # SQLite não suporta async, usar engine None
    async_engine = None
    AsyncSessionLocal = None
else:
    # Converte URL do PostgreSQL para usar asyncpg se necessário
    async_url = str(DATABASE_URL)
    
    # Remove qualquer driver existente primeiro
    if '+asyncpg' in async_url:
        # Já está usando asyncpg, não precisa converter
        pass
    elif '://' in async_url:
        # Converte diferentes formatos de URL PostgreSQL
        if async_url.startswith('postgresql://'):
            async_url = async_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif async_url.startswith('postgres://'):
            async_url = async_url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif async_url.startswith('postgresql+psycopg2://'):
            async_url = async_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://', 1)
        elif async_url.startswith('postgresql+psycopg2cffi://'):
            async_url = async_url.replace('postgresql+psycopg2cffi://', 'postgresql+asyncpg://', 1)
        else:
            # Se não reconhecer o formato, assume PostgreSQL e adiciona asyncpg
            parts = async_url.split('://', 1)
            if len(parts) == 2:
                scheme, rest = parts
                if scheme in ['postgresql', 'postgres']:
                    async_url = f'postgresql+asyncpg://{rest}'
    
    async_engine = create_async_engine(
        async_url,
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    # Async session maker
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

async def get_async_session():
    """
    Generator para obter sessão async
    Uso:
        async for session in get_async_session():
            # usar session
            break
    """
    if IS_SQLITE:
        raise NotImplementedError("SQLite não suporta operações assíncronas. Use PostgreSQL em produção.")
    
    async with AsyncSessionLocal() as session:
        yield session

