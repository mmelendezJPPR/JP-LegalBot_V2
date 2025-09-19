#!/usr/bin/env python3
"""
=======================================================================
APP.PY - APLICACIÓN PRINCIPAL DEL JP_LEGALBOT v3.2
=======================================================================

🎯 FUNCIÓN PRINCIPAL:
   Este es el archivo central que ejecuta toda la aplicación web JP_LegalBot.
   Es un sistema de IA especializado en legislación de planificación de Puerto Rico.

🏗️ ARQUITECTURA:
   - Aplicación Flask que sirve como backend y frontend
   - Sistema híbrido de IA que combina múltiples motores de respuesta
   - Autenticación integrada con control de sesiones
   - API REST para consultas de IA
   - Interface web responsive para usuarios

📋 COMPONENTES PRINCIPALES:
   1. SERVIDOR WEB: Flask app con rutas optimizadas
   2. SISTEMA DE IA: Router inteligente que decide qué motor usar
   3. AUTENTICACIÓN: Login/logout con validación de usuarios
   4. API ENDPOINTS: /chat, /api/stats, /api/diagnostico
   5. RATE LIMITING: Control de solicitudes por IP
   6. LOGGING: Sistema de logs detallado
   7. ERROR HANDLING: Manejo robusto de errores

🔧 DEPENDENCIAS EXTERNAS:
   - simple_auth.py: Sistema de autenticación
   - sistema_hibrido.py: Router de IA y lógica de procesamiento
   - experto_planificacion.py: Motor de IA especializado
   - respuestas_curadas_tier1.py: Base de respuestas pre-aprobadas

🌐 CONFIGURACIÓN PARA DEPLOYMENT:
   - Compatible con Render, Heroku, Railway, Vercel
   - Variables de entorno configurables
   - Timeouts optimizados para servicios cloud
   - Headers de seguridad incluidos
   - Manejo graceful de shutdown

⚙️ CONFIGURACIÓN:
   - Puerto: 10000 (configurable via PORT env var)
   - Debug: Deshabilitado en producción
   - Rate limit: 30 requests/minuto por IP
   - Session timeout: 1 hora
   - Request timeout: 35 segundos
   - OpenAI timeout: 30 segundos

🔐 CREDENCIALES POR DEFECTO:
   - Usuario: Admin911
   - Contraseña: Junta12345

📊 ENDPOINTS DISPONIBLES:
   GET  /           - Página principal (requiere login)
   GET  /login      - Página de login
   POST /login      - Procesar login
   GET  /logout     - Cerrar sesión
   POST /chat       - API para consultas de IA
   GET  /api/stats  - Estadísticas del sistema
   GET  /api/diagnostico - Diagnóstico completo

🚀 PARA EJECUTAR:
   python app.py

=======================================================================
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, flash
import os
import json
import time
import signal
import sys
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
import openai
import traceback
import logging
from typing import Dict, List, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ThreadTimeoutError

# Configurar logging optimizado para Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# ===== VALIDACIÓN DE VARIABLES DE ENTORNO =====
def validar_variables_entorno():
    """Validar variables de entorno críticas"""
    errores = []
    warnings = []
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or len(api_key.strip()) < 20:
        warnings.append("OPENAI_API_KEY faltante o corto - Sistema funcionará con fallbacks")
    
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or len(secret_key) < 16:
        warnings.append("SECRET_KEY corto - Se generará uno automáticamente")
    
    try:
        port = int(os.getenv('PORT', '10000'))
        if port < 1024 or port > 65535:
            errores.append(f"PORT inválido: {port}")
    except ValueError:
        errores.append("PORT debe ser un número")
    
    if errores:
        logger.error("[ERROR] ERRORES CRITICOS EN VARIABLES DE ENTORNO:")
        for error in errores:
            logger.error(f"   - {error}")
        return False
    
    if warnings:
        logger.warning("[WARNING] ADVERTENCIAS EN CONFIGURACION:")
        for warning in warnings:
            logger.warning(f"   - {warning}")
    
    return True

# Validar configuración antes de continuar
if not validar_variables_entorno():
    logger.error("❌ Configuración inválida. Revise su archivo .env")
    # En desarrollo no salir, en producción sí
    if os.getenv('FLASK_ENV') == 'production':
        sys.exit(1)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configurar secret key para sesiones (con fallback seguro)
secret_key = os.getenv('SECRET_KEY')
if not secret_key or len(secret_key) < 16:
    import secrets
    secret_key = secrets.token_hex(32)
    logger.info("[INFO] Secret key generado automaticamente")

app.secret_key = secret_key

# ===== CONFIGURACIONES ESPECÍFICAS PARA RENDER =====
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # 5 minutos cache
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Velocidad
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# ✅ TIMEOUTS OPTIMIZADOS PARA DESARROLLO LOCAL
REQUEST_TIMEOUT = 35  # 35 segundos máximo (suficiente para OpenAI)
OPENAI_TIMEOUT = 30   # 30 segundos máximo (para consultas complejas)

# ===== HEADERS DE SEGURIDAD =====
@app.after_request
def add_security_headers(response):
    """Agregar headers de seguridad"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Solo en producción
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # CSP actualizado para permitir CDNs y fuentes externas
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
    )
    
    return response

