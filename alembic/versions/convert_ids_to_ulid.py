"""convert_ids_to_ulid

Revision ID: convert_ids_to_ulid
Revises: c4e40d0e1b19
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from ulid import ULID

# revision identifiers, used by Alembic.
revision = 'convert_ids_to_ulid'
down_revision = '9dac6f843a11'  # Aponta para add_multi_signer_support (última migration antes desta)
branch_labels = None
depends_on = None


def upgrade():
    """
    Converte todas as colunas de ID de Integer para String(26) para usar ULID.
    IMPORTANTE: Esta migration requer migração de dados existentes.
    """
    
    # 1. Adiciona novas colunas temporárias para ULID
    # Users
    op.add_column('users', sa.Column('id_new', sa.String(26), nullable=True))
    op.add_column('signatures', sa.Column('id_new', sa.String(26), nullable=True))
    op.add_column('signatures', sa.Column('user_id_new', sa.String(26), nullable=True))
    op.add_column('signatures', sa.Column('document_type_id_new', sa.String(26), nullable=True))
    op.add_column('signature_signers', sa.Column('id_new', sa.String(26), nullable=True))
    op.add_column('signature_signers', sa.Column('signature_id_new', sa.String(26), nullable=True))
    op.add_column('document_types', sa.Column('id_new', sa.String(26), nullable=True))
    op.add_column('app_settings', sa.Column('id_new', sa.String(26), nullable=True))
    op.add_column('user_sessions', sa.Column('id_new', sa.String(26), nullable=True))
    op.add_column('user_sessions', sa.Column('user_id_new', sa.String(26), nullable=True))
    
    # 2. Gera ULIDs para registros existentes e popula as novas colunas
    # Conecta ao banco para fazer a migração de dados
    connection = op.get_bind()
    
    # Mapeamento de IDs antigos para novos ULIDs
    user_id_map = {}
    signature_id_map = {}
    document_type_id_map = {}
    signature_signer_id_map = {}
    app_setting_id_map = {}
    user_session_id_map = {}
    
    # Migra Users (deve ser primeiro pois outras tabelas dependem dele)
    users_result = connection.execute(sa.text("SELECT id FROM users ORDER BY id"))
    for row in users_result.fetchall():
        old_id = row[0]
        new_ulid = str(ULID())
        user_id_map[old_id] = new_ulid
        connection.execute(
            sa.text("UPDATE users SET id_new = :new_id WHERE id = :old_id"),
            {"new_id": new_ulid, "old_id": old_id}
        )
    
    # Migra DocumentTypes (antes de signatures)
    doc_types_result = connection.execute(sa.text("SELECT id FROM document_types ORDER BY id"))
    for row in doc_types_result.fetchall():
        old_id = row[0]
        new_ulid = str(ULID())
        document_type_id_map[old_id] = new_ulid
        connection.execute(
            sa.text("UPDATE document_types SET id_new = :new_id WHERE id = :old_id"),
            {"new_id": new_ulid, "old_id": old_id}
        )
    
    # Migra Signatures
    signatures_result = connection.execute(sa.text("SELECT id, user_id, document_type_id FROM signatures ORDER BY id"))
    for row in signatures_result.fetchall():
        old_id, old_user_id, old_doc_type_id = row[0], row[1], row[2]
        new_ulid = str(ULID())
        signature_id_map[old_id] = new_ulid
        
        # Mapeia user_id e document_type_id
        new_user_id = user_id_map.get(old_user_id)
        new_doc_type_id = document_type_id_map.get(old_doc_type_id) if old_doc_type_id else None
        
        connection.execute(
            sa.text("""
                UPDATE signatures 
                SET id_new = :new_id, 
                    user_id_new = :new_user_id,
                    document_type_id_new = :new_doc_type_id
                WHERE id = :old_id
            """),
            {
                "new_id": new_ulid,
                "new_user_id": new_user_id,
                "new_doc_type_id": new_doc_type_id,
                "old_id": old_id
            }
        )
    
    # Migra SignatureSigners
    signers_result = connection.execute(sa.text("SELECT id, signature_id FROM signature_signers ORDER BY id"))
    for row in signers_result.fetchall():
        old_id, old_signature_id = row[0], row[1]
        new_ulid = str(ULID())
        signature_signer_id_map[old_id] = new_ulid
        
        new_signature_id = signature_id_map.get(old_signature_id)
        
        connection.execute(
            sa.text("""
                UPDATE signature_signers 
                SET id_new = :new_id,
                    signature_id_new = :new_signature_id
                WHERE id = :old_id
            """),
            {
                "new_id": new_ulid,
                "new_signature_id": new_signature_id,
                "old_id": old_id
            }
        )
    
    # Migra AppSettings
    settings_result = connection.execute(sa.text("SELECT id FROM app_settings ORDER BY id"))
    for row in settings_result.fetchall():
        old_id = row[0]
        new_ulid = str(ULID())
        app_setting_id_map[old_id] = new_ulid
        connection.execute(
            sa.text("UPDATE app_settings SET id_new = :new_id WHERE id = :old_id"),
            {"new_id": new_ulid, "old_id": old_id}
        )
    
    # Migra UserSessions
    sessions_result = connection.execute(sa.text("SELECT id, user_id FROM user_sessions ORDER BY id"))
    for row in sessions_result.fetchall():
        old_id, old_user_id = row[0], row[1]
        new_ulid = str(ULID())
        user_session_id_map[old_id] = new_ulid
        
        new_user_id = user_id_map.get(old_user_id)
        
        connection.execute(
            sa.text("""
                UPDATE user_sessions 
                SET id_new = :new_id,
                    user_id_new = :new_user_id
                WHERE id = :old_id
            """),
            {
                "new_id": new_ulid,
                "new_user_id": new_user_id,
                "old_id": old_id
            }
        )
    
    # Nota: Alembic gerencia transações automaticamente, não precisa commit manual
    
    # 3. Atualiza foreign keys temporariamente (remove constraints)
    # Remove constraints apenas se existirem
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Remove foreign keys (se existirem)
    try:
        op.drop_constraint('signatures_user_id_fkey', 'signatures', type_='foreignkey')
    except Exception:
        pass  # Ignora se não existir
    
    try:
        op.drop_constraint('signatures_document_type_id_fkey', 'signatures', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_constraint('signature_signers_signature_id_fkey', 'signature_signers', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_constraint('user_sessions_user_id_fkey', 'user_sessions', type_='foreignkey')
    except Exception:
        pass
    
    # 4. Remove índices antigos (apenas se existirem)
    # Verifica índices existentes antes de tentar remover
    if 'signatures' in inspector.get_table_names():
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('signatures')}
        if 'idx_signatures_user_id' in existing_indexes:
            op.drop_index('idx_signatures_user_id', table_name='signatures')
    
    if 'signature_signers' in inspector.get_table_names():
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('signature_signers')}
        if 'idx_signature_signers_signature_id' in existing_indexes:
            op.drop_index('idx_signature_signers_signature_id', table_name='signature_signers')
    
    if 'user_sessions' in inspector.get_table_names():
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('user_sessions')}
        if 'idx_sessions_user_id' in existing_indexes:
            op.drop_index('idx_sessions_user_id', table_name='user_sessions')
    
    # 5. Remove colunas antigas
    op.drop_column('user_sessions', 'user_id')
    op.drop_column('user_sessions', 'id')
    op.drop_column('app_settings', 'id')
    op.drop_column('document_types', 'id')
    op.drop_column('signature_signers', 'signature_id')
    op.drop_column('signature_signers', 'id')
    op.drop_column('signatures', 'document_type_id')
    op.drop_column('signatures', 'user_id')
    op.drop_column('signatures', 'id')
    op.drop_column('users', 'id')
    
    # 6. Renomeia colunas novas
    op.alter_column('users', 'id_new', new_column_name='id')
    op.alter_column('signatures', 'id_new', new_column_name='id')
    op.alter_column('signatures', 'user_id_new', new_column_name='user_id')
    op.alter_column('signatures', 'document_type_id_new', new_column_name='document_type_id')
    op.alter_column('signature_signers', 'id_new', new_column_name='id')
    op.alter_column('signature_signers', 'signature_id_new', new_column_name='signature_id')
    op.alter_column('document_types', 'id_new', new_column_name='id')
    op.alter_column('app_settings', 'id_new', new_column_name='id')
    op.alter_column('user_sessions', 'id_new', new_column_name='id')
    op.alter_column('user_sessions', 'user_id_new', new_column_name='user_id')
    
    # 7. Define como NOT NULL e PRIMARY KEY
    op.alter_column('users', 'id', nullable=False)
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    op.alter_column('signatures', 'id', nullable=False)
    op.create_primary_key('signatures_pkey', 'signatures', ['id'])
    op.alter_column('signatures', 'user_id', nullable=False)
    op.alter_column('signatures', 'document_type_id', nullable=True)
    
    op.alter_column('signature_signers', 'id', nullable=False)
    op.create_primary_key('signature_signers_pkey', 'signature_signers', ['id'])
    op.alter_column('signature_signers', 'signature_id', nullable=False)
    
    op.alter_column('document_types', 'id', nullable=False)
    op.create_primary_key('document_types_pkey', 'document_types', ['id'])
    
    op.alter_column('app_settings', 'id', nullable=False)
    op.create_primary_key('app_settings_pkey', 'app_settings', ['id'])
    
    op.alter_column('user_sessions', 'id', nullable=False)
    op.create_primary_key('user_sessions_pkey', 'user_sessions', ['id'])
    op.alter_column('user_sessions', 'user_id', nullable=False)
    
    # 8. Recria foreign keys
    op.create_foreign_key('signatures_user_id_fkey', 'signatures', 'users', ['user_id'], ['id'])
    op.create_foreign_key('signatures_document_type_id_fkey', 'signatures', 'document_types', ['document_type_id'], ['id'])
    op.create_foreign_key('signature_signers_signature_id_fkey', 'signature_signers', 'signatures', ['signature_id'], ['id'])
    op.create_foreign_key('user_sessions_user_id_fkey', 'user_sessions', 'users', ['user_id'], ['id'])
    
    # 9. Recria índices
    op.create_index('idx_signatures_user_id', 'signatures', ['user_id'])
    op.create_index('idx_signature_signers_signature_id', 'signature_signers', ['signature_id'])
    op.create_index('idx_sessions_user_id', 'user_sessions', ['user_id'])


def downgrade():
    """
    Reverte a migration - converte ULIDs de volta para Integer.
    ATENÇÃO: Esta operação pode perder dados se houver ULIDs que não podem ser convertidos.
    """
    # Esta operação é complexa e pode não ser totalmente reversível
    # Em produção, considere fazer backup antes de fazer downgrade
    
    # Remove foreign keys
    op.drop_constraint('signatures_user_id_fkey', 'signatures', type_='foreignkey')
    op.drop_constraint('signatures_document_type_id_fkey', 'signatures', type_='foreignkey')
    op.drop_constraint('signature_signers_signature_id_fkey', 'signature_signers', type_='foreignkey')
    op.drop_constraint('user_sessions_user_id_fkey', 'user_sessions', type_='foreignkey')
    
    # Remove índices
    op.drop_index('idx_signatures_user_id', table_name='signatures')
    op.drop_index('idx_signature_signers_signature_id', table_name='signature_signers')
    op.drop_index('idx_sessions_user_id', table_name='user_sessions')
    
    # Adiciona colunas Integer temporárias
    op.add_column('users', sa.Column('id_old', sa.Integer(), nullable=True, autoincrement=True))
    op.add_column('signatures', sa.Column('id_old', sa.Integer(), nullable=True, autoincrement=True))
    op.add_column('signatures', sa.Column('user_id_old', sa.Integer(), nullable=True))
    op.add_column('signatures', sa.Column('document_type_id_old', sa.Integer(), nullable=True))
    op.add_column('signature_signers', sa.Column('id_old', sa.Integer(), nullable=True, autoincrement=True))
    op.add_column('signature_signers', sa.Column('signature_id_old', sa.Integer(), nullable=True))
    op.add_column('document_types', sa.Column('id_old', sa.Integer(), nullable=True, autoincrement=True))
    op.add_column('app_settings', sa.Column('id_old', sa.Integer(), nullable=True, autoincrement=True))
    op.add_column('user_sessions', sa.Column('id_old', sa.Integer(), nullable=True, autoincrement=True))
    op.add_column('user_sessions', sa.Column('user_id_old', sa.Integer(), nullable=True))
    
    # Gera IDs sequenciais (perde mapeamento original)
    # Em produção, você precisaria de uma tabela de mapeamento
    
    # Remove colunas ULID
    op.drop_column('user_sessions', 'user_id')
    op.drop_column('user_sessions', 'id')
    op.drop_column('app_settings', 'id')
    op.drop_column('document_types', 'id')
    op.drop_column('signature_signers', 'signature_id')
    op.drop_column('signature_signers', 'id')
    op.drop_column('signatures', 'document_type_id')
    op.drop_column('signatures', 'user_id')
    op.drop_column('signatures', 'id')
    op.drop_column('users', 'id')
    
    # Renomeia colunas antigas
    op.alter_column('users', 'id_old', new_column_name='id')
    op.alter_column('signatures', 'id_old', new_column_name='id')
    op.alter_column('signatures', 'user_id_old', new_column_name='user_id')
    op.alter_column('signatures', 'document_type_id_old', new_column_name='document_type_id')
    op.alter_column('signature_signers', 'id_old', new_column_name='id')
    op.alter_column('signature_signers', 'signature_id_old', new_column_name='signature_id')
    op.alter_column('document_types', 'id_old', new_column_name='id')
    op.alter_column('app_settings', 'id_old', new_column_name='id')
    op.alter_column('user_sessions', 'id_old', new_column_name='id')
    op.alter_column('user_sessions', 'user_id_old', new_column_name='user_id')
    
    # Define como Integer com autoincrement
    op.alter_column('users', 'id', type_=sa.Integer(), nullable=False, autoincrement=True)
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    op.alter_column('signatures', 'id', type_=sa.Integer(), nullable=False, autoincrement=True)
    op.create_primary_key('signatures_pkey', 'signatures', ['id'])
    op.alter_column('signatures', 'user_id', type_=sa.Integer(), nullable=False)
    op.alter_column('signatures', 'document_type_id', type_=sa.Integer(), nullable=True)
    
    op.alter_column('signature_signers', 'id', type_=sa.Integer(), nullable=False, autoincrement=True)
    op.create_primary_key('signature_signers_pkey', 'signature_signers', ['id'])
    op.alter_column('signature_signers', 'signature_id', type_=sa.Integer(), nullable=False)
    
    op.alter_column('document_types', 'id', type_=sa.Integer(), nullable=False, autoincrement=True)
    op.create_primary_key('document_types_pkey', 'document_types', ['id'])
    
    op.alter_column('app_settings', 'id', type_=sa.Integer(), nullable=False, autoincrement=True)
    op.create_primary_key('app_settings_pkey', 'app_settings', ['id'])
    
    op.alter_column('user_sessions', 'id', type_=sa.Integer(), nullable=False, autoincrement=True)
    op.create_primary_key('user_sessions_pkey', 'user_sessions', ['id'])
    op.alter_column('user_sessions', 'user_id', type_=sa.Integer(), nullable=False)
    
    # Recria foreign keys
    op.create_foreign_key('signatures_user_id_fkey', 'signatures', 'users', ['user_id'], ['id'])
    op.create_foreign_key('signatures_document_type_id_fkey', 'signatures', 'document_types', ['document_type_id'], ['id'])
    op.create_foreign_key('signature_signers_signature_id_fkey', 'signature_signers', 'signatures', ['signature_id'], ['id'])
    op.create_foreign_key('user_sessions_user_id_fkey', 'user_sessions', 'users', ['user_id'], ['id'])
    
    # Recria índices
    op.create_index('idx_signatures_user_id', 'signatures', ['user_id'])
    op.create_index('idx_signature_signers_signature_id', 'signature_signers', ['signature_id'])
    op.create_index('idx_sessions_user_id', 'user_sessions', ['user_id'])

