#!/usr/bin/env python3
import sqlite3
import hashlib

def update_password():
    # Hash de admin123
    password = "admin123"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('database/Usuarios.db')
        cursor = conn.cursor()
        
        # Actualizar contraseña para melendez_ma@jp.pr.gov
        cursor.execute("""
            UPDATE usuarios 
            SET password_hash = ? 
            WHERE email = ?
        """, (password_hash, 'melendez_ma@jp.pr.gov'))
        
        if cursor.rowcount > 0:
            print("✅ Contraseña actualizada correctamente para melendez_ma@jp.pr.gov")
        else:
            print("❌ No se encontró el usuario melendez_ma@jp.pr.gov")
        
        conn.commit()
        conn.close()
        
        # Verificar la actualización
        conn = sqlite3.connect('database/Usuarios.db')
        cursor = conn.cursor()
        cursor.execute('SELECT email, password_hash FROM usuarios WHERE email = ?', ('melendez_ma@jp.pr.gov',))
        user = cursor.fetchone()
        
        if user and user[1] == password_hash:
            print(f"✅ Verificación exitosa: {user[0]} ahora tiene la contraseña 'admin123'")
        else:
            print("❌ Error en la verificación")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_password()