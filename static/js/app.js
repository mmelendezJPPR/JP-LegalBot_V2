/**
 * JP_IA - Sistema de Chat Profesional
 * Versión 2.0 - Optimizada y Moderna
 */

// ===== CONFIGURACIÓN GLOBAL =====
const CONFIG = {
    API_ENDPOINT: '/chat',
    MAX_MESSAGE_LENGTH: 1000,
    AUTO_SAVE_INTERVAL: 30000,
    TYPING_DELAY: 1000,
    ANIMATION_DURATION: 300,
    TOAST_DURATION: 4000
};

// ===== ESTADO GLOBAL =====
const AppState = {
    currentSessionId: null,
    isConnected: true,
    isDarkMode: false,
    isTyping: false,
    messageQueue: [],
    chatHistory: [],
    currentSpecialist: 'general' // Nuevo: especialista actual
};

// ===== INICIALIZACIÓN =====
function initializeApp() {
    console.log('🚀 Inicializando JP_IA v2.0...');
    
    // Generar ID de sesión
    AppState.currentSessionId = generateSessionId();
    
    // Configurar event listeners
    setupEventListeners();
    
    // Configurar tema
    initializeTheme();
    
    // Configurar auto-resize del textarea
    setupTextareaAutoResize();
    
    // Cargar historial si existe
    loadChatHistory();
    
    // Configurar auto-guardado
    setupAutoSave();
    
    // Ocultar loading screen
    hideLoadingScreen();
    
    // Configurar tooltips
    setupTooltips();
    
    console.log('✅ JP_IA inicializado correctamente');
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const mobileToggle = document.getElementById('mobile-menu-toggle');
    
    // Entrada de mensajes
    if (messageInput) {
        messageInput.addEventListener('input', handleInputChange);
        messageInput.addEventListener('keydown', handleKeyDown);
        messageInput.addEventListener('paste', handlePaste);
    }
    
    // Botón de envío
    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }
    
    // Toggle móvil
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Atajos de teclado globales
    document.addEventListener('keydown', handleGlobalKeyboard);
    
    // Eventos de conexión
    window.addEventListener('online', handleConnectionChange);
    window.addEventListener('offline', handleConnectionChange);
    
    // Prevenir envío accidental al cerrar
    window.addEventListener('beforeunload', handleBeforeUnload);
}

// ===== MANEJO DE MENSAJES =====
async function handleSendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message || AppState.isTyping) return;
    
    // Validar longitud del mensaje
    if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
        showToast('El mensaje es demasiado largo', 'error');
        return;
    }
    
    // Limpiar input y actualizar UI
    messageInput.value = '';
    updateCharacterCount();
    updateSendButtonState();
    hideSuggestions();
    
    try {
        // Agregar mensaje del usuario
        addMessage(message, 'user');
        
        // Mostrar indicador de escritura
        showTypingIndicator();
        AppState.isTyping = true;
        
        // Enviar a la API
        const response = await sendToAPI(message);
        
        // Ocultar indicador y mostrar respuesta
        hideTypingIndicator();
        addMessage(response, 'bot');
        
        // Guardar en historial
        saveToHistory(message, response);
        
        // Mostrar sugerencias relacionadas
        showRelatedSuggestions(message);
        
    } catch (error) {
        hideTypingIndicator();
        handleAPIError(error);
    } finally {
        AppState.isTyping = false;
        messageInput.focus();
    }
}

async function sendToAPI(message) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    
    try {
        const response = await fetch(CONFIG.API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
            message: message,
            session_id: AppState.currentSessionId,
            specialist: AppState.currentSpecialist // Enviar especialista actual
        }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        return data.response || 'Lo siento, no pude generar una respuesta adecuada.';
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Tiempo de espera agotado. Por favor, intenta nuevamente.');
        }
        
        throw error;
    }
}

function enviarConsultaRapida(consulta) {
    const messageInput = document.getElementById('message-input');
    messageInput.value = consulta;
    messageInput.focus();
    
    // Efecto visual de enfoque
    messageInput.style.transform = 'scale(1.02)';
    setTimeout(() => {
        messageInput.style.transform = 'scale(1)';
        handleSendMessage();
    }, 150);
}

