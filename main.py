import telebot
import openai
import os

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_KEY

@bot.message_handler(func=lambda message: True)
def reply(message):
    user_text = message.text

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é uma IA estratégica, direta e inteligente."},
            {"role": "user", "content": user_text}
        ]
    )

    bot.reply_to(message, response.choices[0].message["content"])

print("Bot rodando...")
bot.infinity_polling()
