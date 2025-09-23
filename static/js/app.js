/**
 * JP_IA - Sistema de Chat Moderno v4.0
 * Interfaz Avanzada con RAG Híbrido
 */

// ===== CONFIGURACIÓN =====
const CONFIG = {
    API_ENDPOINT: '/chat',
    MAX_MESSAGE_LENGTH: 1000,
    TYPING_DELAY: 1500,
    ANIMATION_DURATION: 300,
    AUTO_SCROLL_THRESHOLD: 100
};

// ===== ESTADO GLOBAL =====
const AppState = {
    currentSessionId: null,
    isTyping: false,
    chatHistory: [],
    currentSpecialist: 'general',
    messageQueue: []
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando JP_IA v4.0...');
    
    AppState.currentSessionId = generateSessionId();
    setupEventListeners();
    initializeInterface();
    
    console.log('✅ JP_IA inicializado correctamente');
});

// ===== CONFIGURACIÓN DE EVENTOS =====
function setupEventListeners() {
    // Input de mensaje
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    if (messageInput) {
        messageInput.addEventListener('keydown', handleKeyDown);
        messageInput.addEventListener('input', handleInputChange);
        messageInput.addEventListener('paste', handlePaste);
    }
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Navegación de especialistas
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            const specialist = this.dataset.specialist;
            switchSpecialist(specialist);
        });
    });
    
    // Toggle móvil
    const mobileToggle = document.getElementById('mobileToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleSidebar);
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }
    
    // Auto-scroll al hacer scroll
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        chatContainer.addEventListener('scroll', handleChatScroll);
    }
}

// ===== INICIALIZACIÓN DE INTERFAZ =====
function initializeInterface() {
    // Auto-resize textarea
    autoResizeTextarea();
    
    // Estado inicial del botón
    updateSendButton();
    
    // Inicializar especialista por defecto
    switchSpecialist('general');
    
    // Mostrar mensaje de bienvenida
    showWelcomeMessage();
}

// ===== MANEJO DE ENTRADA =====
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
    
    if (e.key === 'Escape') {
        clearInput();
    }
}

function handleInputChange() {
    autoResizeTextarea();
    updateSendButton();
    
    // Remover mensaje de bienvenida al empezar a escribir
    const welcomeMessage = document.getElementById('welcomeMessage');
    if (welcomeMessage && this.value.trim()) {
        welcomeMessage.style.display = 'none';
    }
}

function handlePaste(e) {
    // Prevenir pegado de contenido muy largo
    setTimeout(() => {
        const input = e.target;
        if (input.value.length > CONFIG.MAX_MESSAGE_LENGTH) {
            input.value = input.value.substring(0, CONFIG.MAX_MESSAGE_LENGTH);
            showToast('Mensaje truncado al límite máximo', 'warning');
        }
        autoResizeTextarea();
        updateSendButton();
    }, 10);
}

// ===== FUNCIONES DE TEXTAREA =====
function autoResizeTextarea() {
    const textarea = document.getElementById('messageInput');
    if (!textarea) return;
    
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function updateSendButton() {
    const input = document.getElementById('messageInput');
    const button = document.getElementById('sendButton');
    
    if (!input || !button) return;
    
    const hasText = input.value.trim().length > 0;
    const withinLimit = input.value.length <= CONFIG.MAX_MESSAGE_LENGTH;
    
    button.disabled = !hasText || !withinLimit || AppState.isTyping;
    
    // Actualizar ícono según estado
    const icon = button.querySelector('i');
    if (icon) {
        if (AppState.isTyping) {
            icon.className = 'fas fa-spinner fa-spin';
        } else {
            icon.className = 'fas fa-paper-plane';
        }
    }
}

function clearInput() {
    const input = document.getElementById('messageInput');
    if (input) {
        input.value = '';
        autoResizeTextarea();
        updateSendButton();
    }
}

// ===== ENVÍO DE MENSAJES =====
async function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message || AppState.isTyping) return;
    
    // Validaciones
    if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
        showToast('Mensaje demasiado largo', 'error');
        return;
    }
    
    // Limpiar input y actualizar estado
    clearInput();
    AppState.isTyping = true;
    updateSendButton();
    
    // Agregar mensaje del usuario
    addUserMessage(message);
    
    // Mostrar indicador de tipeo
    showTypingIndicator();
    
    try {
        // Enviar solicitud
        const response = await fetch(CONFIG.API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                specialist: AppState.currentSpecialist,
                session_id: AppState.currentSessionId
            })
        });
        
        // Procesar respuesta
        if (response.ok) {
            const data = await response.json();
            hideTypingIndicator();
            
            if (data.success) {
                addBotMessage(data.message, data.sources);
            } else {
                addErrorMessage(data.error || 'Error desconocido');
            }
        } else {
            hideTypingIndicator();
            addErrorMessage(`Error del servidor: ${response.status}`);
        }
        
    } catch (error) {
        console.error('Error enviando mensaje:', error);
        hideTypingIndicator();
        addErrorMessage('Error de conexión. Verifique su internet.');
    } finally {
        AppState.isTyping = false;
        updateSendButton();
    }
}