// ===== MANEJO DE MENSAJES EN UI =====
function addMessage(content, sender, timestamp = null) {
    const container = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    const time = timestamp || new Date().toLocaleTimeString('es-PR', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    messageDiv.className = `message ${sender}-message`;
    
    const avatarIcon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
    const senderName = sender === 'user' ? 'Tú' : 'Experto JP';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="${avatarIcon}"></i>
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender-name">${senderName}</span>
                <span class="message-time">${time}</span>
                ${sender === 'bot' ? `
                    <div class="message-actions">
                        <button class="message-action" onclick="copyMessage(this)" title="Copiar mensaje">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="message-action" onclick="regenerateResponse(this)" title="Regenerar respuesta">
                            <i class="fas fa-redo"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
            <div class="message-text">
                ${formatMessageContent(content)}
            </div>
        </div>
    `;
    
    // Agregar al container y hacer scroll
    container.appendChild(messageDiv);
    
    // Animación de entrada
    requestAnimationFrame(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        
        requestAnimationFrame(() => {
            messageDiv.style.transition = `all ${CONFIG.ANIMATION_DURATION}ms ease-out`;
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        });
    });
    
    scrollToBottom();
    return messageDiv;
}

function formatMessageContent(content) {
    console.log('🔧 Procesando contenido del mensaje:', content.substring(0, 100));
    
    // Si ya contiene HTML (como tablas), devolverlo directamente
    if (content.includes('<table')) {
        console.log('📊 Contenido HTML detectado, pasando directamente');
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong class="texto-importante">$1</strong>')
            .replace(/\*(.*?)\*/g, '<em class="texto-enfasis">$1</em>')
            .replace(/•\s*(.*?)(?=\n|$)/g, '<div class="item-lista">• $1</div>')
            .replace(/---/g, '<div class="separador"></div>');
    }
    
    // Detectar y formatear tablas ASCII (fallback)
    content = formatTables(content);
    
    // Formateo simple y limpio
    return content
        // Remover marcadores técnicos innecesarios
        .replace(/🤖\s*/g, '')
        .replace(/\*\*Sistema:\*\*/g, '')
        .replace(/\*\*Respuesta:\*\*/g, '')
        .replace(/\*\*JP_IA:\*\*/g, '')
        
        // Formateo básico pero elegante
        .replace(/\*\*(.*?)\*\*/g, '<strong class="texto-importante">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="texto-enfasis">$1</em>')
        
        // Listas simples
        .replace(/•\s*(.*?)(?=\n|$)/g, '<div class="item-lista">• $1</div>')
        
        // Separadores de sección
        .replace(/---/g, '<div class="separador"></div>')
        
        // Párrafos naturales
        .replace(/\n\n/g, '</p><p class="parrafo">')
        .replace(/\n/g, '<br>');
}

function formatTables(content) {
    console.log('🔍 Detectando tablas en contenido:', content.substring(0, 200));
    
    // Detectar tablas ASCII con bordes ┌─┐├─┤└─┘
    const tableRegex = /┌[─┬]+┐[\s\S]*?└[─┴]+┘/g;
    
    // También detectar formato simple de tabla
    const simpleTableRegex = /TABLA DE [^:]+:\s*\n([\s\S]*?)(?=\n\n|\n[A-Z]|$)/g;
    
    let result = content;
    
    // Primero intentar formato ASCII completo
    result = result.replace(tableRegex, (match) => {
        console.log('📊 Tabla ASCII detectada:', match.substring(0, 100));
        return convertAsciiTableToHtml(match);
    });
    
    // Luego intentar formato simple
    result = result.replace(simpleTableRegex, (match, tableContent) => {
        console.log('📋 Tabla simple detectada:', match.substring(0, 100));
        return convertSimpleTableToHtml(match, tableContent);
    });
    
    return result;
}

function convertAsciiTableToHtml(asciiTable) {
    const lines = asciiTable.split('\n');
    let htmlTable = '<div class="tabla-formal"><table class="tabla-profesional">';
    
    let isHeader = true;
    
    for (let line of lines) {
        // Saltar líneas de borde
        if (line.includes('┌') || line.includes('└') || line.includes('├')) {
            continue;
        }
        
        // Procesar filas de datos
        if (line.includes('│')) {
            const cells = line.split('│')
                .slice(1, -1) // Remover primero y último elemento vacío
                .map(cell => cell.trim());
            
            if (cells.length > 0 && cells.some(cell => cell.length > 0)) {
                const tag = isHeader ? 'th' : 'td';
                const rowClass = isHeader ? 'tabla-header' : 'tabla-row';
                
                htmlTable += `<tr class="${rowClass}">`;
                for (let cell of cells) {
                    htmlTable += `<${tag} class="tabla-cell">${cell}</${tag}>`;
                }
                htmlTable += '</tr>';
                
                isHeader = false;
            }
        }
    }
    
    htmlTable += '</table></div>';
    return htmlTable;
}

function convertSimpleTableToHtml(fullMatch, tableContent) {
    // Para tablas que no tienen formato ASCII pero están estructuradas
    const lines = tableContent.split('\n').filter(line => line.trim());
    
    if (lines.length < 2) return fullMatch;
    
    let htmlTable = '<div class="tabla-formal"><table class="tabla-profesional">';
    
    // Intentar detectar si hay headers y datos
    let isHeader = true;
    
    for (let line of lines) {
        line = line.trim();
        if (!line) continue;
        
        // Detectar si es una línea de datos (contiene al menos dos elementos separados)
        if (line.includes(':') || line.includes('-') || line.includes('│')) {
            let cells = [];
            
            if (line.includes('│')) {
                cells = line.split('│').map(cell => cell.trim()).filter(cell => cell);
            } else if (line.includes(':')) {
                const parts = line.split(':');
                cells = [parts[0].trim(), parts.slice(1).join(':').trim()];
            } else {
                cells = [line];
            }
            
            if (cells.length > 0) {
                const tag = isHeader ? 'th' : 'td';
                const rowClass = isHeader ? 'tabla-header' : 'tabla-row';
                
                htmlTable += `<tr class="${rowClass}">`;
                for (let cell of cells) {
                    htmlTable += `<${tag} class="tabla-cell">${cell}</${tag}>`;
                }
                htmlTable += '</tr>';
                
                isHeader = false;
            }
        }
    }
    
    htmlTable += '</table></div>';
    
    // Si no se generó contenido de tabla válido, devolver original
    if (htmlTable === '<div class="tabla-formal"><table class="tabla-profesional"></table></div>') {
        return fullMatch;
    }
    
    return htmlTable;
}

// ===== INDICADORES VISUALES =====
function showTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.style.display = 'block';
        scrollToBottom();
    }
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connection-status');
    if (!statusElement) return;
    
    AppState.isConnected = isConnected;
    
    statusElement.innerHTML = isConnected 
        ? '<i class="fas fa-wifi"></i><span>Conectado</span>'
        : '<i class="fas fa-wifi-slash"></i><span>Sin conexión</span>';
    
    statusElement.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
}

