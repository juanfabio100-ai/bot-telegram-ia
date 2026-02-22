
#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# ============================================
# CONFIG
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not all([TELEGRAM_TOKEN, GROQ_API_KEY, ADMIN_CHAT_ID]):
    print("❌ Configure TELEGRAM_TOKEN, GROQ_API_KEY e ADMIN_CHAT_ID no Railway")
    sys.exit(1)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ============================================
# IA (GROQ)
# ============================================

def chamar_ia(mensagem):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "Você é uma IA estratégica focada em vendas digitais."},
                {"role": "user", "content": mensagem}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }

        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Erro IA: {str(e)[:100]}"

# ============================================
# TELEGRAM
# ============================================

def enviar_mensagem(chat_id, texto):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": texto[:4000]}
    )

# ============================================
# FLASK APP
# ============================================

app = Flask(__name__)

@app.route("/")
def home():
    return {
        "status": "online",
        "servico": "Máquina de Vendas IA",
        "timestamp": datetime.now().isoformat()
    }

# 🔥 WEBHOOK TELEGRAM (SEM POLLING)
@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.json
    
    if "message" in dados:
        chat_id = str(dados["message"]["chat"]["id"])
        texto = dados["message"].get("text", "")

        if chat_id != ADMIN_CHAT_ID:
            enviar_mensagem(chat_id, "⛔ Acesso negado.")
            return "ok"

        resposta = chamar_ia(texto)
        enviar_mensagem(chat_id, resposta)

    return "ok"

# 🔥 ENDPOINT DO SITE (PAINEL)
@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json()
    msg = dados.get("mensagem", "")
    resposta = chamar_ia(msg)
    return jsonify({"resposta": resposta})

# ============================================
# SET WEBHOOK AUTOMÁTICO
# ============================================

def configurar_webhook():
    url_publica = os.getenv("RAILWAY_STATIC_URL")
    if not url_publica:
        print("⚠️ Defina RAILWAY_STATIC_URL no Railway")
        return
    
    webhook_url = f"https://{url_publica}/webhook"
    requests.get(f"{TELEGRAM_API}/setWebhook?url={webhook_url}")
    print("✅ Webhook configurado:", webhook_url)

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("🚀 MÁQUINA DE VENDAS IA (WEBHOOK MODE)")
    configurar_webhook()
    
    PORT = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