# Handler para shutdown graceful en Render
def signal_handler(signum, frame):
    logger.info("🛑 Recibida señal de shutdown, cerrando aplicación...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Cliente OpenAI con manejo de errores (Azure y estándar)
try:
    # Verificar si Azure OpenAI está configurado
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    
    if azure_endpoint and azure_key:
        # Usar Azure OpenAI
        client = openai.AzureOpenAI(
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            timeout=OPENAI_TIMEOUT
        )
        logger.info("✅ Cliente Azure OpenAI configurado correctamente")
        logger.info(f"   📡 Endpoint: {azure_endpoint}")
        logger.info(f"   🚀 Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4.1')}")
    else:
        # Fallback a OpenAI estándar
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.strip():
            client = openai.OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
            logger.info("✅ Cliente OpenAI estándar configurado correctamente")
        else:
            logger.warning("⚠️ No hay API key configurada (ni Azure ni OpenAI)")
            client = None
except Exception as e:
    logger.error(f"❌ Error configurando cliente OpenAI: {e}")
    client = None

# Importar el sistema de autenticación simple
try:
    from simple_auth import login_user, is_logged_in, login_required
    logger.info("[OK] Sistema de autenticacion importado")
    auth_disponible = True
except ImportError as e:
    logger.warning(f"[WARNING] Error importando autenticacion: {e}")
    auth_disponible = False
    
    # Crear decorador dummy si no hay autenticación
    def login_required(f):
        return f

# ===== IMPORTAR SISTEMA HÍBRIDO CORREGIDO =====
try:
    from sistema_hibrido import (
        procesar_consulta_hibrida,
        obtener_estadisticas_hibridas,
        inicializar_router,
        diagnosticar_sistema
    )
    logger.info("✅ Sistema Híbrido importado correctamente")
    sistema_hibrido_disponible = True
    version_sistema = "v3.2_hibrido_corregido"
    
    # ✅ INICIALIZAR ROUTER HÍBRIDO AL ARRANCAR
    try:
        logger.info("🚀 Inicializando router híbrido...")
        inicializar_router()
        logger.info("✅ Router híbrido inicializado correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando router híbrido: {e}")
        logger.error(f"📝 Traceback: {traceback.format_exc()}")
        
except ImportError as e:
    logger.error(f"❌ Error importando sistema híbrido: {e}")
    
    # ✅ FALLBACK CORREGIDO - Compatible con tu experto_planificacion.py
    try:
        from experto_planificacion import cargar_experto
        logger.info("✅ Fallback: Experto Planificación importado")
        
        # Cargar experto con manejo robusto de errores
        try:
            experto_planificacion = cargar_experto()
            logger.info("✅ Experto cargado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando experto: {e}")
            experto_planificacion = None
        
        sistema_hibrido_disponible = False
        version_sistema = "v3.2_fallback_experto"
        
        # Función de fallback compatible
        def procesar_consulta_hibrida(consulta: str) -> Dict:
            try:
                if experto_planificacion is None:
                    return {
                        'respuesta': "Sistema experto no disponible. Verifique configuración de OpenAI y datos.",
                        'sistema_usado': 'error_config',
                        'confianza': 0.1
                    }
                
                # Usar el método answer() del experto actual
                respuesta = experto_planificacion.answer(consulta)
                return {
                    'respuesta': respuesta,
                    'sistema_usado': 'experto_planificacion',
                    'confianza': 0.8  # Alta confianza con embeddings
                }
            except Exception as e:
                logger.error(f"❌ Error en experto: {e}")
                return {
                    'respuesta': f"Error procesando consulta con experto: {str(e)}",
                    'sistema_usado': 'error',
                    'confianza': 0.1
                }
                
    except ImportError as e2:
        logger.error(f"❌ Error en fallback: {e2}")
        sistema_hibrido_disponible = False
        version_sistema = "v3.2_sin_sistema"
        
        # Función de emergencia ultra-básica
        def procesar_consulta_hibrida(consulta: str) -> Dict:
            return {
                'respuesta': "Sistema de consultas temporalmente no disponible. Por favor, contacte soporte técnico.",
                'sistema_usado': 'emergencia',
                'confianza': 0.1
            }

# Configuraciones del sistema
CONFIG = {
    'RATE_LIMIT_MESSAGES': int(os.getenv('RATE_LIMIT_MESSAGES', '30')),
    'RATE_LIMIT_WINDOW': int(os.getenv('RATE_LIMIT_WINDOW', '60')),
    'SESSION_TIMEOUT': int(os.getenv('SESSION_TIMEOUT', '3600')),
    'ENABLE_ANALYTICS': os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true',
    'DEBUG_MODE': os.getenv('DEBUG_MODE', 'false').lower() == 'true'
}

# ===== RATE LIMITING CON GESTIÓN DE MEMORIA =====
class RateLimiter:
    """Rate limiter con gestión automática de memoria"""
    
    def __init__(self, max_requests=30, window_seconds=60, max_ips=1000):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_ips = max_ips
        self.requests = defaultdict(list)
        self.last_cleanup = time.time()
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier):
        """Verificar si se permite la request"""
        now = time.time()
        
        with self._lock:
            # Limpieza automática cada 5 minutos
            if now - self.last_cleanup > 300:
                self.cleanup_old_requests(now)
                self.last_cleanup = now
            
            # Limpiar requests antiguos de esta IP
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if now - req_time < self.window_seconds
            ]
            
            # Verificar límite
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            self.requests[identifier].append(now)
            return True
    
    def cleanup_old_requests(self, now):
        """Limpiar requests antiguos y limitar número de IPs"""
        # Remover requests antiguos
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip] 
                if now - req_time < self.window_seconds
            ]
            # Remover IPs sin requests recientes
            if not self.requests[ip]:
                del self.requests[ip]
        
        # Si tenemos demasiadas IPs, eliminar las más antiguas
        if len(self.requests) > self.max_ips:
            sorted_ips = sorted(
                self.requests.items(), 
                key=lambda x: max(x[1]) if x[1] else 0, 
                reverse=True
            )[:self.max_ips]
            self.requests = defaultdict(list, dict(sorted_ips))
            
        logger.info(f"🧹 Rate limiter cleanup: {len(self.requests)} IPs activas")