// ===== MANEJO DE ENTRADA =====
function handleInputChange(event) {
    const input = event.target;
    const value = input.value;
    
    updateCharacterCount();
    updateSendButtonState();
    
    // Auto-completado y sugerencias
    if (value.length > 2) {
        showSuggestions(value);
    } else {
        hideSuggestions();
    }
}

function handleKeyDown(event) {
    const input = event.target;
    
    if (event.key === 'Enter') {
        if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            handleSendMessage();
        } else if (!event.shiftKey) {
            event.preventDefault();
            handleSendMessage();
        }
    }
    
    // Navegación con teclas de flecha en sugerencias
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        handleSuggestionNavigation(event);
    }
}

function handleGlobalKeyboard(event) {
    if (event.ctrlKey || event.metaKey) {
        switch(event.key) {
            case 'k':
                event.preventDefault();
                focusMessageInput();
                break;
            case 'l':
                event.preventDefault();
                clearChat();
                break;
            case 's':
                event.preventDefault();
                exportChat();
                break;
            case '/':
                event.preventDefault();
                showHelp();
                break;
        }
    }
    
    if (event.key === 'Escape') {
        closeAllModals();
        hideSuggestions();
    }
}

function updateCharacterCount() {
    const input = document.getElementById('message-input');
    const counter = document.getElementById('char-count');
    
    if (input && counter) {
        const count = input.value.length;
        counter.textContent = count;
        
        // Cambiar color según límite
        if (count > CONFIG.MAX_MESSAGE_LENGTH * 0.9) {
            counter.style.color = '#dc2626';
        } else if (count > CONFIG.MAX_MESSAGE_LENGTH * 0.7) {
            counter.style.color = '#d97706';
        } else {
            counter.style.color = '#64748b';
        }
    }
}

