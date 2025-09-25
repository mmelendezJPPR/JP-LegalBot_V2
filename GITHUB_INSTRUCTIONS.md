# 📋 INSTRUCCIONES PARA SUBIR A GITHUB

## 🛠️ Preparación Previa

### 1. Instalar Git (si no está instalado)
- Descargar desde: https://git-scm.com/download/win
- Instalar con configuración por defecto
- Reiniciar terminal después de la instalación

### 2. Verificar que Git funciona
```bash
git --version
```

## 🚀 Subir Proyecto a GitHub

### Método 1: Script Automático
```bash
python prepare_github.py
```

### Método 2: Manual
```bash
# 1. Inicializar repositorio
git init

# 2. Configurar usuario
git config user.name "Miguel Melendez"
git config user.email "melendez_ma@jp.pr.gov"

# 3. Agregar archivos
git add .

# 4. Hacer commit inicial
git commit -m "Initial commit: JP-LegalBot V2 con autenticación SQLite y mejoras de UI"

# 5. Agregar repositorio remoto
git remote add origin https://github.com/mmelendezJPPR/JP-LegalBot_V2.git

# 6. Cambiar a rama main
git branch -M main

# 7. Subir a GitHub
git push -u origin main
```

## 📝 Cambios Principales en V2

### ✅ Sistema de Autenticación
- ✅ Autenticación SQLite integrada
- ✅ Base de datos de usuarios (`database/Usuarios.db`)
- ✅ Login forzado al acceder al sistema
- ✅ Gestión completa de usuarios

### ✅ Mejoras de UI/UX
- ✅ Output limpio (solo texto, sin colores)
- ✅ Palabras importantes en **negrita**
- ✅ Logo corporativo JP_V2.png
- ✅ Interfaz moderna y profesional

### ✅ Sistema de IA Mejorado
- ✅ Búsqueda cuantitativa más profunda
- ✅ Análisis detallado de documentos
- ✅ Integración con Azure OpenAI GPT-4.1
- ✅ Respuestas más precisas y contextuales

### ✅ Arquitectura Optimizada
- ✅ Código limpio y organizado
- ✅ Eliminación de archivos temporales
- ✅ Scripts de gestión de usuarios
- ✅ Documentación actualizada

## 🔐 Credenciales de Acceso

### Usuario Admin Predeterminado:
- **Email:** admin@juntaplanificacion.pr.gov
- **Contraseña:** admin123

### Gestión de Usuarios:
```bash
python scripts/manage_usuarios.py
```

## 📁 Estructura Final del Proyecto

```
JP-LegalBot_V2-Render/
├── 📱 app.py                     # Aplicación principal
├── 🔐 core/auth.py              # Sistema de autenticación
├── 🤖 ai_system/                # Sistema de IA
├── 💾 database/Usuarios.db      # Base de datos de usuarios
├── 🛠️ scripts/                 # Scripts de gestión
├── 🎨 static/                   # Recursos frontend
├── 📄 templates/                # Templates HTML
├── 📚 data/                     # Documentos y conocimiento
└── 📋 requirements.txt          # Dependencias
```

## 🌐 URLs del Proyecto

- **GitHub:** https://github.com/mmelendezJPPR/JP-LegalBot_V2
- **Render:** (Configurar después del push)
- **Local:** http://127.0.0.1:5000

---

🎉 **¡Proyecto listo para GitHub!**