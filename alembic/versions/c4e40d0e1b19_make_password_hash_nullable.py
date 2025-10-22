"""make_password_hash_nullable

Revision ID: c4e40d0e1b19
Revises: 792010f37dfa
Create Date: 2025-10-20 15:35:45.770524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e40d0e1b19'
down_revision: Union[str, Sequence[str], None] = '792010f37dfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tornar password_hash nullable para suportar usuários LDAP
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Reverter password_hash para NOT NULL
    # ATENÇÃO: Isso pode falhar se houver usuários LDAP sem senha
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=False)
