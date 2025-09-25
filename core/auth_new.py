"""
=======================================================================
AUTH.PY - SISTEMA DE AUTENTICACIÓN SQLite PARA JP_LEGALBOT v3.2
=======================================================================
Sistema de autenticación basado en SQLite que se inicializa automáticamente
en Render y crea usuarios por defecto.
=======================================================================
"""

import sqlite3
import hashlib
import os
from typing import Optional, Dict
from datetime import datetime

class SimpleAuth:
    """Sistema de autenticación SQLite con inicialización automática"""
    
    def __init__(self):
        # Configuración de la base de datos SQLite
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'Usuarios.db')
        
        # Crear directorio database si no existe
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # Inicializar base de datos automáticamente si no existe
        if not os.path.exists(self.db_path):
            print(f"🔧 Creando base de datos de usuarios: {self.db_path}")
            self._init_database()
        
        print("✅ Sistema de autenticación SQLite inicializado")
        print(f"📁 Base de datos: {self.db_path}")
        
        # Verificar conexión y crear usuarios por defecto si es necesario
        self._test_connection()
        self._ensure_default_users()
    
    def _test_connection(self):
        """Verifica la conexión a la base de datos SQLite"""
        try:
            conn = self._get_connection()
            if not conn:
                print("⚠️ No se puede conectar a la base de datos SQLite")
                return
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            count = cursor.fetchone()[0]
            print(f"📊 Usuarios en base de datos: {count}")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error verificando base de datos: {e}")
    
    def _init_database(self):
        """Crea la base de datos y las tablas necesarias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear tabla de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.commit()
            conn.close()
            print("✅ Base de datos de usuarios creada exitosamente")
            
        except Exception as e:
            print(f"❌ Error creando base de datos: {e}")
            raise
    
    def _ensure_default_users(self):
        """Asegura que existan los usuarios por defecto"""
        default_users = [
            ("admin@juntaplanificacion.pr.gov", "admin123"),
            ("melendez_ma@jp.pr.gov", "admin123")
        ]
        
        conn = self._get_connection()
        if not conn:
            print("❌ No se puede conectar para crear usuarios por defecto")
            return
        
        try:
            cursor = conn.cursor()
            
            for email, password in default_users:
                # Verificar si el usuario ya existe
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    # Crear el usuario
                    password_hash = self._hash_password(password)
                    cursor.execute("""
                        INSERT INTO usuarios (email, password_hash, is_active)
                        VALUES (?, ?, 1)
                    """, (email, password_hash))
                    print(f"✅ Usuario creado: {email}")
                else:
                    print(f"👤 Usuario ya existe: {email}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error creando usuarios por defecto: {e}")
            if conn:
                conn.close()
    
    def _get_connection(self):
        """Obtiene conexión a la base de datos SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
            return conn
        except Exception as e:
            print(f"ERROR conectando a SQLite: {e}")
            return None
    
    def _hash_password(self, password: str) -> str:
        """Hash simple de contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica si una contraseña coincide con su hash"""
        # Crear hash de la contraseña ingresada
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        return input_hash == password_hash
    
    def authenticate(self, username: str, password: str) -> Dict:
        """
        Autentica un usuario usando la base de datos SQLite
        
        Returns:
            Dict con 'success' (bool), 'message' (str) y 'user' (dict si exitoso)
        """
        print(f"INTENTANDO AUTENTICAR USUARIO: {username}")
        
        conn = self._get_connection()
        if not conn:
            print("No se puede conectar a la base de datos SQLite")
            return {
                'success': False,
                'message': 'Error de conexión a la base de datos'
            }
        
        try:
            cursor = conn.cursor()
            
            # Buscar usuario activo
            cursor.execute("""
                SELECT id, email, password_hash, created_at, is_active, last_login 
                FROM usuarios 
                WHERE email = ? AND is_active = 1
            """, (username,))
            
            user = cursor.fetchone()
            
            if not user:
                print(f"Usuario '{username}' no encontrado o inactivo en la base de datos")
                return {
                    'success': False,
                    'message': 'Usuario no encontrado o inactivo'
                }
            
            # Verificar contraseña usando hash
            if not self._verify_password(password, user['password_hash']):
                print(f"Contraseña incorrecta para usuario '{username}'")
                return {
                    'success': False,
                    'message': 'Usuario o contraseña incorrectos'
                }
            
            # Actualizar último login
            cursor.execute("""
                UPDATE usuarios 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE email = ?
            """, (username,))
            
            conn.commit()
            
            print(f"✅ Autenticación exitosa para usuario '{username}'")
            
            return {
                'success': True,
                'message': 'Autenticación exitosa',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'created_at': user['created_at'],
                    'last_login': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"Error en autenticación SQLite: {e}")
            return {
                'success': False,
                'message': 'Error interno del sistema'
            }
        
        finally:
            conn.close()

# Instancia global
simple_auth = SimpleAuth()

def login_user(username: str, password: str) -> Dict:
    """Función simple para login"""
    return simple_auth.authenticate(username, password)

def is_logged_in(session) -> bool:
    """Verifica si hay una sesión activa"""
    return 'user_id' in session and 'username' in session

def login_required(f):
    """Decorador para rutas que requieren login"""
    from functools import wraps
    from flask import session, redirect, url_for, request
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in(session):
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function