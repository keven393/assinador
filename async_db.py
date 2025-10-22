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
IS_SQLITE = DATABASE_URL.startswith('sqlite')

# Async engine (apenas para PostgreSQL/MySQL)
if IS_SQLITE:
    # SQLite não suporta async, usar engine None
    async_engine = None
    AsyncSessionLocal = None
else:
    async_engine = create_async_engine(
        DATABASE_URL,
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