function updateSendButtonState() {
    const input = document.getElementById('message-input');
    const button = document.getElementById('send-button');
    
    if (input && button) {
        const hasText = input.value.trim().length > 0;
        const isValidLength = input.value.length <= CONFIG.MAX_MESSAGE_LENGTH;
        
        button.disabled = !hasText || !isValidLength || AppState.isTyping || !AppState.isConnected;
        
        // Efecto visual
        if (hasText && isValidLength) {
            button.classList.add('ready');
        } else {
            button.classList.remove('ready');
        }
    }
}

// ===== FUNCIONES DE UTILIDAD =====
function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function scrollToBottom(smooth = true) {
    const container = document.getElementById('chat-container');
    if (container) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }
}

function focusMessageInput() {
    const input = document.getElementById('message-input');
    if (input) {
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
    }
}

// ===== SISTEMA DE NOTIFICACIONES =====
function showToast(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Animación de entrada
    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    });
    
    // Auto-remove
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// ===== FUNCIONES DE CHAT =====
function clearChat() {
    if (!confirm('¿Estás seguro de que quieres limpiar toda la conversación?')) {
        return;
    }
    
    const container = document.getElementById('chat-container');
    const welcomeMessage = container.querySelector('.welcome-message')?.parentElement;
    
    // Limpiar contenido manteniendo mensaje de bienvenida
    container.innerHTML = '';
    if (welcomeMessage) {
        container.appendChild(welcomeMessage);
    }
    
    // Limpiar historial
    AppState.chatHistory = [];
    localStorage.removeItem(`chat_history_${AppState.currentSessionId}`);
    
    // Nuevo ID de sesión
    AppState.currentSessionId = generateSessionId();
    
    showToast('Conversación limpiada correctamente', 'success');
}

// Función específica para el botón New Chat
function iniciarNuevoChat() {
    clearChat();
}

function exportChat() {
    const messages = AppState.chatHistory;
    
    if (messages.length === 0) {
        showToast('No hay mensajes para exportar', 'warning');
        return;
    }
    
    let content = `Conversación JP_IA - ${new Date().toLocaleString('es-PR')}\n`;
    content += '='.repeat(60) + '\n\n';
    
    messages.forEach((msg, index) => {
        content += `[${msg.timestamp}] ${msg.sender === 'user' ? 'Usuario' : 'JP_IA'}:\n`;
        content += `${msg.content}\n\n`;
    });
    
    downloadFile(content, `JP_IA_Chat_${new Date().toISOString().split('T')[0]}.txt`);
    showToast('Conversación exportada correctamente', 'success');
}

function downloadFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ===== TEMA Y CONFIGURACIÓN =====
function initializeTheme() {
    const savedTheme = localStorage.getItem('jp-ia-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    AppState.isDarkMode = savedTheme === 'dark' || (!savedTheme && prefersDark);
    updateTheme();
}

function toggleTheme() {
    AppState.isDarkMode = !AppState.isDarkMode;
    updateTheme();
    
    const message = AppState.isDarkMode ? 'Tema oscuro activado' : 'Tema claro activado';
    showToast(message, 'info');
}

function updateTheme() {
    const html = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');
    
    if (AppState.isDarkMode) {
        html.classList.add('dark');
        if (themeIcon) themeIcon.className = 'fas fa-sun';
    } else {
        html.classList.remove('dark');
        if (themeIcon) themeIcon.className = 'fas fa-moon';
    }
    
    localStorage.setItem('jp-ia-theme', AppState.isDarkMode ? 'dark' : 'light');
}

// ===== HISTORIAL Y PERSISTENCIA =====
function saveToHistory(userMessage, botResponse) {
    const timestamp = new Date().toLocaleTimeString('es-PR', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    AppState.chatHistory.push(
        { sender: 'user', content: userMessage, timestamp },
        { sender: 'bot', content: botResponse, timestamp }
    );
    
    // Limitar historial a últimos 100 mensajes
    if (AppState.chatHistory.length > 100) {
        AppState.chatHistory = AppState.chatHistory.slice(-100);
    }
    
    saveChatHistory();
}

function saveChatHistory() {
    try {
        localStorage.setItem(
            `chat_history_${AppState.currentSessionId}`, 
            JSON.stringify(AppState.chatHistory)
        );
    } catch (error) {
        console.warn('Error guardando historial:', error);
    }
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem(`chat_history_${AppState.currentSessionId}`);
        if (saved) {
            AppState.chatHistory = JSON.parse(saved);
            
            // Recrear mensajes en la UI
            AppState.chatHistory.forEach(msg => {
                if (msg.sender !== 'welcome') {
                    addMessage(msg.content, msg.sender, msg.timestamp);
                }
            });
        }
    } catch (error) {
        console.warn('Error cargando historial:', error);
        AppState.chatHistory = [];
    }
}

function setupAutoSave() {
    setInterval(() => {
        saveChatHistory();
    }, CONFIG.AUTO_SAVE_INTERVAL);
}

// ===== FUNCIONES DE UI AVANZADAS =====
function setupTextareaAutoResize() {
    const textarea = document.getElementById('message-input');
    if (!textarea) return;
    
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        const maxHeight = 120;
        const newHeight = Math.min(this.scrollHeight, maxHeight);
        this.style.height = newHeight + 'px';
        
        // Ajustar scroll del container si es necesario
        if (this.scrollHeight > maxHeight) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
    });
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }, 1000);
    }
}

function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('modal-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    }
}

function setupTooltips() {
    // Implementar tooltips para botones con data-tooltip
    const elements = document.querySelectorAll('[data-tooltip]');
    
    elements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const element = event.target;
    const text = element.getAttribute('data-tooltip');
    
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    requestAnimationFrame(() => {
        tooltip.style.opacity = '1';
        tooltip.style.transform = 'translateY(0)';
    });
}

function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// ===== SUGERENCIAS INTELIGENTES =====
function showSuggestions(query) {
    const suggestions = getSuggestions(query.toLowerCase());
    const container = document.getElementById('quick-suggestions');
    
    if (!container || suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    container.innerHTML = '';
    suggestions.forEach(suggestion => {
        const chip = document.createElement('div');
        chip.className = 'suggestion-chip';
        chip.textContent = suggestion.text;
        chip.onclick = () => enviarConsultaRapida(suggestion.query);
        container.appendChild(chip);
    });
    
    container.style.display = 'flex';
}

function hideSuggestions() {
    const container = document.getElementById('quick-suggestions');
    if (container) {
        container.style.display = 'none';
    }
}

function getSuggestions(query) {
    const suggestions = [
        { keywords: ['permiso', 'permisos'], text: '📋 Tabla de permisos', query: 'tabla de permisos' },
        { keywords: ['historico', 'histórico', 'conservacion'], text: '🏛️ Sitios históricos', query: 'sitios históricos' },
        { keywords: ['construccion', 'construcción', 'edificar'], text: '🏗️ Permisos de construcción', query: '¿Qué es un permiso de construcción?' },
        { keywords: ['tabla', 'formato'], text: '📊 Menú de tablas', query: 'Generar respuesta en formato tabla' },
        { keywords: ['ayuda', 'help'], text: '❓ Ayuda del sistema', query: 'ayuda' },
        { keywords: ['documento', 'documentos'], text: '📄 Documentos requeridos', query: '¿Qué documentos necesito para un permiso de construcción?' },
        { keywords: ['plazo', 'plazos', 'tiempo'], text: '⏱️ Plazos de tramitación', query: 'plazos de tramitación' },
        { keywords: ['zonificacion', 'zonificación'], text: '🏗️ Requisitos de zonificación', query: 'requisitos zonificación' }
    ];
    
    return suggestions.filter(suggestion => 
        suggestion.keywords.some(keyword => keyword.includes(query) || query.includes(keyword))
    ).slice(0, 3);
}

function showRelatedSuggestions(query) {
    // Mostrar sugerencias relacionadas después de una consulta
    setTimeout(() => {
        const relatedSuggestions = getSuggestions(query.toLowerCase());
        if (relatedSuggestions.length > 0) {
            showSuggestions(query);
        }
    }, 2000);
}

// ===== FUNCIONES DE MODAL =====
function showHelp() {
    const modal = document.getElementById('help-modal');
    const overlay = document.getElementById('modal-overlay');
    
    if (modal && overlay) {
        modal.style.display = 'block';
        overlay.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus en el modal para accesibilidad
        setTimeout(() => {
            const closeButton = modal.querySelector('.modal-close');
            if (closeButton) closeButton.focus();
        }, 100);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    const overlay = document.getElementById('modal-overlay');
    
    if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }
    
    if (overlay) {
        overlay.classList.remove('active');
    }
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal');
    const overlay = document.getElementById('modal-overlay');
    
    modals.forEach(modal => {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    });
    
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// ===== FUNCIONES DE MENSAJE AVANZADAS =====
function copyMessage(button) {
    const messageText = button.closest('.message-content').querySelector('.message-text');
    const text = messageText.textContent || messageText.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Mensaje copiado al portapapeles', 'success');
        
        // Efecto visual en el botón
        const icon = button.querySelector('i');
        const originalClass = icon.className;
        icon.className = 'fas fa-check';
        setTimeout(() => {
            icon.className = originalClass;
        }, 1500);
    }).catch(() => {
        showToast('Error al copiar el mensaje', 'error');
    });
}