// ===== MANEJO DE MENSAJES EN UI =====
function addUserMessage(text) {
    const messageId = `msg-${Date.now()}-user`;
    const time = formatTime(new Date());
    
    const messageHtml = `
        <div class="message user-message" id="${messageId}">
            <div class="message-content">
                <div class="message-bubble">
                    <div class="message-text">${escapeHtml(text)}</div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
        </div>
    `;
    
    appendMessage(messageHtml);
    scrollToBottom();
    
    // Guardar en historial
    AppState.chatHistory.push({
        type: 'user',
        text: text,
        timestamp: new Date().toISOString()
    });
}

function addBotMessage(text, sources = []) {
    const messageId = `msg-${Date.now()}-bot`;
    const time = formatTime(new Date());
    
    // Procesar texto para formato markdown básico
    const formattedText = formatBotResponse(text);
    
    // Crear HTML de citas si existen
    let citationsHtml = '';
    if (sources && sources.length > 0) {
        citationsHtml = `
            <div class="message-citations">
                <strong>📚 Fuentes:</strong>
                ${sources.map(source => `<span class="citation">${escapeHtml(source)}</span>`).join(' ')}
            </div>
        `;
    }
    
    const messageHtml = `
        <div class="message bot-message" id="${messageId}">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="message-text">${formattedText}</div>
                    ${citationsHtml}
                    <div class="message-time">${time}</div>
                </div>
            </div>
        </div>
    `;
    
    appendMessage(messageHtml);
    scrollToBottom();
    
    // Guardar en historial
    AppState.chatHistory.push({
        type: 'bot',
        text: text,
        sources: sources,
        timestamp: new Date().toISOString()
    });
}

function addErrorMessage(errorText) {
    const messageId = `msg-${Date.now()}-error`;
    const time = formatTime(new Date());
    
    const messageHtml = `
        <div class="message bot-message" id="${messageId}">
            <div class="message-avatar" style="background: var(--jp-error);">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble" style="border-left: 4px solid var(--jp-error);">
                    <div class="message-text">
                        <strong>❌ Error:</strong> ${escapeHtml(errorText)}
                    </div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
        </div>
    `;
    
    appendMessage(messageHtml);
    scrollToBottom();
    
    showToast('Error en la respuesta', 'error');
}

function appendMessage(messageHtml) {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    
    // Remover mensaje de bienvenida si existe
    const welcomeMessage = document.getElementById('welcomeMessage');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    chatContainer.insertAdjacentHTML('beforeend', messageHtml);
}

