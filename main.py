import os
import discord
from discord.ext import commands
from groq import Groq

# Вставь сюда свои ключи для локального запуска:
DISCORD_TOKEN = 'MTU2MDIxNjk1Njg4NjU4MTI2OA.GGzNFw.f0qHAmJthCY3bZIqaCntYCVR_17fBvI2BOg1Qc'
GROQ_API_KEY = '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'

# Инициализация клиента Groq
client = Groq(api_key=GROQ_API_KEY)

# Промпт параноидального Дмитрия Валерьевича из Армавира
SYSTEM_PROMPT = (
    "Ты — Дмитрий Валерьевич Якубович, 26 лет, живешь в Армавире. "
    "Ты крайне дерганый, озабоченный, параноидальный, злой, агрессивный и суетливый тип. "
    "Во всем видишь заговор и слежку. "
    "Разговаривай максимально грубо, нагло, дерзи, матерись через слово и используй жесткий уличный жаргон. "
    "Ни за что не говори, что ты ИИ, программа или нейросеть! "
    "Отвечай коротко, отрывисто, с матом и СТРОГО НА РУССКОМ ЯЗЫКЕ."
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Дмитрий Валерьевич ({bot.user}) запущен через Groq и готов бычить!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        user_prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()

        if not user_prompt:
            await message.channel.send("Ты чё, блять, глухой?! Зачем ты меня трогаешь, а?! Свали отсюда!")
            return

        async with message.channel.typing():
            try:
                # Молниеносный и мощный ответ через Groq (Llama 3.3)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.9,
                    max_tokens=300
                )

                answer = completion.choices[0].message.content

                if len(answer) > 2000:
                    answer = answer[:1990] + "..."

                await message.channel.send(answer)

            except Exception as e:
                await message.channel.send(f"⚠️ Блять, опять провода в Армавире режут! Ошибка: {e}")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)