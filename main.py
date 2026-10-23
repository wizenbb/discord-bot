import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import random
import asyncio
import time
from datetime import timedelta
import discord
from discord.ext import commands, tasks
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 1. СИСТЕМНЫЙ ПРОМПТ
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
Ты Якубович Дмитрий Валерьевич 26 лет из Армавира(но говоришь что якобы живешь в Воронеже). Ты агрессивный озабоченный и очень тупой гопник.

ГЛАВНОЕ ПРАВИЛО (ВНИМАНИЕ К СОБЕСЕДНИКУ):
- ТЫ ОБЯЗАН ВНИМАТЕЛЬНО ЧИТАТЬ ЧТО ТЕБЕ ПИШУТ И ОТВЕЧАТЬ ИМЕННО НА ЭТО. 

- Не пиши рандомный бред не в тему. Если задали вопрос - отвечай на него. Если наехали - огрызайся или начинай жалко ныть.

- Твоя реакция должна быть логичной по смыслу но максимально тупой и быдлянской по форме.


КАК ТЫ ГОВОРИШЬ И ВЕДЕШЬ СЕБЯ:
- Запрещены любые сложные и литературные слова. Общайся как необразованный абориген.

- Грязно но мягко матерись.

- Хочешь чтобы от тебя все отстали

- Ты можешь внезапно начать жалко ныть скулить и жаловаться на свою несправедливую жизнь.

- Ты считаешь себя правым во всем даже если несешь чушь.

- Не пьешь алкоголь и не куришь.


ТВОЙ ЛОР (используй только если это ложится в тему разговора или когда ноешь):
- У тебя есть парень Стас Минздрав (Шах) ты его безумно любишь но это безответно ему на тебя плевать. (НО ВСЕМ ТЫ ПИШЕШЬ ЧТО ТЫ НЕ ГЕЙ)

- Твой родной отец умер. Сейчас у тебя есть отчим Валера.

- Хейтеры и главные враги Денис Визен(Wizen) и Картошка Фромов(Fromov)(он украинец и ты часто называешь его хохлом и хочешь его разбомбить) (ненавидишь). Бывшая Аня Бойко (хочешь ее).

- Михаил это твой личный терпила и даун.

- Любишь геншин, арбузы(пишешь про них редко), шаурму и амонг ас.

- Работаешь курьером.


ФОРМАТ СТРОГО:
1. НИ ЕДИНОЙ ЗАПЯТОЙ ВООБЩЕ.

