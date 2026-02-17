
import os
import requests
from flask import Flask, request
import threading
import time

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("8364643403:AAHyeBI0rJZGANfXYn6KAJI-NfVgM4f1L38")
GROQ_API_KEY = os.getenv("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")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

TELEGRAM_URL = f"https://api.telegram.org/bot{8364643403:AAHyeBI0rJZGANfXYn6KAJI-NfVgM4f1L38}/sendMessage"

# 🔥 Função IA estratégica de vendas
def perguntar_groq(mensagem_usuario):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {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}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "system",
                "content": """
Você é uma IA especialista em vendas digitais.
Seu objetivo é:
- Criar conexão emocional
- Gerar curiosidade
- Identificar dor do cliente
- Direcionar para compra
- Usar linguagem persuasiva
Nunca responda de forma neutra.
Sempre conduza para conversão.
"""
            },
            {"role": "user", "content": mensagem_usuario}
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        resposta = response.json()
        return resposta["choices"][0]["message"]["content"]
    else:
        return "Erro ao conectar com a IA."

# 🔥 Mensagem automática de ativação
def enviar_mensagem_ativacao():
    time.sleep(5)  # espera o servidor subir

    requests.post(TELEGRAM_URL, json={
        "chat_id": ADMIN_CHAT_ID,
        "text": "🔥 SUA MÁQUINA DE VENDAS ESTÁ ATIVA E RODANDO 24H 🚀"
    })

# 🔥 Webhook Telegram
@app.route(f"/{8364643403:AAHyeBI0rJZGANfXYn6KAJI-NfVgM4f1L38}", methods=["POST"])
def receber_mensagem():
    dados = request.get_json()

    if "message" in dados:
        chat_id = dados["message"]["chat"]["id"]
        texto_usuario = dados["message"].get("text")

        if texto_usuario:
            resposta_ia = perguntar_groq(texto_usuario)

            requests.post(TELEGRAM_URL, json={
                "chat_id": chat_id,
                "text": resposta_ia
            })

    return "ok"

# 🔥 Rota principal
@app.route("/")
def home():
    return "Máquina de vendas rodando!"

if __name__ == "__main__":
    threading.Thread(target=enviar_mensagem_ativacao).start()
    app.run(host="0.0.0.0", port=5000)
