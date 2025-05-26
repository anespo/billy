/**
 * EnergyWise Chatbot - Frontend JavaScript
 */

// Classe principale del chatbot
class EnergyWiseChatbot {
    constructor() {
        this.chatbotIcon = null;
        this.chatWindow = null;
        this.messageContainer = null;
        this.messageInput = null;
        this.sendButton = null;
        this.uploadButton = null;
        this.closeButton = null;
        this.fileInput = null;
        this.isOpen = false;
        this.isProcessing = false;
        this.userId = this.generateUserId();
        this.init();
    }

    // Inizializza il chatbot
    init() {
        this.createChatbotIcon();
        this.createChatWindow();
        this.setupEventListeners();
    }

    // Genera un ID utente univoco
    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }

    // Crea l'icona del chatbot
    createChatbotIcon() {
        this.chatbotIcon = document.createElement('div');
        this.chatbotIcon.className = 'chatbot-icon';
        this.chatbotIcon.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        `;
        document.body.appendChild(this.chatbotIcon);
    }

    // Crea la finestra di chat
    createChatWindow() {
        this.chatWindow = document.createElement('div');
        this.chatWindow.className = 'chatbot-window';
        this.chatWindow.innerHTML = `
            <div class="chatbot-header">
                <div class="chatbot-title">
                    <img src="/static/images/logo-small.png" alt="EnergyWise" class="chatbot-logo">
                    <span>EnergyBot</span>
                </div>
                <button class="chatbot-close">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="chatbot-messages"></div>
            <div class="chatbot-upload-preview"></div>
            <div class="chatbot-input">
                <button class="chatbot-upload">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                </button>
                <input type="file" class="chatbot-file-input" accept=".pdf,.jpg,.jpeg,.png" style="display: none;">
                <input type="text" class="chatbot-message-input" placeholder="Scrivi un messaggio...">
                <button class="chatbot-send">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        `;
        document.body.appendChild(this.chatWindow);

        // Salva i riferimenti agli elementi
        this.messageContainer = this.chatWindow.querySelector('.chatbot-messages');
        this.messageInput = this.chatWindow.querySelector('.chatbot-message-input');
        this.sendButton = this.chatWindow.querySelector('.chatbot-send');
        this.uploadButton = this.chatWindow.querySelector('.chatbot-upload');
        this.closeButton = this.chatWindow.querySelector('.chatbot-close');
        this.fileInput = this.chatWindow.querySelector('.chatbot-file-input');
        this.uploadPreview = this.chatWindow.querySelector('.chatbot-upload-preview');
    }

    // Configura gli event listener
    setupEventListeners() {
        // Apri/chiudi chatbot
        this.chatbotIcon.addEventListener('click', () => this.toggleChatWindow());
        this.closeButton.addEventListener('click', () => this.toggleChatWindow());

        // Invia messaggio
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Upload file
        this.uploadButton.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    // Apri/chiudi la finestra di chat
    toggleChatWindow() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.chatWindow.classList.add('open');
            this.chatbotIcon.classList.add('hidden');
            
            // Mostra il messaggio di benvenuto se è la prima apertura
            if (this.messageContainer.children.length === 0) {
                this.addBotMessage("Ciao! Sono EnergyBot, l'assistente virtuale di EnergyWise. Come posso aiutarti oggi? Posso fornirti informazioni sui nostri prodotti e offerte, rispondere a domande sulla tua bolletta o darti consigli per risparmiare energia.");
            }
        } else {
            this.chatWindow.classList.remove('open');
            this.chatbotIcon.classList.remove('hidden');
        }
    }

    // Invia un messaggio
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (message === '' || this.isProcessing) return;

        // Aggiungi il messaggio dell'utente
        this.addUserMessage(message);
        this.messageInput.value = '';

        // Mostra l'indicatore di digitazione
        this.addTypingIndicator();
        this.isProcessing = true;

        // Invia la richiesta al server
        fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: this.userId,
                message: message
            })
        })
        .then(response => response.json())
        .then(data => {
            // Rimuovi l'indicatore di digitazione
            this.removeTypingIndicator();
            this.isProcessing = false;

            // Aggiungi la risposta del bot
            this.addBotMessage(data.response);
        })
        .catch(error => {
            console.error('Errore:', error);
            this.removeTypingIndicator();
            this.isProcessing = false;
            this.addBotMessage("Mi dispiace, si è verificato un errore. Riprova più tardi o contatta il nostro servizio clienti al numero 800.123.456.");
        });
    }

    // Gestisci l'upload di un file
    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Verifica il tipo di file
        const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
        if (!validTypes.includes(file.type)) {
            this.addBotMessage("Mi dispiace, puoi caricare solo file PDF o immagini (JPG, PNG).");
            return;
        }

        // Mostra l'anteprima del file
        this.uploadPreview.innerHTML = `
            <div class="upload-preview-container">
                <span class="upload-filename">${file.name}</span>
                <button class="upload-remove">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;

        // Aggiungi event listener per rimuovere il file
        const removeButton = this.uploadPreview.querySelector('.upload-remove');
        removeButton.addEventListener('click', () => {
            this.uploadPreview.innerHTML = '';
            this.fileInput.value = '';
        });

        // Aggiungi messaggio utente
        this.addUserMessage(`Ho caricato la mia bolletta: ${file.name}`);

        // Mostra l'indicatore di digitazione
        this.addTypingIndicator();
        this.isProcessing = true;

        // Carica il file
        const formData = new FormData();
        formData.append('user_id', this.userId);
        formData.append('file', file);

        fetch('/api/chatbot/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Rimuovi l'indicatore di digitazione
            this.removeTypingIndicator();
            this.isProcessing = false;

            // Aggiungi la risposta del bot
            this.addBotMessage(data.response);

            // Pulisci l'anteprima
            this.uploadPreview.innerHTML = '';
            this.fileInput.value = '';
        })
        .catch(error => {
            console.error('Errore:', error);
            this.removeTypingIndicator();
            this.isProcessing = false;
            this.addBotMessage("Mi dispiace, si è verificato un errore durante l'elaborazione della bolletta. Riprova più tardi o contatta il nostro servizio clienti al numero 800.123.456.");
            
            // Pulisci l'anteprima
            this.uploadPreview.innerHTML = '';
            this.fileInput.value = '';
        });
    }

    // Aggiungi un messaggio dell'utente
    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chatbot-message user-message';
        messageElement.innerHTML = `
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;
        this.messageContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    // Aggiungi un messaggio del bot
    addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chatbot-message bot-message';
        
        // Usa un'immagine di fallback se l'avatar del bot non è disponibile
        const avatarSrc = '/static/images/bot-avatar.png';
        const avatarFallback = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM0Q0FGNTAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTVhMiAyIDAgMCAxLTIgMkg3bC00IDRWNWEyIDIgMCAwIDEgMi0yaDE0YTIgMiAwIDAgMSAyIDJ6Ij48L3BhdGg+PC9zdmc+';
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <img src="${avatarSrc}" alt="EnergyBot" onerror="this.onerror=null;this.src='${avatarFallback}';">
            </div>
            <div class="message-content">${this.formatMessage(message)}</div>
        `;
        this.messageContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    // Aggiungi l'indicatore di digitazione
    addTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'chatbot-message bot-message typing';
        typingElement.innerHTML = `
            <div class="message-avatar">
                <img src="/static/images/bot-avatar.png" alt="EnergyBot">
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.messageContainer.appendChild(typingElement);
        this.scrollToBottom();
    }

    // Rimuovi l'indicatore di digitazione
    removeTypingIndicator() {
        const typingElement = this.messageContainer.querySelector('.typing');
        if (typingElement) {
            typingElement.remove();
        }
    }

    // Formatta il messaggio (supporta markdown semplice)
    formatMessage(message) {
        // Sostituisci i link
        message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Sostituisci gli asterischi con grassetto
        message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Sostituisci gli underscore con corsivo
        message = message.replace(/\_(.*?)\_/g, '<em>$1</em>');
        
        // Sostituisci le newline con <br>
        message = message.replace(/\n/g, '<br>');
        
        return message;
    }

    // Escape HTML per prevenire XSS
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Scorri fino in fondo
    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }
}

// Stili CSS per il chatbot
function addChatbotStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .chatbot-icon {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background-color: #4CAF50;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            transition: all 0.3s ease;
            color: white;
        }
        
        .chatbot-icon:hover {
            transform: scale(1.05);
        }
        
        .chatbot-icon.hidden {
            display: none;
        }
        
        .chatbot-window {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            z-index: 1000;
            overflow: hidden;
            opacity: 0;
            pointer-events: none;
            transform: translateY(20px);
            transition: all 0.3s ease;
        }
        
        .chatbot-window.open {
            opacity: 1;
            pointer-events: all;
            transform: translateY(0);
        }
        
        .chatbot-header {
            background-color: #4CAF50;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chatbot-title {
            display: flex;
            align-items: center;
            font-weight: bold;
            font-size: 16px;
        }
        
        .chatbot-logo {
            height: 24px;
            margin-right: 10px;
        }
        
        .chatbot-close {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 0;
        }
        
        .chatbot-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .chatbot-message {
            margin-bottom: 15px;
            display: flex;
            max-width: 80%;
        }
        
        .user-message {
            align-self: flex-end;
            flex-direction: row-reverse;
        }
        
        .bot-message {
            align-self: flex-start;
        }
        
        .message-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            overflow: hidden;
            margin: 0 8px;
        }
        
        .message-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .message-content {
            padding: 10px 15px;
            border-radius: 18px;
            background-color: #f1f1f1;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            line-height: 1.4;
        }
        
        .user-message .message-content {
            background-color: #4CAF50;
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message .message-content {
            background-color: #f1f1f1;
            color: #333;
            border-bottom-left-radius: 5px;
        }
        
        .typing-indicator {
            display: flex;
            align-items: center;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background-color: #888;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out both;
        }
        
        .typing-indicator span:nth-child(1) {
            animation-delay: 0s;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0% { transform: scale(1); }
            50% { transform: scale(1.5); }
            100% { transform: scale(1); }
        }
        
        .chatbot-upload-preview {
            padding: 0 15px;
        }
        
        .upload-preview-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #f1f1f1;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .upload-filename {
            font-size: 14px;
            color: #333;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 250px;
        }
        
        .upload-remove {
            background: none;
            border: none;
            color: #888;
            cursor: pointer;
            padding: 0;
        }
        
        .chatbot-input {
            display: flex;
            align-items: center;
            padding: 15px;
            border-top: 1px solid #eee;
        }
        
        .chatbot-message-input {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 10px 15px;
            margin: 0 10px;
            outline: none;
        }
        
        .chatbot-upload, .chatbot-send {
            background: none;
            border: none;
            color: #4CAF50;
            cursor: pointer;
            padding: 0;
        }
        
        @media (max-width: 480px) {
            .chatbot-window {
                width: 100%;
                height: 100%;
                bottom: 0;
                right: 0;
                border-radius: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Inizializza il chatbot quando il DOM è caricato
document.addEventListener('DOMContentLoaded', () => {
    addChatbotStyles();
    window.energyWiseChatbot = new EnergyWiseChatbot();
});