// ===== INDICADOR DE TIPEO =====
function showTypingIndicator() {
    const typingId = 'typing-indicator';
    
    // Remover indicador existente
    const existing = document.getElementById(typingId);
    if (existing) existing.remove();
    
    const typingHtml = `
        <div class="message bot-message" id="${typingId}">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span>JP_IA está escribiendo</span>
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    appendMessage(typingHtml);
    scrollToBottom();
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// ===== NAVEGACIÓN DE ESPECIALISTAS =====
function switchSpecialist(specialistId) {
    AppState.currentSpecialist = specialistId;
    
    // Actualizar UI de navegación
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.specialist === specialistId);
    });
    
    // Actualizar header
    updateSpecialistHeader(specialistId);
    
    // Limpiar chat y mostrar bienvenida
    clearChat();
    showWelcomeMessage();
}

function updateSpecialistHeader(specialistId) {
    const specialists = {
        general: {
            title: 'Chat General',
            subtitle: 'Análisis completo de todos los Reglamentos de Planificación',
            icon: 'fas fa-comments'
        },
        procedimientos: {
            title: 'Procedimientos',
            subtitle: 'Trámites administrativos y más',
            icon: 'fas fa-clipboard-list'
        },
        tecnico: {
            title: 'Técnico Gráfico',
            subtitle: 'Planos, mapas y documentos técnicos',
            icon: 'fas fa-drafting-compass'
        },
        edificabilidad: {
            title: 'Edificabilidad',
            subtitle: 'Construcción y densidad urbana',
            icon: 'fas fa-building'
        },
        zonificacion: {
            title: 'Zonificación',
            subtitle: 'Clasificación de uso de suelo',
            icon: 'fas fa-map-marked-alt'
        },
        ambiental: {
            title: 'Ambiental',
            subtitle: 'Impacto ambiental y mitigación',
            icon: 'fas fa-leaf'
        },
        permisos: {
            title: 'Permisos y licencias',
            subtitle: 'Autorizaciones y licencias',
            icon: 'fas fa-file-signature'
        },
        aspectos: {
            title: 'Aspectos ambientales',
            subtitle: 'Normativas ambientales',
            icon: 'fas fa-balance-scale'
        },
        historico: {
            title: 'Histórico',
            subtitle: 'Conservación histórica y cultural',
            icon: 'fas fa-landmark'
        }
    };
    
    const specialist = specialists[specialistId] || specialists.general;
    
    const titleElement = document.getElementById('specialistTitle');
    const subtitleElement = document.getElementById('specialistDescription');
    
    if (titleElement) {
        titleElement.innerHTML = `<i class="${specialist.icon}"></i> ${specialist.title}`;
    }
    
    if (subtitleElement) {
        subtitleElement.textContent = specialist.subtitle;
    }
}

// ===== FUNCIONES DE UI =====
function clearChat() {
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        chatContainer.innerHTML = '';
    }
    AppState.chatHistory = [];
}

function showWelcomeMessage() {
    const welcomeMessage = document.getElementById('welcomeMessage');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'block';
    }
}

function scrollToBottom(smooth = true) {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    
    const scrollOptions = {
        top: chatContainer.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
    };
    
    chatContainer.scrollTo(scrollOptions);
}

function handleChatScroll() {
    // Lógica para manejar scroll si es necesario
    // Por ejemplo, marcar mensajes como leídos
}

// ===== SIDEBAR MÓVIL =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar && overlay) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }
}

// ===== SISTEMA DE TOASTS =====
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
        <div class="toast ${type}" id="${toastId}">
            <div class="toast-content">
                <span>${escapeHtml(message)}</span>
                <button class="toast-close" onclick="removeToast('${toastId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Auto-remove después del duration
    setTimeout(() => removeToast(toastId), duration);
}

function removeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }
}

// ===== UTILIDADES =====
function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

function formatTime(date) {
    return date.toLocaleTimeString('es-PR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBotResponse(text) {
    // Formato básico para respuestas del bot
    return escapeHtml(text)
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\[TOMO ([^\]]+)\]/g, '<span class="citation">TOMO $1</span>');
}

// ===== ATAJOS DE TECLADO =====
document.addEventListener('keydown', function(e) {
    // Ctrl+/ para enfocar input
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        const input = document.getElementById('messageInput');
        if (input) input.focus();
    }
    
    // Escape para cerrar sidebar en móvil
    if (e.key === 'Escape') {
        closeSidebar();
    }
});

// ===== MANEJO DE ERRORES GLOBALES =====
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    showToast('Error inesperado en la aplicación', 'error');
});

// ===== CSS DINÁMICAS ADICIONALES =====
const additionalStyles = `
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .toast-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }
    
    .toast-close {
        background: none;
        border: none;
        cursor: pointer;
        opacity: 0.7;
        padding: 4px;
        border-radius: 4px;
    }
    
    .toast-close:hover {
        opacity: 1;
        background: rgba(0,0,0,0.1);
    }
`;

// Agregar estilos adicionales
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

console.log('✅ JP_IA v4.0 - Sistema de Chat Moderno cargado completamente');