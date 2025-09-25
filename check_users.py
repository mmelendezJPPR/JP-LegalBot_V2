#!/usr/bin/env python3
import sqlite3
import hashlib

def check_users():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('database/Usuarios.db')
        cursor = conn.cursor()
        
        # Primero verificar qué tablas existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📊 Tablas en la base de datos:")
        for table in tables:
            print(f"   - {table[0]}")
        print()
        
        # Intentar diferentes nombres de tabla
        table_names = ['users', 'usuarios', 'Usuarios', 'Users']
        users = []
        table_found = None
        
        for table_name in table_names:
            try:
                cursor.execute(f'SELECT email, password_hash, created_at, is_active FROM {table_name}')
                users = cursor.fetchall()
                table_found = table_name
                break
            except sqlite3.OperationalError:
                continue
        
        if table_found:
            print(f"👥 Usuarios en la tabla '{table_found}':")
            print("=" * 50)
            
            if not users:
                print("❌ No hay usuarios en la base de datos")
                return
            
            for i, (email, password_hash, created_at, is_active) in enumerate(users, 1):
                print(f"{i}. Email: {email}")
                print(f"   Hash: {password_hash[:20]}...")
                print(f"   Creado: {created_at}")
                print(f"   Activo: {'Sí' if is_active else 'No'}")
                print()
        else:
            print("❌ No se encontró ninguna tabla de usuarios válida")
        
        # Probar el hash de admin123
        test_password = "admin123"
        test_hash = hashlib.sha256(test_password.encode()).hexdigest()
        print(f"🔐 Hash de 'admin123': {test_hash}")
        
        # Verificar si algún usuario tiene ese hash
        if users:
            for email, stored_hash, _, _ in users:
                if stored_hash == test_hash:
                    print(f"✅ El usuario {email} tiene la contraseña 'admin123'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_users()