#!/usr/bin/env python3
"""
Script para atualizar o banco de dados com as novas colunas de auditoria
"""

import os
import sys
import sqlite3
from datetime import datetime

def update_database():
    """Atualiza o banco de dados com as novas colunas"""
    
    db_path = "instance/assinador.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        print("Execute primeiro: python init_db.py")
        return False
    
    print("🔄 Conectando ao banco de dados...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se a tabela signatures existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='signatures'")
        if not cursor.fetchone():
            print("❌ Tabela 'signatures' não encontrada")
            print("Execute primeiro: python init_db.py")
            return False
        
        print("✅ Tabela 'signatures' encontrada")
        
        # Verifica colunas existentes
        cursor.execute("PRAGMA table_info(signatures)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colunas existentes: {', '.join(existing_columns)}")
        
        # Lista de novas colunas a serem adicionadas
        new_columns = [
            # Informações do Cliente/Assinante
            ("client_name", "TEXT"),
            ("client_cpf", "VARCHAR(14)"),
            ("client_email", "TEXT"),
            ("client_phone", "VARCHAR(20)"),
            ("client_birth_date", "DATE"),
            ("client_address", "TEXT"),
            
            # Informações do Dispositivo e Conexão
            ("ip_address", "VARCHAR(45)"),
            ("mac_address", "VARCHAR(17)"),
            ("user_agent", "TEXT"),
            ("browser_name", "VARCHAR(50)"),
            ("browser_version", "VARCHAR(20)"),
            ("operating_system", "VARCHAR(100)"),
            ("device_type", "VARCHAR(20)"),
            ("screen_resolution", "VARCHAR(20)"),
            ("timezone", "VARCHAR(50)"),
            
            # Informações de Localização
            ("location_country", "VARCHAR(100)"),
            ("location_city", "VARCHAR(100)"),
            ("location_latitude", "REAL"),
            ("location_longitude", "REAL"),
            
            # Informações da Assinatura
            ("signature_method", "VARCHAR(20)"),
            ("signature_duration", "INTEGER"),
            ("verification_status", "VARCHAR(20)"),
            ("verification_notes", "TEXT"),
            
            # Auditoria
            ("created_at", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP"),
            # Armazenamento opcional do PDF assinado (BLOB)
            ("signed_pdf", "BLOB")
        ]
        
        print(f"\n🔄 Adicionando {len(new_columns)} novas colunas...")
        
        # Adiciona cada coluna se não existir
        added_columns = []
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE signatures ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"  ✅ Coluna {column_name} adicionada")
                except Exception as e:
                    print(f"  ⚠️ Erro ao adicionar {column_name}: {str(e)}")
            else:
                print(f"  ℹ️ Coluna {column_name} já existe")
        
        # Define valores padrão para colunas existentes
        print("\n🔄 Definindo valores padrão...")
        
        # Atualiza colunas com valores padrão
        update_queries = [
            ("signature_method", "UPDATE signatures SET signature_method = 'drawing' WHERE signature_method IS NULL"),
            ("verification_status", "UPDATE signatures SET verification_status = 'verified' WHERE verification_status IS NULL"),
            ("created_at", "UPDATE signatures SET created_at = timestamp WHERE created_at IS NULL"),
            ("updated_at", "UPDATE signatures SET updated_at = timestamp WHERE updated_at IS NULL")
        ]
        
        for column_name, query in update_queries:
            if column_name in existing_columns:
                try:
                    cursor.execute(query)
                    print(f"  ✅ Valores padrão definidos para {column_name}")
                except Exception as e:
                    print(f"  ⚠️ Erro ao definir valores padrão para {column_name}: {str(e)}")
        
        # Cria tabela de configurações da aplicação, se não existir
        print("\n🔧 Garantindo tabela 'app_settings'...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL
            )
            """
        )

        # Define configuração padrão store_pdfs=false se não existir
        cursor.execute("SELECT value FROM app_settings WHERE key = 'store_pdfs'")
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO app_settings (key, value) VALUES (?, ?)", ("store_pdfs", "false"))
            print("  ✅ Configuração padrão 'store_pdfs=false' criada")
        else:
            print("  ℹ️ Configuração 'store_pdfs' já existe")

        # Commit das alterações
        conn.commit()
        
        print(f"\n🎯 Atualização concluída!")
        print(f"✅ {len(added_columns)} novas colunas adicionadas:")
        for col in added_columns:
            print(f"  - {col}")
        
        # Verifica estrutura final
        cursor.execute("PRAGMA table_info(signatures)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n📊 Total de colunas na tabela: {len(final_columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a atualização: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def show_database_info():
    """Mostra informações sobre o banco de dados"""
    
    db_path = "instance/assinador.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return
    
    print("📊 Informações do Banco de Dados:")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Informações da tabela signatures
        cursor.execute("PRAGMA table_info(signatures)")
        columns = cursor.fetchall()
        
        print(f"📋 Tabela 'signatures':")
        print(f"   Total de colunas: {len(columns)}")
        print("\n   Colunas:")
        for col in columns:
            col_id, name, type_name, not_null, default_val, primary_key = col
            pk = " (PK)" if primary_key else ""
            nn = " NOT NULL" if not_null else ""
            default = f" DEFAULT {default_val}" if default_val else ""
            print(f"     {name}: {type_name}{nn}{default}{pk}")
        
        # Contagem de registros
        cursor.execute("SELECT COUNT(*) FROM signatures")
        count = cursor.fetchone()[0]
        print(f"\n   Total de registros: {count}")
        
        # Verifica se as novas colunas estão presentes
        new_columns = [
            "client_name", "client_cpf", "client_email", "client_phone",
            "client_birth_date", "client_address", "ip_address", "mac_address",
            "user_agent", "browser_name", "browser_version", "operating_system",
            "device_type", "screen_resolution", "timezone", "location_country",
            "location_city", "location_latitude", "location_longitude",
            "signature_method", "signature_duration", "verification_status",
            "verification_notes", "created_at", "updated_at"
        ]
        
        existing_columns = [col[1] for col in columns]
        missing_columns = [col for col in new_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"\n⚠️  Colunas pendentes: {len(missing_columns)}")
            for col in missing_columns:
                print(f"     - {col}")
        else:
            print(f"\n✅ Todas as colunas de auditoria estão presentes!")
        
    except Exception as e:
        print(f"❌ Erro ao obter informações: {str(e)}")
        
    finally:
        conn.close()

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python update_database.py [comando]")
        print("\nComandos disponíveis:")
        print("  update    - Atualiza o banco com novas colunas")
        print("  info      - Mostra informações do banco")
        print("  help      - Mostra esta ajuda")
        return
    
    command = sys.argv[1].lower()
    
    if command == "update":
        print("🚀 Iniciando atualização do banco de dados...")
        success = update_database()
        if success:
            print("\n🎉 Banco de dados atualizado com sucesso!")
            print("O sistema agora suporta todas as funcionalidades de auditoria.")
        else:
            print("\n❌ Falha na atualização do banco de dados.")
            sys.exit(1)
            
    elif command == "info":
        show_database_info()
        
    elif command == "help":
        print("Script de Atualização do Banco de Dados")
        print("=" * 50)
        print("\nEste script adiciona as novas colunas necessárias para:")
        print("- Auditoria completa de assinaturas")
        print("- Informações do cliente/assinante")
        print("- Detalhes do dispositivo e conexão")
        print("- Relatórios administrativos avançados")
        print("\nComandos:")
        print("  update    - Executa a atualização do banco")
        print("  info      - Mostra status atual do banco")
        print("  help      - Mostra esta ajuda")
        
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("Use 'python update_database.py help' para ver comandos disponíveis")

if __name__ == "__main__":
    main()
