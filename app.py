from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Конфигурация Grok API
GROK_API_KEY = "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"  # Замени на свой ключ
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

class GrokAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.conversation_history = []
        
    def chat(self, message, system_prompt=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": "grok-beta",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(GROK_API_URL, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Сохраняем историю
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            return f"Ошибка при запросе к Grok API: {str(e)}"

grok_ai = GrokAI(GROK_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    system_prompt = """Ты - Grok AI помощник, созданный компанией X.AI. 
    Отвечай на русском языке, будь дружелюбным и полезным."""
    
    response = grok_ai.chat(message, system_prompt)
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    grok_ai.conversation_history = []
    return jsonify({'status': 'История очищена'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
