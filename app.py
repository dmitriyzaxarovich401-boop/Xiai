from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from groq import Groq
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Конфигурация Groq API
GROQ_API_KEY = "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"  # Замени на свой ключ от console.groq.com
client = Groq(api_key=GROQ_API_KEY)

class GroqAI:
    def __init__(self):
        self.conversation_history = []
        self.available_models = [
            "mixtral-8x7b-32768",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it"
        ]
        
    def chat(self, message, model="llama-3.3-70b-versatile", temperature=0.7):
        messages = [
            {
                "role": "system",
                "content": "Ты - мощный AI ассистент на базе Groq. Отвечай на русском языке, будь креативным и полезным. Используй эмодзи для лучшего восприятия."
            }
        ]
        
        # Добавляем историю последних 10 сообщений для контекста
        messages.extend(self.conversation_history[-20:])
        messages.append({"role": "user", "content": message})
        
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
                top_p=1,
                stream=False
            )
            
            ai_response = completion.choices[0].message.content
            
            # Сохраняем в историю
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return {
                'response': ai_response,
                'model': model,
                'usage': {
                    'prompt_tokens': completion.usage.prompt_tokens,
                    'completion_tokens': completion.usage.completion_tokens,
                    'total_tokens': completion.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {'error': f"🚨 Ошибка Groq API: {str(e)}"}
    
    def stream_chat(self, message, model="llama-3.3-70b-versatile"):
        messages = [
            {"role": "system", "content": "Ты - Groq AI. Отвечай на русском."}
        ]
        messages.extend(self.conversation_history[-20:])
        messages.append({"role": "user", "content": message})
        
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'chunk': content, 'full': full_response})}\n\n"
            
            # Сохраняем в историю
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            yield f"data: {json.dumps({'done': True, 'full': full_response})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

groq_ai = GroqAI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'llama-3.3-70b-versatile')
    temperature = data.get('temperature', 0.7)
    
    if not message:
        return jsonify({'error': 'Введи сообщение 😊'}), 400
    
    result = groq_ai.chat(message, model, temperature)
    return jsonify(result)

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'llama-3.3-70b-versatile')
    
    return Response(
        stream_with_context(groq_ai.stream_chat(message, model)),
        content_type='text/event-stream'
    )

@app.route('/api/models', methods=['GET'])
def get_models():
    return jsonify({
        'models': groq_ai.available_models,
        'current': 'llama-3.3-70b-versatile'
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({'history': groq_ai.conversation_history[-50:]})

@app.route('/api/clear', methods=['POST'])
def clear_history():
    groq_ai.conversation_history = []
    return jsonify({'status': '🧹 История очищена'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'total_messages': len(groq_ai.conversation_history),
        'models_available': len(groq_ai.available_models),
        'api_status': 'connected'
    })

if __name__ == '__main__':
    print("🚀 Groq AI Server запущен на http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
