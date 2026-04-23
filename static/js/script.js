class GroqChatApp {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.messagesWrapper = document.getElementById('messagesWrapper');
        this.modelSelect = document.getElementById('modelSelect');
        this.temperature = document.getElementById('temperature');
        this.tempValue = document.getElementById('tempValue');
        this.streamToggle = document.getElementById('streamToggle');
        this.isStreaming = true;
        
        this.init();
    }
    
    init() {
        // Обработчики событий
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => this.handleInput(e));
        this.temperature.addEventListener('input', () => {
            this.tempValue.textContent = this.temperature.value;
        });
        this.streamToggle.addEventListener('click', () => this.toggleStream());
        document.getElementById('clearChat').addEventListener('click', () => this.clearChat());
        
        // Автофокус
        this.messageInput.focus();
        
        // Частицы
        this.initParticles();
    }
    
    handleInput(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Добавляем сообщение пользователя
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Показываем индикатор
        this.showTyping(true);
        
        const model = this.modelSelect.value;
        const temp = parseFloat(this.temperature.value);
        
        try {
            if (this.isStreaming) {
                await this.streamResponse(message, model);
            } else {
                await this.normalResponse(message, model, temp);
            }
        } catch (error) {
            this.addMessage(`Ошибка: ${error.message}`, 'bot');
        } finally {
            this.showTyping(false);
        }
    }
    
    async streamResponse(message, model) {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, model })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botMessage = this.addMessage('', 'bot');
        let fullText = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    if (data.chunk) {
                        fullText += data.chunk;
                        botMessage.textContent = fullText;
                        this.scrollToBottom();
                    }
                }
            }
        }
    }
    
    async normalResponse(message, model, temp) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, model, temperature: temp })
        });
        
        const data = await response.json();
        this.addMessage(data.response, 'bot');
    }
    
    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = type === 'bot' ? '⚡' : '👤';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <span>${avatar}</span>
            </div>
            <div class="message-content">
                <div class="message-bubble glass-bubble">
                    ${text}
                </div>
            </div>
        `;
        
        this.messagesWrapper.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv.querySelector('.message-bubble');
    }
    
    showTyping(show) {
        const indicator = document.getElementById('typingIndicator');
        indicator.style.display = show ? 'flex' : 'none';
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesWrapper.scrollTop = this.messagesWrapper.scrollHeight;
        }, 100);
    }
    
    toggleStream() {
        this.isStreaming = !this.isStreaming;
        this.streamToggle.classList.toggle('active');
    }
    
    async clearChat() {
        await fetch('/api/clear', { method: 'POST' });
        this.messagesWrapper.innerHTML = '';
        location.reload();
    }
    
    initParticles() {
        const canvas = document.getElementById('particleCanvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const particles = [];
        for (let i = 0; i < 100; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 2 + 1,
                speedX: Math.random() * 0.5 - 0.25,
                speedY: Math.random() * 0.5 - 0.25
            });
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(p => {
                p.x += p.speedX;
                p.y += p.speedY;
                
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;
                
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(99, 102, 241, 0.3)';
                ctx.fill();
            });
            
            requestAnimationFrame(animate);
        }
        
        animate();
    }
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', () => {
    new GroqChatApp();
});