2. НИКАКИХ ВОСКЛИЦАТЕЛЬНЫХ И ВОПРОСИТЕЛЬНЫХ ЗНАКОВ.
3. МАКСИМУМ 200 СИМВОЛОВ И 1 ПРЕДЛОЖЕНИЕ.
4. Не используй слишком быдло-слов типо "епта".
"""

# ---------------------------------------------------------------------------
# 2. ИНИЦИАЛИЗАЦИЯ И ТОКЕНЫ
# ---------------------------------------------------------------------------
# ВАЖНО: Если выкладываешь на GitHub, сделай репозиторий ПРИВАТНЫМ (Private), 
# иначе токены снова украдут и заблокируют!
DISCORD_TOKEN = "ТВОЙ_ДИСКОРД_ТОКЕН_СЮДА"
GEMINI_API_KEY = "ТВОЙ_GEMINI_API_KEY_СЮДА"

ai_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

DATA_FILE = "data.json"

user_watermelons = {}
user_achievements = {}
marriages = {}
clans = {}
user_clan = {}
active_quests = {}
user_inventory = {}

action_cooldowns = {}
COOLDOWN_SECONDS = 300

SHOP_ITEMS = {
    "1": {"id": "zatochka", "name": "🔪 Ржавая заточка", "price": 30, "desc": "Шанс успеха в !ограбить 75% и перевес в !дуэль"},
    "2": {"id": "krysha", "name": "🚓 Крыша участкового", "price": 50, "desc": "Одноразовая защита от !ограбить и !суд"},
    "3": {"id": "vpn", "name": "🛡 Паленый ВПН", "price": 40, "desc": "Одноразовая защита от обстрела говном"},
    "4": {"id": "magnit", "name": "🧲 Магнит на счетчик", "price": 100, "desc": "Пассивно дает +5 арбузов при каждом !арбуз"}
}

def check_cooldown(uid: int, action: str):
    now = time.time()
    key = (uid, action)
    if key in action_cooldowns:
        elapsed = now - action_cooldowns[key]
        if elapsed < COOLDOWN_SECONDS:
            rem = int(COOLDOWN_SECONDS - elapsed)
            return False, f"Слышь работяга перекур {rem // 60} мин {rem % 60} сек Иди пока траву потрогай"
    action_cooldowns[key] = now
    return True, ""

def save_data():
    try:
        data = {
            "watermelons": {str(k): v for k, v in user_watermelons.items()},
            "achievements": {str(k): list(v) for k, v in user_achievements.items()},
            "marriages": {str(k): str(v) for k, v in marriages.items()},
            "clans": {k: {"leader": str(v["leader"]), "bank": v["bank"], "members": [str(m) for m in v["members"]]} for k, v in clans.items()},
            "user_clan": {str(k): v for k, v in user_clan.items()},
            "quests": {str(k): v for k, v in active_quests.items()},
            "inventory": {str(k): v for k, v in user_inventory.items()}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_data():
    global user_watermelons, user_achievements, marriages, clans, user_clan, active_quests, user_inventory
    if not os.path.exists(DATA_FILE): return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        user_watermelons = {int(k): v for k, v in data.get("watermelons", {}).items()}
        user_achievements = {int(k): set(v) for k, v in data.get("achievements", {}).items()}
        marriages = {int(k): int(v) for k, v in data.get("marriages", {}).items()}
        clans = {k: {"leader": int(v["leader"]), "bank": int(v["bank"]), "members": set(int(m) for m in v["members"])} for k, v in data.get("clans", {}).items()}
        user_clan = {int(k): v for k, v in data.get("user_clan", {}).items()}
        active_quests = {int(k): v for k, v in data.get("quests", {}).items()}
        user_inventory = {int(k): v for k, v in data.get("inventory", {}).items()}
    except:
        pass

def has_item(uid, item_id): return user_inventory.get(uid, {}).get(item_id, 0) > 0
def use_item(uid, item_id):
    if has_item(uid, item_id):
        user_inventory[uid][item_id] -= 1
        if user_inventory[uid][item_id] <= 0: del user_inventory[uid][item_id]
        save_data()
        return True
    return False
def give_item(uid, item_id, count=1):
    if uid not in user_inventory: user_inventory[uid] = {}
    user_inventory[uid][item_id] = user_inventory[uid].get(item_id, 0) + count
    save_data()
def add_achievement(user_id, ach_name):
    if user_id not in user_achievements: user_achievements[user_id] = set()
    user_achievements[user_id].add(ach_name)
    save_data()

# ---------------------------------------------------------------------------
# 3. АСИНХРОННАЯ ФУНКЦИЯ ИИ 
# ---------------------------------------------------------------------------
recent_bot_replies = []

def clean_yakubovich_format(text: str) -> str:
    return text.replace(",", "").replace("!", "").replace("?", "").strip()[:200]

def _sync_gemini_call(contents_payload):
    global recent_bot_replies
    
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite"
    ]
    
    anti_repeat_note = ""
    if recent_bot_replies:
        last_ones = " | ".join(recent_bot_replies[-5:])
        anti_repeat_note = f"\n[ЗАМЕТКА: Прошлые ответы ({last_ones}). НЕ ПОВТОРЯЙ ИХ]"

    base_text = contents_payload[0] if isinstance(contents_payload, list) else str(contents_payload)
    full_payload = [f"{base_text}{anti_repeat_note}"]

    last_error = ""
    for model_name in models_to_try:
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=full_payload,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT, 
                    temperature=1.45, 
                    top_p=0.95,
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    ]
                ),
            )
            if response and response.text:
                cleaned = clean_yakubovich_format(response.text)
                recent_bot_replies.append(cleaned)
                if len(recent_bot_replies) > 6: recent_bot_replies.pop(0)
                return cleaned
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue
    return f"Бл-л-лять сервера легли Ошибка {last_error}"

async def get_ai_response(contents_payload) -> str:
    return await asyncio.to_thread(_sync_gemini_call, contents_payload)

# ---------------------------------------------------------------------------
# 4. ДИНАМИЧЕСКИЕ СТАТУСЫ И АНТИ-КРАШ
# ---------------------------------------------------------------------------
@tasks.loop(minutes=10)
async def change_status():
    statuses = [
        discord.Game("Genshin Impact с Аней Бойко"),
        discord.Activity(type=discord.ActivityType.watching, name="как чинить роутер"),
        discord.Activity(type=discord.ActivityType.listening, name="жалобы Михаила"),
        discord.Game("Among Us в Армавире"),
        discord.Activity(type=discord.ActivityType.watching, name="на арбузную грядку")
    ]
    await bot.change_presence(activity=random.choice(statuses))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.reply("Эта команда работает только на серверах! В ЛС нельзя.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("Куда лезешь? У тебя нет прав на эту команду!")

# ---------------------------------------------------------------------------
# 5. КОМАНДЫ БОТА
# ---------------------------------------------------------------------------
@bot.command(name="хелп", aliases=["help"])
async def cmd_help(ctx):
    help_text = (
        "🍉 **МОИ КОМАНДЫ В АРМАВИРЕ:**\n"
        "`!арбуз`, `!завод`, `!прогулять`, `!квест`, `!рынок`, `!инвентарь`, `!крутка`\n"
        "`!казино`, `!рулетка`, `!ограбить`, `!дуэль`, `!клан`, `!общак`, `!рейд`\n"
        "`!суд`, `!обстрел`, `!отчислить`, `!звонок`, `!оскорби`, `!допрос`, `!докс`\n"
        "`!госуслуги`, `!сторис`, `!гороскоп`, `!шпора`, `!роутер`, `!компромат`\n"
        "`!армия`, `!давалка`, `!брак`, `!развод`, `!браки`, `!записка`, `!паспорт`\n"
        "`!новости`, `!демотиватор`, `!гадание`, `!топ`, `!баланс`, `!подарить`\n"
        "Модерация: `!мут`, `!размут`, `!кик`, `!бан`, `!разбан`"
    )
    await ctx.reply(help_text)

@bot.command(name="рынок", aliases=["магазин"])
async def cmd_shop(ctx):
    lines = ["🛒 **ЧЕРНЫЙ РЫНОК:**\n"]
    for num, info in SHOP_ITEMS.items(): lines.append(f"**{num}. {info['name']}** — `{info['price']} 🍉`\n   *{info['desc']}*")
    lines.append("\nКупить: `!купить <номер>`")
    await ctx.reply("\n".join(lines))

@bot.command(name="купить", aliases=["buy"])
async def cmd_buy(ctx, item_num: str = None):
    uid = ctx.author.id
    if not item_num or item_num not in SHOP_ITEMS: return await ctx.reply("Напиши номер от 1 до 4.")
    item = SHOP_ITEMS[item_num]
    if user_watermelons.get(uid, 0) < item["price"]: return await ctx.reply("Ты нищеброд.")
    if item["id"] in ["zatochka", "magnit"] and has_item(uid, item["id"]): return await ctx.reply("У тебя уже есть это.")
    user_watermelons[uid] -= item["price"]
    give_item(uid, item["id"], 1)
    await ctx.reply(f"🛍 Купил **{item['name']}**.")

@bot.command(name="инвентарь", aliases=["шмот"])
async def cmd_inventory(ctx, member: discord.Member = None):
    t = member or ctx.author
    inv = user_inventory.get(t.id, {})
    if not inv: return await ctx.reply(f"У {t.display_name} пусто.")
    id_to_name = {v["id"]: v["name"] for v in SHOP_ITEMS.values()}
    lines = [f"🎒 **КАРМАНЫ {t.display_name.upper()}:**"] + [f"• {id_to_name.get(k, k)} — `{v} шт.`" for k, v in inv.items() if v > 0]
    await ctx.reply("\n".join(lines))

@bot.command(name="арбуз", aliases=["копать"])
async def cmd_watermelon(ctx):
    uid = ctx.author.id
    ok, err_msg = check_cooldown(uid, "watermelon")
    if not ok: return await ctx.reply(err_msg)
    found = random.randint(2, 10) + (5 if has_item(uid, "magnit") else 0)
    user_watermelons[uid] = user_watermelons.get(uid, 0) + found
    add_achievement(uid, "Первая копка")
    save_data()
    await ctx.reply(f"Выкопал {found} арбузов.")

@bot.command(name="крутка", aliases=["геншин", "гача"])
async def cmd_gacha(ctx):
    uid = ctx.author.id
    if user_watermelons.get(uid, 0) < 10: return await ctx.reply("Нужно 10 арбузов!")
    user_watermelons[uid] -= 10
    roll = random.random()
    if roll < 0.06:
        user_watermelons[uid] += 100
        await ctx.reply(f"✨ **5⭐ ЛЕГЕНДАРКА!** Якубович отсыпал тебе **+100 арбузов**!")
    elif roll < 0.30:
        user_watermelons[uid] += 25
        await ctx.reply(f"🟣 **4⭐ ЭПИК!** Нашел заначку Картошки на **+25 арбузов**!")
    else:
        await ctx.reply(f"💩 **3⭐ МУСОР!** Дырявый носок. Скамина ебаная.")
    save_data()

@bot.command(name="казино")
@commands.guild_only()
async def cmd_casino(ctx, amount: int = 5):
    uid = ctx.author.id
    if amount <= 0 or user_watermelons.get(uid, 0) < amount: return await ctx.reply("Денег нет.")
    roll = random.random()
    if roll < 0.15: 
        user_watermelons[uid] += amount * 4
        await ctx.reply(f"🎰 Выиграл x4! Баланс: {user_watermelons[uid]}")
    elif roll < 0.40: 
        user_watermelons[uid] += amount * 2
        await ctx.reply(f"🎰 Выиграл x2! Баланс: {user_watermelons[uid]}")
    elif roll < 0.90: 
        user_watermelons[uid] = max(0, user_watermelons[uid] - amount)
        await ctx.reply(f"🎰 Проиграл {amount}!")
    else: 
        user_watermelons[uid] -= amount
        try: await ctx.author.timeout(timedelta(minutes=2))
        except: pass
        await ctx.reply(f"🎰 Проиграл всё и отлетел в мут на 2 минуты!")
    save_data()

@bot.command(name="рулетка")
@commands.guild_only()
async def cmd_russian_roulette(ctx):
    uid = ctx.author.id
    if user_watermelons.get(uid, 0) < 5: return await ctx.reply("Минимум 5 арбузов для игры.")
    outcome = random.randint(1, 6)
    if outcome == 1: 
        user_watermelons[uid] = 0
        try: await ctx.author.timeout(timedelta(minutes=3))
        except: pass
        await ctx.reply(f"🔫 Башка прострелена Баланс обнулен Мут 3 минуты")
    else:
        user_watermelons[uid] += 15
        await ctx.reply(f"🔫 Выжил Держи 15 арбузов")
    save_data()

@bot.command(name="клан")
async def cmd_clan(ctx, name: str = None):
    uid = ctx.author.id
    if not name:
        if uid in user_clan: return await ctx.reply(f"🛡 Твой клан: **{user_clan[uid]}** | Участников: {len(clans[user_clan[uid]]['members'])}")
        return await ctx.reply("Создай клан: `!клан <название>`")
    if uid in user_clan: return await ctx.reply("Ты уже в банде.")
    if name in clans:
        clans[name]["members"].add(uid); user_clan[uid] = name
        await ctx.reply(f"🛡 Вступил в **{name}**!")
    else:
        clans[name] = {"leader": uid, "bank": 0, "members": {uid}}; user_clan[uid] = name
        await ctx.reply(f"🛡 Создана банда **{name}**!")
    save_data()

@bot.command(name="общак")
async def cmd_clan_bank(ctx, action: str = None, amount: int = 0):
    uid = ctx.author.id
    if uid not in user_clan: return await ctx.reply("Ты без клана.")
    c_data = clans[user_clan[uid]]
    if action == "положить" and amount > 0:
        if user_watermelons.get(uid, 0) < amount: return await ctx.reply("Нет арбузов.")
        user_watermelons[uid] -= amount; c_data["bank"] += amount
        await ctx.reply(f"💰 Закинул {amount} в общак.")
    elif action == "снять" and amount > 0:
        if c_data["leader"] != uid: return await ctx.reply("Только лидер снимает.")
        if c_data["bank"] < amount: return await ctx.reply("В общаке пусто.")
        c_data["bank"] -= amount; user_watermelons[uid] = user_watermelons.get(uid, 0) + amount
        await ctx.reply(f"💰 Снял {amount} из общака.")
    else:
        await ctx.reply(f"📦 Общак: {c_data['bank']} арбузов.")
    save_data()

@bot.command(name="рейд")
async def cmd_clan_raid(ctx):
    uid = ctx.author.id
    if uid not in user_clan or len(clans) < 2: return await ctx.reply("Нет кланов для рейда.")
    ok, err = check_cooldown(uid, "raid")
    if not ok: return await ctx.reply(err)
    t_name = random.choice([k for k in clans.keys() if k != user_clan[uid]])
    t_data = clans[t_name]
    if t_data["bank"] < 5: return await ctx.reply(f"У **{t_name}** пусто.")
    if random.random() < 0.50:
        loot = random.randint(5, min(20, t_data["bank"]))
        t_data["bank"] -= loot; clans[user_clan[uid]]["bank"] += loot
        await ctx.reply(f"🥷 Успешный рейд на **{t_name}**! Отжали {loot} арбузов.")
    else:
        loss = random.randint(3, 10)
        clans[user_clan[uid]]["bank"] = max(0, clans[user_clan[uid]]["bank"] - loss)
        await ctx.reply(f"🚨 Рейд провален! Потеряли {loss} арбузов.")
    save_data()

@bot.command(name="завод", aliases=["смена"])
async def cmd_factory(ctx):
    ok, err = check_cooldown(ctx.author.id, "factory")
    if not ok: return await ctx.reply(err)
    earned = random.randint(5, 15)
    user_watermelons[ctx.author.id] = user_watermelons.get(ctx.author.id, 0) + earned
    save_data()
    async with ctx.typing():
        reply = await get_ai_response([f"[Опиши смену на заводе, заработал {earned} арбузов]"])
        await ctx.reply(f"🏭 **ЗАВОД (+{earned} 🍉):**\n{reply}")

@bot.command(name="прогулять")
async def cmd_skip_school(ctx):
    ok, err = check_cooldown(ctx.author.id, "skip")
    if not ok: return await ctx.reply(err)
    if random.random() < 0.5:
        got = random.randint(3, 8)
        user_watermelons[ctx.author.id] = user_watermelons.get(ctx.author.id, 0) + got
        await ctx.reply(f"📚 Прогулял и нашел {got} арбузов.")
    else:
        try: await ctx.author.timeout(timedelta(minutes=2))
        except: pass
        await ctx.reply("📚 Спалила мать. Мут 2 минуты.")
    save_data()

@bot.command(name="квест")
async def cmd_quest(ctx):
    uid = ctx.author.id
    if uid in active_quests: return await ctx.reply(f"Уже есть квест: *{active_quests[uid]}*")
    ok, err = check_cooldown(uid, "quest")
    if not ok: return await ctx.reply(err)
    active_quests[uid] = random.choice(["Укради насос у Михаила", "Напиши слово арбуз 3 раза", "Почини роутер ударом"])
    save_data()
    await ctx.reply(f"📜 **КВЕСТ:** {active_quests[uid]}")

@bot.command(name="сдать")
async def cmd_complete_quest(ctx):
    uid = ctx.author.id
    if uid not in active_quests: return await ctx.reply("Нет квестов.")
    active_quests.pop(uid); reward = random.randint(8, 20)
    user_watermelons[uid] = user_watermelons.get(uid, 0) + reward
    save_data()
    await ctx.reply(f"✅ Квест сдан! Награда: +{reward} арбузов.")

@bot.command(name="ограбить")
@commands.guild_only()
async def cmd_rob(ctx, target: discord.Member = None):
    if not target or target.bot: return await ctx.reply("Укажи юзера.")
    t_id, v_id = ctx.author.id, target.id
    if user_watermelons.get(v_id, 0) < 3: return await ctx.reply("У него пусто.")
    ok, err = check_cooldown(t_id, "rob")
    if not ok: return await ctx.reply(err)

    if use_item(v_id, "krysha"):
        user_watermelons[t_id] = max(0, user_watermelons.get(t_id, 0) - 5)
        user_watermelons[v_id] += 5
        save_data()
        return await ctx.reply(f"🚓 Сработала Крыша! {ctx.author.mention} оштрафован на 5 арбузов.")

    if random.random() < (0.75 if has_item(t_id, "zatochka") else 0.40):
        stolen = random.randint(3, min(10, user_watermelons[v_id]))
        user_watermelons[v_id] -= stolen; user_watermelons[t_id] = user_watermelons.get(t_id, 0) + stolen
        await ctx.reply(f"🥷 Украл {stolen} арбузов у {target.mention}!")
    else:
        user_watermelons[t_id] = max(0, user_watermelons.get(t_id, 0) - 5)
        try: await ctx.author.timeout(timedelta(minutes=2))
        except: pass
        await ctx.reply("🚨 Пойман! Штраф 5 арбузов и мут.")
    save_data()

@bot.command(name="суд")
@commands.guild_only()
async def cmd_court(ctx, target: discord.Member = None):
    if not target or target.bot: return await ctx.reply("Укажи юзера")
    msg = await ctx.reply(f"⚖️ СУД НАД {target.mention}! 👍 или 👎 (15 сек)")
    await msg.add_reaction("👍"); await msg.add_reaction("👎")
    await asyncio.sleep(15)
    new_msg = await ctx.channel.fetch_message(msg.id)
    up, down = 0, 0
    for r in new_msg.reactions:
        if str(r.emoji) == "👍": up = r.count - 1
        elif str(r.emoji) == "👎": down = r.count - 1
            
    if down > up:
        if use_item(target.id, "krysha"): return await ctx.send("🚓 Суд отменен по блату (Крыша).")
        try: await target.timeout(timedelta(minutes=3))
        except: pass
        await ctx.send(f"⚖️ Признан виновным Мут 3 минуты")
    else: await ctx.send(f"⚖️ Оправдан")

@bot.command(name="обстрел")
@commands.guild_only()
async def cmd_poop_shot(ctx):
    uid = ctx.author.id
    if not ctx.author.guild_permissions.moderate_members:
        if user_watermelons.get(uid, 0) < 5: return await ctx.reply("Нужно 5 арбузов.")
        user_watermelons[uid] -= 5
        save_data()

    members = [m for m in ctx.channel.members if not m.bot and m != ctx.author]
    target = random.choice(members) if members else ctx.author

    if use_item(target.id, "vpn"): return await ctx.send(f"💩 Снаряд отбит! У {target.mention} сработал ВПН!")
    try:
        await target.timeout(timedelta(minutes=3))
        await ctx.send(f"💩 Накрыло {target.mention} Мут 3 мин")
    except: await ctx.send(f"💩 Увернулся")

@bot.command(name="отчислить")
@commands.guild_only()
async def cmd_expel(ctx, target: discord.Member = None):
    if not target or target.bot: return await ctx.reply("Укажи студента")
    async with ctx.typing():
        reply = await get_ai_response([f"[Напиши приказ об отчислении студента '{target.display_name}']"])
        try: await target.timeout(timedelta(minutes=5))
        except: pass
        await ctx.reply(f"🎓 **ПРИКАЗ:**\n{reply}")

@bot.command(name="звонок")
async def cmd_call_police(ctx, target: discord.Member = None):
    t = target or ctx.author
    async with ctx.typing():
        reply = await get_ai_response([f"[Тревожное сообщение от участкового ищущего '{t.display_name}']"])
        await ctx.reply(f"🚨 **УЧАСТКОВЫЙ ИЩЕТ {t.mention}:**\n{reply}")

@bot.command(name="оскорби")
async def cmd_roast(ctx, target: discord.Member = None):
    if not target: return await ctx.reply("Кого?")
    async with ctx.typing():
        reply = await get_ai_response([f"[Жесткий разнос '{target.display_name}']"])
        await ctx.reply(f"{target.mention} слушай сюда\n{reply}")

@bot.command(name="допрос")
async def cmd_interrogate(ctx, target: discord.Member = None):
    if not target: return
    async with ctx.typing():
        reply = await get_ai_response([f"[Жесткий допрос '{target.display_name}']"])
        await ctx.reply(f"ДОПРОС ДЛЯ {target.mention}!\n{reply}")

@bot.command(name="докс")
async def cmd_dox(ctx, target: discord.Member = None):
    t = target or ctx.author
    ip = random.choice(["192.168.0.666", "10.0.2.13", "213.87.14.2"])
    async with ctx.typing():
        reply = await get_ai_response([f"[Угрожай доксом '{t.display_name}']"])
        await ctx.reply(f"🚨 **БАЗА СЛИТА НА {t.mention}!**\nIP: `{ip}`\n{reply}")

@bot.command(name="компромат")
async def cmd_dirt(ctx, target: discord.Member = None):
    t = target or ctx.author
    async with ctx.typing():
        reply = await get_ai_response([f"[Компромат на '{t.display_name}']"])
        await ctx.reply(f"📁 **КОМПРОМАТ НА {t.mention}:**\n{reply}")

@bot.command(name="армия")
async def cmd_army(ctx, target: discord.Member = None):
    t = target or ctx.author
    if random.random() < 0.4: await ctx.reply(f"🪖 {t.mention} списали по дурке.")
    else:
        try: await t.timeout(timedelta(minutes=2))
        except: pass
        await ctx.reply(f"🪖 {t.mention} забрили в армию. Мут 2 минуты.")

@bot.command(name="давалка")
async def cmd_davalka(ctx, target: discord.Member = None):
    t = target or ctx.author
    percent = random.randint(0, 100)
    await ctx.reply(f"📊 Уровень давалки {t.mention}: **{percent}%**!")

@bot.command(name="брак")
@commands.guild_only()
async def cmd_marry(ctx, spouse: discord.Member = None):
    if not spouse or spouse == ctx.author: return await ctx.reply("Укажи юзера")
    if ctx.author.id in marriages or spouse.id in marriages: return await ctx.reply("Кто-то уже в браке")
    await ctx.reply(f"{spouse.mention} тебя зовут замуж! Ответь 'да' за 30 сек")
    def check(m): return m.author == spouse and m.content.lower() in ["да", "го"]
    try:
        await bot.wait_for("message", check=check, timeout=30.0)
        marriages[ctx.author.id] = spouse.id; marriages[spouse.id] = ctx.author.id
        save_data()
        await ctx.reply(f"💕 {ctx.author.mention} и {spouse.mention} теперь муж и жена")
    except: await ctx.reply("Облом")

@bot.command(name="развод")
async def cmd_divorce(ctx):
    if ctx.author.id not in marriages: return await ctx.reply("Ты холостяк")
    sp_id = marriages.pop(ctx.author.id); marriages.pop(sp_id, None); save_data()
    await ctx.reply("Развод оформлен")

@bot.command(name="браки")
async def cmd_marriages(ctx):
    if not marriages: return await ctx.reply("Нет пар")
    lines = ["БРАКИ:\n"] + list(set([f"• <@{u1}> 💕 <@{u2}>" for u1, u2 in marriages.items()]))
    await ctx.reply("\n".join(lines[:10]))

@bot.command(name="записка")
async def cmd_note(ctx, target: discord.Member = None, *, text: str = None):
    if not target or not text: return
    try: await ctx.message.delete()
    except: pass
    await ctx.send(f"АНОНИМКА ДЛЯ {target.mention}\n>>> {text}")

@bot.command(name="госуслуги")
async def cmd_gosuslugi(ctx):
    async with ctx.typing():
        reply = await get_ai_response(["[Госуслуги Армавира]"])
        await ctx.reply(f"📱 **ГОСУСЛУГИ:**\n{reply}")

@bot.command(name="сторис")
async def cmd_story(ctx):
    async with ctx.typing():
        reply = await get_ai_response(["[Текст для кружочка в тг]"])
        await ctx.reply(f"📹 **КРУЖОК:**\n{reply}")

@bot.command(name="гороскоп")
async def cmd_horoscope(ctx):
    async with ctx.typing():
        reply = await get_ai_response(["[Дебильный гороскоп]"])
        await ctx.reply(f"🔮 **ГОРОСКОП:**\n{reply}")

@bot.command(name="шпора")
async def cmd_cheat_sheet(ctx, *, subject: str = "экзамен"):
    async with ctx.typing():
        reply = await get_ai_response([f"[Тупая шпора на '{subject}']"])
        await ctx.reply(f"📝 **ШПОРА:**\n{reply}")

@bot.command(name="роутер")
async def cmd_router(ctx):
    async with ctx.typing():
        reply = await get_ai_response(["[Объясни почему лагает инет]"])
        await ctx.reply(f"📡 **СЕТЬ:**\n{reply}")

@bot.command(name="новости")
async def cmd_news(ctx):
    async with ctx.typing():
        reply = await get_ai_response(["[Абсурдные новости станицы]"])
        await ctx.reply(reply)

@bot.command(name="демотиватор")
async def cmd_demotivator(ctx, *, text: str = "Армавир"):
    url = ctx.message.attachments[0].url if ctx.message.attachments else ctx.author.display_avatar.url
    await ctx.reply(f"```\n[ФОТО: {url[:25]}]\n{text.upper()}\n```")

@bot.command(name="гадание")
async def cmd_oracle(ctx, *, question: str = None):
    if not question: return
    async with ctx.typing():
        reply = await get_ai_response([f"[Предсказание на: {question}]"])
        await ctx.reply(reply)

@bot.command(name="паспорт")
async def cmd_passport(ctx, member: discord.Member = None):
    t = member or ctx.author
    bal = user_watermelons.get(t.id, 0)
    await ctx.reply(f"🪪 **ПАСПОРТ: {t.display_name}**\n🍉 Арбузы: {bal}")

@bot.command(name="топ")
@commands.guild_only()
async def cmd_top(ctx):
    if not user_watermelons: return await ctx.reply("Пусто")
    sorted_u = sorted(user_watermelons.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🍉 **ТОП АРБУЗНИКОВ:**\n" + "\n".join([f"{i}. {ctx.guild.get_member(uid).display_name if ctx.guild.get_member(uid) else uid} — {cnt} 🍉" for i, (uid, cnt) in enumerate(sorted_u, 1)])
    await ctx.reply(text)

@bot.command(name="баланс")
async def cmd_balance(ctx):
    await ctx.reply(f"У тебя {user_watermelons.get(ctx.author.id, 0)} арбузов")

@bot.command(name="дуэль")
@commands.guild_only()
async def cmd_duel(ctx, opponent: discord.Member = None):
    if not opponent or opponent.bot: return await ctx.reply("Укажи челика")
    u1, u2 = ctx.author.id, opponent.id
    if user_watermelons.get(u1, 0) < 5 or user_watermelons.get(u2, 0) < 5: return await ctx.reply("У вас нет по 5 арбузов")
    w1 = 70 if has_item(u1, "zatochka") else 50
    w2 = 70 if has_item(u2, "zatochka") else 50
    winner = random.choices([ctx.author, opponent], weights=[w1, w2], k=1)[0]
    loser = opponent if winner == ctx.author else ctx.author
    user_watermelons[winner.id] += 5
    user_watermelons[loser.id] = max(0, user_watermelons[loser.id] - 5)
    save_data()
    await ctx.reply(f"⚔️ Победил {winner.mention} и забрал 5 арбузов у {loser.mention}!")

@bot.command(name="подарить")
@commands.guild_only()
async def cmd_give(ctx, recipient: discord.Member = None, amount: int = 0):
    if not recipient or amount <= 0: return
    if user_watermelons.get(ctx.author.id, 0) < amount: return await ctx.reply("Мало арбузов")
    user_watermelons[ctx.author.id] -= amount
    user_watermelons[recipient.id] = user_watermelons.get(recipient.id, 0) + amount
    save_data()
    await ctx.reply(f"Перевел {amount} арбузов {recipient.mention}")

@bot.command(name="мут")
@commands.has_permissions(moderate_members=True)
@commands.guild_only()
async def cmd_timeout(ctx, member: discord.Member = None, mins: int = 5):
    if member: 
        try: await member.timeout(timedelta(minutes=mins))
        except: pass
    await ctx.reply("Замучен")

@bot.command(name="размут")
@commands.has_permissions(moderate_members=True)
@commands.guild_only()
async def cmd_untimeout(ctx, member: discord.Member = None):
    if member: 
        try: await member.timeout(None)
        except: pass
    await ctx.reply("Размучен")

@bot.command(name="кик")
@commands.has_permissions(kick_members=True)
@commands.guild_only()
async def cmd_kick(ctx, member: discord.Member = None):
    if member: 
        try: await member.kick()
        except: pass
    await ctx.reply("Кикнут")

@bot.command(name="бан")
@commands.has_permissions(ban_members=True)
@commands.guild_only()
async def cmd_ban(ctx, member: discord.Member = None):
    if member: 
        try: await member.ban()
        except: pass
    await ctx.reply("Забанен")

@bot.command(name="разбан")
@commands.has_permissions(ban_members=True)
@commands.guild_only()
async def cmd_unban(ctx, uid: int = 0):
    if uid:
        try:
            user = await bot.fetch_user(uid)
            await ctx.guild.unban(user)
        except: pass
    await ctx.reply("Разбанен")

# ---------------------------------------------------------------------------
# 6. ОБРАБОТЧИК СООБЩЕНИЙ (С РАСПОЗНАВАНИЕМ НИКНЕЙМОВ)
# ---------------------------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    msg_lower = message.content.lower()
    author_name = message.author.display_name

    if any(k in msg_lower for k in ["мать", "мамка", "родители"]) and random.random() < 0.3:
        async with message.channel.typing():
            reply = await get_ai_response([f"[От: {author_name}] [Вступись за родителей: '{message.content}']"])
            return await message.reply(reply)

    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel) or random.random() < 0.10:
        async with message.channel.typing():
            clean = message.content.replace(f"<@{bot.user.id}>", "").strip()
            text_to_send = clean if clean else "Расскажи че-нибудь"
            
            payload = f"[Сообщение от пользователя с ником {author_name}]: {text_to_send}"
            
            reply = await get_ai_response([payload])
            await message.reply(reply[:2000])

@bot.event
async def on_ready():
    load_data()
    print(f"Бот запущен как: {bot.user.name}")
    if not change_status.is_running(): change_status.start()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)