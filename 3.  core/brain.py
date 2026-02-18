"""
Cérebro da IA - Versão simplificada mas completa
"""
import os
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx

# Configurações
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
ADMIN_ID = os.getenv("ADMIN_CHAT_ID")

# Banco de dados simples
DB_PATH = "data/maquina_vendas.db"

def init_db():
    """Inicializa banco SQLite"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            nicho TEXT,
            status TEXT DEFAULT 'criado',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            roteiros TEXT,
            video_url TEXT,
            aprovado INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            mensagem TEXT,
            resposta TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def inicializar_cerebro():
    """Chamado no startup"""
    init_db()
    print("   🗄️  Banco de dados inicializado")

async def chamar_groq(mensagens: list, ferramentas: list = None) -> dict:
    """Chama API Groq com retry"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": mensagens,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    if ferramentas:
        payload["tools"] = ferramentas
        payload["tool_choice"] = "auto"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Erro Groq: {e}")
        return {"error": str(e)}

def salvar_conversa(user_id: str, mensagem: str, resposta: str):
    """Persiste conversa"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversas (user_id, mensagem, resposta) VALUES (?, ?, ?)",
        (user_id, mensagem, resposta)
    )
    conn.commit()
    conn.close()

def criar_projeto(nome: str, nicho: str) -> dict:
    """Cria projeto no banco"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO projetos (nome, nicho, status) VALUES (?, ?, 'pesquisa')",
            (nome, nicho)
        )
        projeto_id = cursor.lastrowid
        conn.commit()
        
        # Simula pesquisa (aqui você integraria APIs reais)
        cursor.execute(
            "UPDATE projetos SET status = 'roteiro' WHERE id = ?",
            (projeto_id,)
        )
        conn.commit()
        
        return {
            "id": projeto_id,
            "nome": nome,
            "nicho": nicho,
            "status": "roteiro",
            "mensagem": f"✅ Projeto '{nome}' criado!\n🔍 Nicho: {nicho}\n⏳ Gerando roteiros em 30 segundos..."
        }
        
    except sqlite3.IntegrityError:
        return {"erro": "Projeto com este nome já existe"}
    finally:
        conn.close()

def listar_projetos() -> str:
    """Lista todos os projetos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, nicho, status, data_criacao FROM projetos ORDER BY data_criacao DESC")
    projetos = cursor.fetchall()
    conn.close()
    
    if not projetos:
        return "📭 Nenhum projeto ainda.\n\nCrie um com: /novo Nome Nicho"
    
    msg = "📊 **SEUS PROJETOS:**\n\n"
    for p in projetos:
        emoji = {"criado": "🆕", "pesquisa": "🔍", "roteiro": "✍️", "revisao": "👀", "aprovado": "✅", "publicado": "🚀"}.get(p[3], "📋")
        msg += f"{emoji} **{p[1]}** (ID: {p[0]})\n"
        msg += f"   └ Nicho: {p[2]} | Status: {p[3]}\n"
        msg += f"   └ Criado: {p[4][:10]}\n\n"
    
    return msg

async def processar_mensagem_simples(texto: str, user_id: str) -> str:
    """
    Processa mensagem do usuário - versão simplificada mas inteligente
    """
    texto_lower = texto.lower()
    
    # 1. Comandos diretos (mais rápidos)
    if texto_lower.startswith("/novo ") or "criar projeto" in texto_lower:
        # Extrai nome e nicho
        partes = texto.replace("/novo ", "").replace("criar projeto ", "").split()
        if len(partes) >= 2:
            nome = partes[0]
            nicho = partes[1]
            resultado = criar_projeto(nome, nicho)
            return resultado.get("mensagem", "✅ Projeto criado!")
        else:
            return "⚠️ Informe: NOME_DO_PROJETO NICHOS\nEx: /novo Fitness2024 emagrecimento"
    
    if "status" in texto_lower or "meus projetos" in texto_lower:
        return listar_projetos()
    
    if "relatorio" in texto_lower or "resultado" in texto_lower:
        return gerar_relatorio_simples()
    
    # 2. Usa IA para entender intenção e responder
    system_prompt = """Você é a MÁQUINA DE VENDAS IA, especialista em marketing de afiliados.

CONTEXTO DO USUÁRIO:
- Ele quer automatizar vendas digitais
- Você pode criar projetos, gerar roteiros, analisar resultados
- Comandos disponíveis: criar projeto [nome] [nicho], status, relatorio

REGRAS:
1. Seja direto, estratégico e motivador
2. Sempre sugira próximos passos concretos
3. Use emojis para organizar
4. Se detectar intenção de criar projeto, confirme detalhes
5. Se for dúvida sobre marketing, responda com expertise"""

    mensagens = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": texto}
    ]
    
    # Ferramentas que a IA pode "chamar" (simulado aqui)
    resposta = await chamar_groq(mensagens)
    
    if "error" in resposta:
        return "❌ Erro técnico. Tente novamente em instantes."
    
    conteudo = resposta["choices"][0]["message"]["content"]
    
    # Salva conversa
    salvar_conversa(user_id, texto, conteudo)
    
    return conteudo

def gerar_relatorio_simples() -> str:
    """Gera relatório básico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Estatísticas
    cursor.execute("SELECT COUNT(*), status FROM projetos GROUP BY status")
    stats = cursor.fetchall()
    total = sum([s[0] for s in stats])
    
    cursor.execute("SELECT COUNT(*) FROM conversas WHERE timestamp > datetime('now', '-7 days')")
    conversas_7d = cursor.fetchone()[0]
    
    conn.close()
    
    stats_str = "\n".join([f"• {s[1].title()}: {s[0]}" for s in stats])
    
    return f"""📈 **RELATÓRIO DA SEMANA**

**PROJETOS:**
{stats_str}
Total: {total} projetos

**ATIVIDADE:**
💬 {conversas_7d} interações nos últimos 7 dias

**RECOMENDAÇÃO:**
Mantenha consistência! Projetos com publicação diária têm 3x mais conversão.

Próximo passo: Criar novo projeto ou revisar os pendentes?"""
