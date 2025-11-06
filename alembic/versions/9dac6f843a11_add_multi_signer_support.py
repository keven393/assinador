"""add_multi_signer_support

Revision ID: 9dac6f843a11
Revises: c4e40d0e1b19
Create Date: 2025-11-05 16:16:55.845713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9dac6f843a11'
down_revision: Union[str, Sequence[str], None] = 'c4e40d0e1b19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Verificar e adicionar campos novos na tabela signatures (idempotente)
    conn = op.get_bind()
    
    # Verificar se colunas já existem
    cursor = conn.execute(sa.text("PRAGMA table_info(signatures)"))
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    if 'is_multi_signer' not in existing_columns:
        op.add_column('signatures', sa.Column('is_multi_signer', sa.Boolean(), nullable=False, server_default='0'))
    if 'total_signers' not in existing_columns:
        op.add_column('signatures', sa.Column('total_signers', sa.Integer(), nullable=False, server_default='1'))
    if 'signed_signers_count' not in existing_columns:
        op.add_column('signatures', sa.Column('signed_signers_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Verificar se tabela signature_signers já existe
    cursor = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='signature_signers'"))
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Criar tabela signature_signers
        op.create_table('signature_signers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('signature_id', sa.Integer(), nullable=False),
            sa.Column('signer_name', sa.String(length=255), nullable=False),
            sa.Column('signer_cpf', sa.String(length=14), nullable=False),
            sa.Column('signer_email', sa.String(length=255), nullable=True),
            sa.Column('signer_phone', sa.String(length=20), nullable=True),
            sa.Column('signer_birth_date', sa.Date(), nullable=True),
            sa.Column('signer_address', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('signed_at', sa.DateTime(), nullable=True),
            sa.Column('signature_image', sa.Text(), nullable=True),
            sa.Column('signature_hash', sa.String(length=64), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('browser_name', sa.String(length=50), nullable=True),
            sa.Column('browser_version', sa.String(length=20), nullable=True),
            sa.Column('operating_system', sa.String(length=100), nullable=True),
            sa.Column('device_type', sa.String(length=20), nullable=True),
            sa.Column('screen_resolution', sa.String(length=20), nullable=True),
            sa.Column('timezone', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['signature_id'], ['signatures.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Verificar e criar índices (idempotente)
    cursor = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_signature_signers_signature_id'"))
    if cursor.fetchone() is None:
        op.create_index('idx_signature_signers_signature_id', 'signature_signers', ['signature_id'], unique=False)
    
    cursor = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_signature_signers_signer_cpf'"))
    if cursor.fetchone() is None:
        op.create_index('idx_signature_signers_signer_cpf', 'signature_signers', ['signer_cpf'], unique=False)
    
    cursor = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_signature_signers_status'"))
    if cursor.fetchone() is None:
        op.create_index('idx_signature_signers_status', 'signature_signers', ['status'], unique=False)
    
    # Migrar dados existentes: documentos existentes terão is_multi_signer=False
    # e signed_signers_count baseado no status atual
    if 'is_multi_signer' in existing_columns:
        # Apenas atualizar se colunas já existiam
        try:
            op.execute(sa.text("""
                UPDATE signatures 
                SET signed_signers_count = CASE 
                    WHEN status = 'completed' THEN 1 
                    ELSE 0 
                END
                WHERE is_multi_signer = 0 AND signed_signers_count IS NULL
            """))
        except Exception:
            pass  # Ignora se já foi atualizado


def downgrade() -> None:
    """Downgrade schema."""
    # Remover índices
    op.drop_index('idx_signature_signers_status', table_name='signature_signers')
    op.drop_index('idx_signature_signers_signer_cpf', table_name='signature_signers')
    op.drop_index('idx_signature_signers_signature_id', table_name='signature_signers')
    
    # Remover tabela
    op.drop_table('signature_signers')
    
    # Remover colunas
    op.drop_column('signatures', 'signed_signers_count')
    op.drop_column('signatures', 'total_signers')
    op.drop_column('signatures', 'is_multi_signer')