function regenerateResponse(button) {
    const messageElement = button.closest('.message');
    const previousMessage = messageElement.previousElementSibling;
    
    if (previousMessage && previousMessage.classList.contains('user-message')) {
        const userText = previousMessage.querySelector('.message-text').textContent;
        
        // Remover la respuesta actual
        messageElement.remove();
        
        // Regenerar respuesta
        enviarConsultaRapida(userText);
        showToast('Regenerando respuesta...', 'info');
    }
}

function handleInternalLink(link) {
    // Manejar enlaces internos del sistema
    switch(link) {
        case 'tabla-permisos':
            enviarConsultaRapida('tabla de permisos');
            break;
        case 'sitios-historicos':
            enviarConsultaRapida('sitios históricos');
            break;
        case 'ayuda':
            showHelp();
            break;
        default:
            console.log('Enlace no reconocido:', link);
    }
}

// ===== MANEJO DE ERRORES =====
function handleAPIError(error) {
    console.error('Error de API:', error);
    
    let errorMessage = 'Ha ocurrido un error inesperado.';
    
    if (error.message.includes('fetch')) {
        errorMessage = 'Error de conexión. Verifica tu conexión a internet.';
        updateConnectionStatus(false);
    } else if (error.message.includes('timeout') || error.message.includes('agotado')) {
        errorMessage = 'Tiempo de espera agotado. El servidor tardó demasiado en responder.';
    } else if (error.message.includes('HTTP 5')) {
        errorMessage = 'Error del servidor. Por favor, intenta nuevamente en unos momentos.';
    } else if (error.message.includes('HTTP 4')) {
        errorMessage = 'Error en la solicitud. Verifica que el mensaje sea válido.';
    }
    
    addMessage(`⚠️ ${errorMessage}`, 'bot');
    showToast(errorMessage, 'error');
}

function handleConnectionChange() {
    const isOnline = navigator.onLine;
    updateConnectionStatus(isOnline);
    
    if (isOnline) {
        showToast('Conexión restablecida', 'success');
    } else {
        showToast('Sin conexión a internet', 'warning');
    }
}

function handleBeforeUnload(event) {
    if (AppState.isTyping || document.getElementById('message-input').value.trim()) {
        event.preventDefault();
        event.returnValue = '¿Estás seguro de que quieres salir? Hay una conversación en progreso.';
        return event.returnValue;
    }
}

function handlePaste(event) {
    // Manejar pegado de contenido (futuro: imágenes, archivos)
    const clipboardData = event.clipboardData;
    const items = clipboardData.items;
    
    for (let item of items) {
        if (item.type.indexOf('image') !== -1) {
            event.preventDefault();
            showToast('Función de imágenes próximamente disponible', 'info');
            break;
        }
    }
}

// ===== FUNCIONES ADICIONALES =====
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {
            showToast('No se pudo activar pantalla completa', 'error');
        });
    } else {
        document.exitFullscreen();
    }
}