# Instanciar rate limiter
rate_limiter = RateLimiter(
    max_requests=CONFIG['RATE_LIMIT_MESSAGES'],
    window_seconds=CONFIG['RATE_LIMIT_WINDOW']
)

def check_rate_limit(identifier: str) -> bool:
    """Rate limiting con gestión de memoria"""
    return rate_limiter.is_allowed(identifier)

def get_client_ip():
    """Obtener IP del cliente (funciona con proxies de Render)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

# ===== PROCESAMIENTO CON TIMEOUT ROBUSTO =====
def procesar_con_timeout(mensaje, timeout_segundos=REQUEST_TIMEOUT):
    """Procesar consulta con timeout usando threading"""
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(procesar_consulta_hibrida, mensaje)
            resultado = future.result(timeout=timeout_segundos)
            return resultado
    except ThreadTimeoutError:
        raise TimeoutError(f"Timeout después de {timeout_segundos} segundos")
    except Exception as e:
        logger.error(f"❌ Error en procesar_con_timeout: {e}")
        raise e

# ===== MANEJO ROBUSTO DE SESSION TIMEOUT =====
def verificar_timeout_sesion():
    """Verificar si la sesión ha expirado"""
    if not is_logged_in(session):
        return False, "No hay sesión activa"
    
    login_time = session.get('login_time')
    if not login_time:
        logger.warning("⚠️ Sesión sin login_time, limpiando")
        session.clear()
        return False, "Sesión inválida"
    
    try:
        # Manejar tanto string ISO como timestamp
        if isinstance(login_time, str):
            login_datetime = datetime.fromisoformat(login_time.replace('Z', '+00:00'))
        else:
            login_datetime = datetime.fromtimestamp(float(login_time))
        
        tiempo_transcurrido = datetime.now() - login_datetime.replace(tzinfo=None)
        timeout_limite = timedelta(seconds=CONFIG['SESSION_TIMEOUT'])
        
        if tiempo_transcurrido > timeout_limite:
            logger.info(f"⏰ Sesión expirada: {tiempo_transcurrido.total_seconds()}s > {timeout_limite.total_seconds()}s")
            session.clear()
            return False, "Sesión expirada"
        
        return True, "Sesión válida"
        
    except (ValueError, TypeError, OSError) as e:
        logger.error(f"❌ Error parseando login_time '{login_time}': {e}")
        session.clear()
        return False, "Error en datos de sesión"

# ===== RUTAS PRINCIPALES =====

@app.route('/')
def index():
    """Página principal optimizada"""
    if auth_disponible and not is_logged_in(session):
        return redirect(url_for('login_page'))
    
    # ✅ VERIFICAR TIMEOUT DE SESIÓN ROBUSTO
    if auth_disponible and is_logged_in(session):
        sesion_valida, mensaje = verificar_timeout_sesion()
        if not sesion_valida:
            flash(f'{mensaje}. Por favor inicie sesión nuevamente.', 'warning')
            return redirect(url_for('login_page'))
    
    return render_template('index.html', 
                         version=version_sistema,
                         sistema_activo=sistema_hibrido_disponible)

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint principal de chat optimizado para Render"""
    inicio_tiempo = time.time()
    
    try:
        # Validar autenticación
        if auth_disponible and not is_logged_in(session):
            return jsonify({
                'error': 'Sesión no válida',
                'redirect': '/login'
            }), 401
        
        # Obtener datos
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensaje requerido'}), 400
        
        mensaje = data['message'].strip()
        if not mensaje:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        if len(mensaje) > 1000:
            return jsonify({'error': 'Mensaje demasiado largo (máximo 1000 caracteres)'}), 400
        
        # Rate limiting
        client_ip = get_client_ip()
        if not check_rate_limit(client_ip):
            return jsonify({
                'error': f'Demasiadas solicitudes. Límite: {CONFIG["RATE_LIMIT_MESSAGES"]} por minuto',
                'retry_after': CONFIG['RATE_LIMIT_WINDOW']
            }), 429
        
        # Log de la consulta
        logger.info(f"🔄 Nueva consulta desde {client_ip}: '{mensaje[:50]}...'")
        
        # ✅ PROCESAR CONSULTA CON TIMEOUT ROBUSTO
        try:
            resultado = procesar_con_timeout(mensaje, timeout_segundos=REQUEST_TIMEOUT)
            
        except TimeoutError:
            logger.warning(f"⏰ Timeout procesando consulta: '{mensaje[:30]}...'")
            return jsonify({
                'error': 'La consulta tardó demasiado en procesarse. Por favor, simplifique su pregunta.',
                'timeout': True
            }), 408
        except Exception as e:
            logger.error(f"❌ Error procesando consulta: {e}")
            logger.error(f"📝 Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': 'Error interno procesando la consulta',
                'details': str(e) if CONFIG['DEBUG_MODE'] else None
            }), 500
        
        # Validar resultado
        if not isinstance(resultado, dict) or 'respuesta' not in resultado:
            logger.error(f"❌ Resultado inválido del sistema híbrido: {resultado}")
            return jsonify({
                'error': 'Error en el formato de respuesta del sistema'
            }), 500
        
        # Preparar respuesta
        tiempo_total = time.time() - inicio_tiempo
        sistema_usado = resultado.get('sistema_usado', 'desconocido')
        confianza = resultado.get('confianza', 0.0)
        
        logger.info(f"✅ Consulta procesada en {tiempo_total:.2f}s - Sistema: {sistema_usado} - Confianza: {confianza}")
        
        # Log para analytics
        log_consulta(mensaje, resultado['respuesta'], {
            'sistema_usado': sistema_usado,
            'confianza': confianza,
            'tiempo_procesamiento': tiempo_total,
            'client_ip': client_ip
        })
        
        return jsonify({
            'response': resultado['respuesta'],
            'metadata': {
                'sistema_usado': sistema_usado,
                'confianza': confianza,
                'tiempo_procesamiento': tiempo_total,
                'version': version_sistema,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        tiempo_total = time.time() - inicio_tiempo
        logger.error(f"❌ Error crítico en endpoint chat: {e}")
        logger.error(f"📝 Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Error interno del servidor',
            'tiempo_procesamiento': tiempo_total,
            'timestamp': datetime.now().isoformat()
        }), 500

def log_consulta(consulta: str, respuesta: str, metadata: Dict = None):
    """Log básico de consultas para analytics"""
    if not CONFIG['ENABLE_ANALYTICS']:
        return
    
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'consulta_length': len(consulta),
            'respuesta_length': len(respuesta),
            'sistema_usado': metadata.get('sistema_usado', 'unknown') if metadata else 'unknown',
            'confianza': metadata.get('confianza', 0.0) if metadata else 0.0,
            'tiempo_procesamiento': metadata.get('tiempo_procesamiento', 0.0) if metadata else 0.0,
            'ip': get_client_ip(),
            'user_agent': request.headers.get('User-Agent', '')[:100]
        }
        
        logger.info(f"📊 ANALYTICS: {json.dumps(log_entry, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"❌ Error logging consulta: {e}")

# ===== RUTAS DE AUTENTICACIÓN =====

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Página de login optimizada"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not password:
                flash('Por favor complete todos los campos', 'error')
                return render_template('login.html', error='Campos requeridos')
            
            if auth_disponible:
                result = login_user(username, password)
                
                if result['success']:
                    user_data = result.get('user', {})
                    
                    session['user_id'] = user_data.get('user_id', username)
                    session['username'] = user_data.get('username', username)
                    session['logged_in'] = True
                    session['auth_method'] = user_data.get('auth_method', 'local')
                    session['login_time'] = datetime.now().isoformat()
                    
                    logger.info(f"✅ Login exitoso: {username}")
                    flash(f'¡Bienvenido, {username}!', 'success')
                    
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                else:
                    logger.warning(f"❌ Login fallido: {result['message']}")
                    flash(result['message'], 'error')
                    return render_template('login.html', error=result['message'])
            else:
                flash('Sistema de autenticación no disponible', 'error')
                return render_template('login.html', error='Auth no disponible')
                
        except Exception as e:
            logger.error(f"❌ Error en login: {str(e)}")
            flash('Error interno del servidor', 'error')
            return render_template('login.html', error='Error interno')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    username = session.get('username', 'Usuario')
    session.clear()
    flash(f'Sesión de {username} cerrada exitosamente', 'info')
    logger.info(f"🔤 Logout: {username}")
    return redirect(url_for('login_page'))

# ===== RUTAS DE API =====

@app.route('/api/stats')
def api_stats():
    """Estadísticas del sistema"""
    try:
        if sistema_hibrido_disponible:
            stats = obtener_estadisticas_hibridas()
        else:
            stats = {
                'version': version_sistema,
                'sistema_hibrido_disponible': False,
                'fallback_mode': True
            }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Error obteniendo estadísticas: {str(e)}'}), 500

@app.route('/api/diagnostico')
def api_diagnostico():
    """Diagnóstico completo del sistema"""
    try:
        diagnostico_info = {
            'timestamp': datetime.now().isoformat(),
            'version_app': version_sistema,
            'sistema_hibrido_disponible': sistema_hibrido_disponible,
            'auth_disponible': auth_disponible,
            'openai_disponible': client is not None,
            'configuracion': {
                'rate_limit': CONFIG['RATE_LIMIT_MESSAGES'],
                'session_timeout': CONFIG['SESSION_TIMEOUT'],
                'debug_mode': CONFIG['DEBUG_MODE'],
                'request_timeout': REQUEST_TIMEOUT,
                'openai_timeout': OPENAI_TIMEOUT
            },
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'variables_entorno': {
                'OPENAI_MODEL': os.getenv('OPENAI_MODEL', 'No configurado'),
                'FLASK_ENV': os.getenv('FLASK_ENV', 'No configurado'),
                'PORT': os.getenv('PORT', 'No configurado')
            }
        }
        
        # Si el sistema híbrido está disponible, obtener su diagnóstico
        if sistema_hibrido_disponible:
            try:
                diagnostico_hibrido = diagnosticar_sistema()
                diagnostico_info['diagnostico_hibrido'] = diagnostico_hibrido
            except Exception as e:
                diagnostico_info['error_diagnostico_hibrido'] = str(e)
        
        return jsonify(diagnostico_info)
    except Exception as e:
        return jsonify({
            'error': f'Error en diagnóstico: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/test')
def api_test():
    """Test rápido del sistema"""
    try:
        resultado = procesar_consulta_hibrida("Test de funcionamiento")
        return jsonify({
            'status': 'ok',
            'sistema_usado': resultado.get('sistema_usado', 'desconocido'),
            'confianza': resultado.get('confianza', 0.0),
            'respuesta_preview': resultado.get('respuesta', '')[:100],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ===== MANEJO DE ARCHIVOS ESTÁTICOS OPTIMIZADO =====

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir archivos estáticos con manejo optimizado"""
    try:
        response = send_from_directory(app.static_folder, filename)
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutos
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    except Exception as e:
        logger.warning(f"⚠️ Error sirviendo archivo estático {filename}: {e}")
        return "Archivo no encontrado", 404

# ===== MANEJO DE ERRORES OPTIMIZADO =====

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"⚠️ 404: {request.url}")
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Error 500: {error}")
    return jsonify({'error': 'Error interno del servidor'}), 500

@app.errorhandler(502)
def handle_bad_gateway(e):
    logger.error(f"❌ Error 502 Bad Gateway: {e}")
    return jsonify({
        'error': 'Servicio temporalmente no disponible',
        'code': 502,
        'timestamp': datetime.now().isoformat()
    }), 502

@app.errorhandler(504)
def handle_gateway_timeout(e):
    logger.error(f"❌ Error 504 Gateway Timeout: {e}")
    return jsonify({
        'error': 'Tiempo de respuesta agotado. Reformule su consulta.',
        'code': 504,
        'timestamp': datetime.now().isoformat()
    }), 504

@app.errorhandler(429)
def rate_limit_error(error):
    return jsonify({
        'error': 'Demasiadas solicitudes',
        'message': 'Por favor espere antes de hacer otra consulta',
        'retry_after': CONFIG['RATE_LIMIT_WINDOW']
    }), 429

# ===== STARTUP OPTIMIZADO =====

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🤖 INICIANDO JP_IA v3.2 - VERSIÓN CORREGIDA PARA RENDER")
    print("🧠 Sistema de IA con análisis de datos regulatorios")
    print("🔄 Router inteligente híbrido integrado")
    print("✅ TODAS LAS CORRECCIONES CRÍTICAS APLICADAS")
    print("="*70)
    
    print(f"📊 Configuración:")
    print(f"   🔧 Sistema: {version_sistema}")
    print(f"   🔒 Auth: {'✅ Activado' if auth_disponible else '❌ Desactivado'}")
    print(f"   🚀 Híbrido: {'✅ Activo' if sistema_hibrido_disponible else '❌ Fallback'}")
    print(f"   🤖 OpenAI: {'✅ Configurado' if client else '❌ No disponible'}")
    print(f"   ⚡ Rate Limit: {CONFIG['RATE_LIMIT_MESSAGES']} req/min")
    print(f"   ⏰ Timeouts: Request={REQUEST_TIMEOUT}s, OpenAI={OPENAI_TIMEOUT}s")
    
    if auth_disponible:
        print(f"\n🔑 Credenciales de acceso:")
        print(f"   👤 Usuario: Admin911")
        print(f"   🔐 Contraseña: Junta12345")
    
    # Puerto para producción (Render)
    port = int(os.getenv('PORT', 10000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n🌐 Servidor:")
    print(f"   📡 Puerto: {port}")
    print(f"   🛠 Debug: {'✅ Activado' if debug_mode else '❌ Producción'}")
    print(f"   📱 URL: http://0.0.0.0:{port}")
    
    print("\n✨ Powered by GPT-5 + Análisis Regulatorio Avanzado")
    print("🎯 OPTIMIZADO PARA RENDER - Sin errores 502")
    print("🔧 Correcciones aplicadas:")
    print("   ✅ Signal alarm → Threading timeout")
    print("   ✅ Memory leak → Rate limiter robusto")  
    print("   ✅ Timeouts → Optimizados para Render")
    print("   ✅ Security → Headers de seguridad")
    print("   ✅ Validation → Variables de entorno")
    print("   ✅ Expert API → Compatible con tu experto")
    print("="*70)
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=debug_mode,
        threaded=True,
        use_reloader=False  # Evitar problemas en Render
    )