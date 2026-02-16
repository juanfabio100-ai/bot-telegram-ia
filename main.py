import os
import telebot
from groq import Groq

# =========================
# CONFIGURAÇÕES
# =========================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# =========================
# FUNÇÃO IA (GROQ)
# =========================

def gerar_resposta(texto_usuario):
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": "Você é um especialista em vendas, persuasivo, direto e estratégico."
            },
            {
                "role": "user",
                "content": texto_usuario
            }
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content

# =========================
# COMANDO START
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 Bem-vindo! Me diga o que você precisa.")

# =========================
# RESPONDER MENSAGENS
# =========================

@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        resposta = gerar_resposta(message.text)
        bot.reply_to(message, resposta)
    except Exception as e:
        print("Erro:", e)
        bot.reply_to(message, "⚠️ Erro interno. Tente novamente.")

# =========================
# INICIAR BOT
# =========================

print("Bot rodando...")
bot.infinity_polling()
