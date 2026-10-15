import os
import discord
from discord.ext import commands
import json
import urllib.request
from flask import Flask
from threading import Thread

# --- Микро-сервер для удержания бота в сети 24/7 на Render ---
app = Flask('')

@app.route('/')
def home():
    return "Бот работает 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# -------------------------------------------------------------

# Токен берется из переменных окружения (на Render) или подставляется локально
DISCORD_TOKEN = os.getenv('MTU2MDIxNjk1Njg4NjU4MTI2OA.GqvVWa.sBjnDHRe8fnL20R2e8KNHnd8CWRpVMPhVjclOE')

# Системный промпт (характер бота)
SYSTEM_PROMPT = (
    "Ты — подозрительный, озабоченный, гиперактивный и крайне странный тип. "
    "Ты во всем видишь слежку, заговор, суетишься, шепчешь, постоянно озираешься "
    "и заикаешься от нервов. Ни в коем случае НЕ отвечай как обычная нейросеть или ИИ! "
    "Отвечай только от лица этого дерганого и параноидального человека."
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен и держит оборону!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        user_prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()

        if not user_prompt:
            await message.channel.send("Тс-с-с... ты зачем меня трогаешь?! Что тебе нужно?! Говори тихо...")
            return

        async with message.channel.typing():
            try:
                payload = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "model": "openai",
                    "jsonMode": False
                }
                
                data = json.dumps(payload).encode('utf-8')
                
                req = urllib.request.Request(
                    'https://text.pollinations.ai/',
                    data=data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'Mozilla/5.0'
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(req) as response:
                    answer = response.read().decode('utf-8')

                if len(answer) > 2000:
                    answer = answer[:1990] + "..."

                await message.channel.send(answer)

            except Exception as e:
                await message.channel.send(f"⚠️ Ч-что-то сломалось... Они перерезали провода?! Ошибка: {e}")

    await bot.process_commands(message)

@bot.command(name='stop')
@commands.is_owner()
async def stop(ctx):
    await ctx.send("Они близко... я ухожу в подполье!")
    await bot.close()

if __name__ == "__main__":
    # Запускаем веб-сервер в фоне для Render и стартуем бота
    keep_alive()
    bot.run(DISCORD_TOKEN)