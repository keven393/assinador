"""add_ldap_fields_to_user

Revision ID: 792010f37dfa
Revises: 3428989358d4
Create Date: 2025-10-20 15:15:19.262773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '792010f37dfa'
down_revision: Union[str, Sequence[str], None] = '3428989358d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adicionar campos do Active Directory à tabela users
    op.add_column('users', sa.Column('ldap_dn', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('department', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('position', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('mobile', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('street_address', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('home_phone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('work_address', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('fax', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('pager', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('is_ldap_user', sa.Boolean(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remover campos do Active Directory da tabela users
    op.drop_column('users', 'is_ldap_user')
    op.drop_column('users', 'pager')
    op.drop_column('users', 'fax')
    op.drop_column('users', 'work_address')
    op.drop_column('users', 'home_phone')
    op.drop_column('users', 'street_address')
    op.drop_column('users', 'country')
    op.drop_column('users', 'postal_code')
    op.drop_column('users', 'state')
    op.drop_column('users', 'city')
    op.drop_column('users', 'mobile')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'position')
    op.drop_column('users', 'department')
    op.drop_column('users', 'ldap_dn')
