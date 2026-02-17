import os
import time
import psycopg2
import telebot
import traceback

# =========================
# CONFIGURAÇÕES
# =========================
BOT_TOKEN = os.getenv("8364643403:AAHyeBI0rJZGANfXYn6KAJI-NfVgM4f1L38")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN não encontrado")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL não encontrado")

bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# CONEXÃO COM BANCO
# =========================
try:
    print("🔍 Conectando ao banco...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens (
        id SERIAL PRIMARY KEY,
        chat_id TEXT,
        username TEXT,
        mensagem TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    print("✅ Banco conectado e tabela pronta")

except Exception as e:
    print("❌ ERRO AO CONECTAR NO BANCO")
    print(e)
    traceback.print_exc()
    raise e

# =========================
# FUNÇÃO PARA SALVAR
# =========================
def salvar_mensagem(chat_id, username, texto):
    try:
        cursor.execute(
            "INSERT INTO mensagens (chat_id, username, mensagem) VALUES (%s, %s, %s)",
            (chat_id, username, texto)
        )
        conn.commit()
        print("💾 Mensagem salva no banco")
    except Exception as e:
        print("❌ ERRO AO SALVAR NO BANCO")
        print(e)
        traceback.print_exc()

# =========================
# HANDLERS
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🔥 Bem-vindo! Me diga o que você precisa."
    )

@bot.message_handler(func=lambda m: True)
def conversa(message):
    try:
        chat_id = message.chat.id
        username = message.from_user.username
        texto = message.text

        print(f"📩 Mensagem recebida: {texto}")

        salvar_mensagem(chat_id, username, texto)

        bot.send_message(
            chat_id,
            f"🧠 Recebi sua mensagem:\n\n{texto}"
        )

    except Exception as e:
        print("❌ ERRO NO HANDLER")
        print(e)
        traceback.print_exc()

        bot.send_message(
            message.chat.id,
            f"⚠️ Erro real:\n{e}"
        )

# =========================
# START DO BOT
# =========================
print("🚀 Bot iniciado com sucesso")

while True:
    try:
        bot.polling(none_stop=True, interval=3, timeout=20)
    except Exception as e:
        print("♻️ Erro no polling, reiniciando...")
        print(e)
        time.sleep(5)
