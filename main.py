#!/usr/bin/env python3
"""
MÁQUINA DE VENDAS IA - VERSÃO RAILWAY (Funcional)
"""
import os
import sys
import threading
import sqlite3
import json
from datetime import datetime

# ============================================
# CONFIGURAÇÃO
# ============================================

# Verifica variáveis
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not all([TELEGRAM_TOKEN, GROQ_API_KEY, ADMIN_CHAT_ID]):
    print("❌ ERRO: Configure as variáveis de ambiente no Railway!")
    print("TELEGRAM_TOKEN, GROQ_API_KEY, ADMIN_CHAT_ID")
    sys.exit(1)

# Banco de dados
os.makedirs("data", exist_ok=True)
DB_PATH = "data/maquina_vendas.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            nicho TEXT,
            status TEXT DEFAULT 'criado',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# FUNÇÕES DA IA
# ============================================

import requests

def chamar_groq(mensagem):
    """Chama API Groq"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",  # Modelo mais leve
            "messages": [
                {"role": "system", "content": "Você é uma IA especialista em vendas digitais. Seja direto, estratégico e motivador."},
                {"role": "user", "content": mensagem}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erro na IA: {str(e)[:100]}"

def criar_projeto_db(nome, nicho):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO projetos (nome, nicho, status) VALUES (?, ?, 'ativo')", (nome, nicho))
        conn.commit()
        return f"✅ Projeto '{nome}' criado no nicho '{nicho}'!"
    except:
        return "❌ Erro ao criar projeto"
    finally:
        conn.close()

def listar_projetos_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projetos ORDER BY id DESC")
    projetos = cursor.fetchall()
    conn.close()
    
    if not projetos:
        return "📭 Nenhum projeto ainda."
    
    msg = "📊 SEUS PROJETOS:\n\n"
    for p in projetos:
        msg += f"🆔 {p[0]} | {p[1]} ({p[2]})\n   Status: {p[3]}\n\n"
    return msg

# ============================================
# TELEGRAM BOT (Versão 13.7 - Síncrona)
# ============================================

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

def check_auth(update: Update) -> bool:
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_CHAT_ID:
        update.message.reply_text("⛔ Acesso negado.")
        return False
    return True

def cmd_start(update: Update, context: CallbackContext):
    if not check_auth(update):
        return
    update.message.reply_text(
        "🔥 MÁQUINA DE VENDAS IA\n\n"
        "Comandos:\n"
        "/novo NOME NICHOS - Criar projeto\n"
        "/status - Ver projetos\n"
        "/ajuda - Ajuda completa"
    )

def cmd_novo(update: Update, context: CallbackContext):
    if not check_auth(update):
        return
    
    args = context.args
    if len(args) < 2:
        update.message.reply_text("⚠️ Use: /novo NomeProjeto nicho")
        return
    
    nome, nicho = args[0], args[1]
    resposta = criar_projeto_db(nome, nicho)
    update.message.reply_text(resposta)

def cmd_status(update: Update, context: CallbackContext):
    if not check_auth(update):
        return
    resposta = listar_projetos_db()
    update.message.reply_text(resposta)

def handle_texto(update: Update, context: CallbackContext):
    if not check_auth(update):
        return
    
    texto = update.message.text
    
    # Comandos naturais
    if "criar projeto" in texto.lower():
        partes = texto.split()
        if len(partes) >= 4:
            nome = partes[2]
            nicho = partes[3]
            resposta = criar_projeto_db(nome, nicho)
        else:
            resposta = "⚠️ Formato: criar projeto NOME NICHOS"
    elif "status" in texto.lower():
        resposta = listar_projetos_db()
    else:
        # Usa IA
        resposta = chamar_groq(texto)
    
    update.message.reply_text(resposta[:4000])  # Limite Telegram

def iniciar_telegram():
    print("🤖 Iniciando Bot Telegram...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", cmd_start))
    dispatcher.add_handler(CommandHandler("novo", cmd_novo))
    dispatcher.add_handler(CommandHandler("status", cmd_status))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_texto))
    
    updater.start_polling()
    print("✅ Bot Telegram rodando!")
    updater.idle()

# ============================================
# WEB SERVER (Flask)
# ============================================

from flask import Flask, request, jsonify
from flask_cors import CORS

def iniciar_web():
    print("🌐 Iniciando Web Server...")
    app = Flask(__name__)
    CORS(app)
    
    @app.route("/")
    def home():
        return {
            "status": "online",
            "servico": "Máquina de Vendas IA",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.route("/health")
    def health():
        return {"ok": True}
    
    @app.route("/chat", methods=["POST"])
    def chat():
        dados = request.get_json()
        msg = dados.get("mensagem", "")
        resposta = chamar_groq(msg)
        return jsonify({"resposta": resposta})
    
    porta = int(os.getenv("PORT", 5000))
    print(f"✅ Web na porta {porta}")
    app.run(host="0.0.0.0", port=porta, threaded=True)

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("=" * 40)
    print("🚀 MÁQUINA DE VENDAS IA v2.0")
    print("=" * 40)
    
    # Thread Telegram
    telegram_thread = threading.Thread(target=iniciar_telegram, daemon=True)
    telegram_thread.start()
    
    # Web (main thread)
    iniciar_web()