function attachFile() {
    showToast('Función de archivos próximamente disponible', 'info');
}

function toggleVoiceInput() {
    showToast('Función de voz próximamente disponible', 'info');
}

// ===== MANEJO DE ESPECIALISTAS =====
function seleccionarEspecialista(especialista) {
    // Actualizar estado global
    AppState.currentSpecialist = especialista;
    
    // Actualizar UI de botones
    document.querySelectorAll('.specialist-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeButton = document.querySelector(`[data-specialist="${especialista}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Actualizar header del chat
    updateChatHeader(especialista);
    
    // Limpiar chat para el nuevo especialista
    iniciarNuevoChat();
    
    // Mostrar mensaje inicial del especialista
    mostrarMensajeInicialEspecialista(especialista);
}

function updateChatHeader(especialista) {
    const especialistas = {
        'general': {
            name: 'Experto JP_IA',
            description: 'Análisis Inteligente de Reglamentos de Planificación',
            icon: 'fas fa-brain',
            status: 'Sistema Experto Activo'
        },
        'procedimientos': {
            name: 'Especialista en Procedimientos',
            description: 'Procesos administrativos y trámites',
            icon: 'fas fa-clipboard-list',
            status: 'Especialista en Procedimientos Activo'
        },
        'tecnico-grafico': {
            name: 'Especialista Técnico Gráfico',
            description: 'Planos, mapas y documentos técnicos',
            icon: 'fas fa-drafting-compass',
            status: 'Especialista Técnico Gráfico Activo'
        },
        'edificabilidad': {
            name: 'Especialista en Edificabilidad',
            description: 'Construcción y densidad urbana',
            icon: 'fas fa-building',
            status: 'Especialista en Edificabilidad Activo'
        },
        'zonificacion': {
            name: 'Especialista en Zonificación',
            description: 'Clasificación y uso del suelo',
            icon: 'fas fa-map-marked-alt',
            status: 'Especialista en Zonificación Activo'
        },
        'ambiental-infraestructura': {
            name: 'Especialista Ambiental',
            description: 'Impacto ambiental e infraestructura',
            icon: 'fas fa-leaf',
            status: 'Especialista Ambiental Activo'
        },
        'historico': {
            name: 'Especialista Histórico',
            description: 'Conservación histórica y cultural',
            icon: 'fas fa-landmark',
            status: 'Especialista Histórico Activo'
        }
    };
    
    const info = especialistas[especialista] || especialistas['general'];
    
    // Actualizar elementos del header
    const titleElement = document.getElementById('specialist-title');
    const nameElement = document.getElementById('specialist-name');
    const descElement = document.getElementById('specialist-description');
    const statusElement = document.getElementById('specialist-status');
    
    if (titleElement && nameElement) {
        titleElement.innerHTML = `<i class="${info.icon}"></i> <span id="specialist-name">${info.name}</span>`;
    }
    if (descElement) {
        descElement.textContent = info.description;
    }
    if (statusElement) {
        statusElement.textContent = info.status;
    }
}

function mostrarMensajeInicialEspecialista(especialista) {
    const mensajes = {
        'general': {
            mensaje: `¡Hola! Soy tu experto en planificación de Puerto Rico. 🎓 Tengo acceso completo a todos los reglamentos y puedo analizar cualquier consulta para darte respuestas precisas y detalladas.`,
            ejemplos: [
                "¿Qué permisos necesito para construir una casa?",
                "Explícame el proceso de zonificación",
                "¿Cuáles son las regulaciones para sitios históricos?",
                "¿Qué agencias están involucradas en X proceso?"
            ]
        },
        'procedimientos': {
            mensaje: `¡Hola! Soy tu especialista en **Procedimientos Administrativos**. 📋 Me enfoco específicamente en procesos, trámites y procedimientos de la Junta de Planificación.`,
            ejemplos: [
                "¿Cuál es el proceso para obtener un permiso de construcción?",
                "¿Qué documentos necesito para solicitar una consulta de ubicación?",
                "¿Cuáles son los pasos para obtener una endorsación?",
                "¿Cómo se tramita una solicitud de variación?"
            ]
        },
        'tecnico-grafico': {
            mensaje: `¡Hola! Soy tu especialista **Técnico Gráfico**. 📐 Me especializo en planos, mapas, documentos técnicos y aspectos gráficos de la planificación.`,
            ejemplos: [
                "¿Qué requisitos tienen los planos de construcción?",
                "¿Cómo debo presentar los mapas de ubicación?",
                "¿Qué especificaciones técnicas necesitan los documentos?",
                "¿Cuáles son los estándares para dibujos técnicos?"
            ]
        },
        'edificabilidad': {
            mensaje: `¡Hola! Soy tu especialista en **Edificabilidad**. 🏗️ Me enfoco en construcción, densidad urbana y aspectos de edificación.`,
            ejemplos: [
                "¿Cuál es la densidad máxima permitida en mi zona?",
                "¿Qué restricciones de altura tienen los edificios?",
                "¿Cómo se calcula el factor de edificabilidad?",
                "¿Qué es el coeficiente de ocupación del lote?"
            ]
        },
        'zonificacion': {
            mensaje: `¡Hola! Soy tu especialista en **Zonificación**. 🗺️ Me especializo en clasificación y uso del suelo, zonificación urbana y rural.`,
            ejemplos: [
                "¿Qué usos están permitidos en mi zona?",
                "¿Cómo se clasifican las zonas urbanas?",
                "¿Qué es una zona de desarrollo planificado?",
                "¿Cuáles son las restricciones por zonificación?"
            ]
        },
        'ambiental-infraestructura': {
            mensaje: `¡Hola! Soy tu especialista **Ambiental**. 🌿 Me enfoco en impacto ambiental, infraestructura y sostenibilidad.`,
            ejemplos: [
                "¿Qué estudios ambientales necesito para mi proyecto?",
                "¿Cuáles son los requisitos de infraestructura?",
                "¿Cómo evalúo el impacto ambiental?",
                "¿Qué regulaciones ambientales aplican?"
            ]
        },
        'historico': {
            mensaje: `¡Hola! Soy tu especialista en **Conservación Histórica**. 🏛️ Me especializo en sitios históricos, patrimonio cultural y conservación.`,
            ejemplos: [
                "¿Cómo designo un sitio como histórico?",
                "¿Qué restricciones tienen los edificios históricos?",
                "¿Cuál es el proceso de conservación histórica?",
                "¿Qué incentivos existen para la conservación?"
            ]
        }
    };
    
    const info = mensajes[especialista] || mensajes['general'];
    
    // Crear mensaje con ejemplos
    let mensajeCompleto = info.mensaje;
    
    if (info.ejemplos && info.ejemplos.length > 0) {
        mensajeCompleto += `\n\n**Pregúntame sobre:**\n`;
        info.ejemplos.forEach(ejemplo => {
            mensajeCompleto += `• ${ejemplo}\n`;
        });
    }
    
    mensajeCompleto += `\n¡Pregúntame lo que necesites sobre mi área de especialización!`;
    
    // Agregar mensaje al chat
    addMessage(mensajeCompleto, 'bot');
}

// ===== INICIALIZACIÓN GLOBAL =====
// Configurar variables globales para compatibilidad
window.AppState = AppState;
window.CONFIG = CONFIG;
window.enviarMensaje = handleSendMessage;
window.enviarConsultaRapida = enviarConsultaRapida;
window.iniciarNuevoChat = iniciarNuevoChat;
window.clearChat = clearChat;
window.exportChat = exportChat;
window.showHelp = showHelp;
window.toggleTheme = toggleTheme;
window.copyMessage = copyMessage;
window.regenerateResponse = regenerateResponse;
window.handleInternalLink = handleInternalLink;
window.closeModal = closeModal;
window.closeAllModals = closeAllModals;
window.toggleMobileMenu = toggleMobileMenu;
window.toggleFullscreen = toggleFullscreen;
window.attachFile = attachFile;
window.toggleVoiceInput = toggleVoiceInput;
window.seleccionarEspecialista = seleccionarEspecialista; // Nueva función

// Debug info
console.log('🔧 JP_IA JavaScript cargado correctamente');
console.log('📊 Estado de la aplicación disponible en window.AppState');
console.log('⚙️ Configuración disponible en window.CONFIG');