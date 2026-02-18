#!/usr/bin/env python3
"""
MÁQUINA DE VENDAS IA v2.0
Ponto de entrada único - Roda Web + Telegram simultaneamente
"""
import os
import sys
import asyncio
import threading
from datetime import datetime

# Adiciona pasta raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================

def check_env():
    """Verifica se todas as variáveis obrigatórias existem"""
    required = [
        'TELEGRAM_TOKEN',
        'GROQ_API_KEY', 
        'ADMIN_CHAT_ID'
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print("❌ ERRO: Variáveis de ambiente faltando:")
        for var in missing:
            print(f"   - {var}")
        print("\nCrie um arquivo .env com:")
        print("TELEGRAM_TOKEN=seu_token_aqui")
        print("GROQ_API_KEY=sua_chave_aqui")
        print("ADMIN_CHAT_ID=seu_id_telegram")
        sys.exit(1)
    
    print("✅ Variáveis de ambiente OK")

# ============================================
# INICIALIZAÇÃO SIMPLIFICADA
# ============================================

def iniciar_telegram():
    """Inicia bot do Telegram em thread separada"""
    print("🤖 Iniciando Bot Telegram...")
    
    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        
        TOKEN = os.getenv("TELEGRAM_TOKEN")
        ADMIN_ID = os.getenv("ADMIN_CHAT_ID")
        
        # Verifica se é admin
        async def check_auth(update: Update) -> bool:
            user_id = str(update.effective_user.id)
            if user_id != ADMIN_ID:
                await update.message.reply_text("⛔ Acesso negado.")
                return False
            return True
        
        # Comandos
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await check_auth(update):
                return
            
            await update.message.reply_text(
                f"""🔥 **MÁQUINA DE VENDAS IA**

Olá! Sou sua CEO digital.

**Comandos rápidos:**
/novo [nome] [nicho] - Criar projeto
/status - Ver projetos
/relatorio - Resultados

Ou converse naturalmente!"""
            )
        
        async def novo_projeto(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await check_auth(update):
                return
            
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "⚠️ Use: /novo NomeProjeto nicho\n"
                    "Ex: /novo Verao2024 emagrecimento"
                )
                return
            
            nome = args[0]
            nicho = args[1]
            
            # Processa via cérebro
            from core.brain import processar_mensagem_simples
            resposta = await processar_mensagem_simples(
                f"criar projeto {nome} no nicho {nicho}",
                str(update.effective_user.id)
            )
            
            await update.message.reply_text(resposta, parse_mode="Markdown")
        
        async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await check_auth(update):
                return
            
            from core.brain import processar_mensagem_simples
            resposta = await processar_mensagem_simples("status geral", str(update.effective_user.id))
            await update.message.reply_text(resposta, parse_mode="Markdown")
        
        async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await check_auth(update):
                return
            
            texto = update.message.text
            user_id = str(update.effective_user.id)
            
            print(f"💬 Telegram: {texto[:50]}...")
            
            from core.brain import processar_mensagem_simples
            resposta = await processar_mensagem_simples(texto, user_id)
            
            # Divide se for muito longo
            if len(resposta) > 4000:
                partes = [resposta[i:i+4000] for i in range(0, len(resposta), 4000)]
                for parte in partes:
                    await update.message.reply_text(parte, parse_mode="Markdown")
            else:
                await update.message.reply_text(resposta, parse_mode="Markdown")
        
        # Cria aplicação
        application = Application.builder().token(TOKEN).build()
        
        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("novo", novo_projeto))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Roda em modo polling (mais simples que webhook)
        print("✅ Bot Telegram rodando!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Erro no Telegram: {e}")
        import traceback
        traceback.print_exc()

def iniciar_web():
    """Inicia servidor web em thread separada"""
    print("🌐 Iniciando Servidor Web...")
    
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        @app.route("/")
        def home():
            return {
                "status": "online",
                "servico": "Máquina de Vendas IA",
                "versao": "2.0",
                "timestamp": datetime.now().isoformat()
            }
        
        @app.route("/health")
        def health():
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
        
        @app.route("/webhook/telegram", methods=["POST"])
        def webhook():
            """Endpoint para webhook do Telegram (se usar)"""
            return {"ok": True}
        
        @app.route("/chat", methods=["POST"])
        def chat():
            """API para conversação via web"""
            dados = request.get_json()
            mensagem = dados.get("mensagem", "")
            user_id = dados.get("user_id", "web_user")
            
            # Processa de forma síncrona
            import asyncio
            from core.brain import processar_mensagem_simples
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            resposta = loop.run_until_complete(
                processar_mensagem_simples(mensagem, user_id)
            )
            loop.close()
            
            return jsonify({
                "resposta": resposta,
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route("/projetos", methods=["GET"])
        def listar_projetos():
            """Lista projetos"""
            import asyncio
            from core.brain import processar_mensagem_simples
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            resposta = loop.run_until_complete(
                processar_mensagem_simples("status geral", "web_user")
            )
            loop.close()
            
            return jsonify({"data": resposta})
        
        # Pega porta do ambiente (Railway/Render definem automaticamente)
        porta = int(os.getenv("PORT", 5000))
        
        print(f"✅ Web server rodando na porta {porta}!")
        # Roda sem debug em produção
        app.run(host="0.0.0.0", port=porta, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Erro na Web: {e}")
        import traceback
        traceback.print_exc()

# ============================================
# CÉREBRO SIMPLIFICADO (Tudo em um arquivo)
# ============================================

# Cria estrutura mínima do cérebro se não existir
def criar_estrutura():
    """Cria pastas e arquivos necessários"""
    pastas = ['config', 'core', 'core/plugins', 'interfaces', 'interfaces/telegram', 'interfaces/web', 'models', 'utils', 'data', 'logs']
    for pasta in pastas:
        os.makedirs(pasta, exist_ok=True)
        # Cria __init__.py
        init_file = os.path.join(pasta, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('')
    
    print("✅ Estrutura de pastas criada")

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 MÁQUINA DE VENDAS IA v2.0")
    print("=" * 50)
    
    # 1. Verifica ambiente
    check_env()
    
    # 2. Cria estrutura
    criar_estrutura()
    
    # 3. Importa e inicializa cérebro
    print("🧠 Inicializando Cérebro...")
    try:
        from core.brain import inicializar_cerebro
        inicializar_cerebro()
        print("✅ Cérebro pronto!")
    except Exception as e:
        print(f"⚠️  Cérebro com erro (não crítico): {e}")
    
    # 4. Inicia serviços em paralelo
    print("\n🔥 Iniciando serviços...")
    
    # Thread do Telegram
    telegram_thread = threading.Thread(target=iniciar_telegram, daemon=True)
    telegram_thread.start()
    
    # Thread da Web (main thread)
    print("💡 Pressione Ctrl+C para parar\n")
    try:
        iniciar_web()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando...")
        sys.exit(0)
