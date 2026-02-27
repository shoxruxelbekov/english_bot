import sqlite3
import asyncio
import os
import random
import uuid
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from gtts import gTTS
from deep_translator import GoogleTranslator
from groq import Groq

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "8460732938:AAEXxdsq7uzI9VwgKEIWCAbRUcwMw2crwaw"
GROQ_KEY = "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"
ADMIN_ID = 6202785302

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, username TEXT)''')
    conn.commit()
    conn.close()

def save_user(user_id, name, username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)',
              (user_id, name, username or "yoq"))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()
    return users

# ==================== BOT SOZLASH ====================
groq_client = Groq(api_key=GROQ_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== XOTIRA ====================
user_states = {}
user_scores = {}
user_current_word = {}
active_duels = {}
user_duel = {}
waiting_queue = []
learn_sessions = {}

# ==================== AI ====================
def ask_ai(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800
    )
    return response.choices[0].message.content

def get_duel_words_ai(topic):
    prompt = (
        f"Give me exactly 10 English words about '{topic}' for Uzbek learners. "
        f"Return ONLY a JSON array like this, nothing else: "
        f'[{{"en":"word1","uz":"tarjima1"}},{{"en":"word2","uz":"tarjima2"}}]'
    )
    result = ask_ai(prompt)
    try:
        start = result.find('[')
        end = result.rfind(']') + 1
        return json.loads(result[start:end])
    except:
        return [
            {"en": "apple", "uz": "olma"},
            {"en": "book", "uz": "kitob"},
            {"en": "water", "uz": "suv"},
            {"en": "house", "uz": "uy"},
            {"en": "sun", "uz": "quyosh"},
            {"en": "cat", "uz": "mushuk"},
            {"en": "dog", "uz": "it"},
            {"en": "bird", "uz": "qush"},
            {"en": "fish", "uz": "baliq"},
            {"en": "car", "uz": "mashina"},
        ]

def get_learn_questions_ai(topic, level):
    level_desc = {"beginner": "A1-A2 basic", "intermediate": "B1-B2 medium", "advanced": "C1-C2 advanced"}
    prompt = (
        f"Create 5 English grammar/vocabulary multiple choice questions about '{topic}' "
        f"for {level_desc.get(level, 'basic')} level Uzbek learners. "
        f"Return ONLY a JSON array, nothing else: "
        f'[{{"question":"...","options":["A) ...","B) ...","C) ...","D) ..."],"correct":"A) ...",'
        f'"explanation":"short explanation in Uzbek"}}]'
    )
    result = ask_ai(prompt)
    try:
        start = result.find('[')
        end = result.rfind(']') + 1
        return json.loads(result[start:end])
    except:
        return None

# ==================== FLASHCARD SO'ZLARI ====================
flashcard_words = {
    "easy": [
        {"en": "apple", "uz": "olma"}, {"en": "book", "uz": "kitob"},
        {"en": "water", "uz": "suv"}, {"en": "house", "uz": "uy"},
        {"en": "sun", "uz": "quyosh"}, {"en": "moon", "uz": "oy"},
        {"en": "cat", "uz": "mushuk"}, {"en": "dog", "uz": "it"},
        {"en": "food", "uz": "ovqat"}, {"en": "car", "uz": "mashina"},
        {"en": "hand", "uz": "qol"}, {"en": "eye", "uz": "koz"},
        {"en": "bread", "uz": "non"}, {"en": "milk", "uz": "sut"},
        {"en": "egg", "uz": "tuxum"}, {"en": "tea", "uz": "choy"},
        {"en": "fire", "uz": "olov"}, {"en": "rain", "uz": "yomgir"},
        {"en": "bird", "uz": "qush"}, {"en": "fish", "uz": "baliq"},
    ],
    "medium": [
        {"en": "school", "uz": "maktab"}, {"en": "friend", "uz": "dust"},
        {"en": "bridge", "uz": "koprik"}, {"en": "market", "uz": "bozor"},
        {"en": "hospital", "uz": "kasalxona"}, {"en": "teacher", "uz": "oqituvchi"},
        {"en": "student", "uz": "talaba"}, {"en": "mountain", "uz": "tog"},
        {"en": "forest", "uz": "ormon"}, {"en": "desert", "uz": "chol"},
        {"en": "driver", "uz": "haydovchi"}, {"en": "doctor", "uz": "shifokor"},
        {"en": "village", "uz": "qishloq"}, {"en": "window", "uz": "deraza"},
        {"en": "flower", "uz": "gul"}, {"en": "chicken", "uz": "tovuq"},
        {"en": "finger", "uz": "barmoq"}, {"en": "sugar", "uz": "shakar"},
        {"en": "cloud", "uz": "bulut"}, {"en": "river", "uz": "daryo"},
    ],
    "hard": [
        {"en": "beautiful", "uz": "chiroyli"}, {"en": "difficult", "uz": "qiyin"},
        {"en": "comfortable", "uz": "qulay"}, {"en": "government", "uz": "hukumat"},
        {"en": "environment", "uz": "atrof-muhit"}, {"en": "opportunity", "uz": "imkoniyat"},
        {"en": "responsible", "uz": "masuliyatli"}, {"en": "independent", "uz": "mustaqil"},
        {"en": "experience", "uz": "tajriba"}, {"en": "development", "uz": "rivojlanish"},
        {"en": "achievement", "uz": "yutuq"}, {"en": "imagination", "uz": "tasavvur"},
        {"en": "volunteer", "uz": "kongilli"}, {"en": "agriculture", "uz": "qishloq xojaligi"},
        {"en": "technology", "uz": "texnologiya"}, {"en": "electricity", "uz": "elektr"},
        {"en": "university", "uz": "universitet"}, {"en": "competition", "uz": "musobaqa"},
        {"en": "celebration", "uz": "bayram"}, {"en": "profession", "uz": "kasb"},
    ]
}

# ==================== /start ====================
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("duel_"):
        duel_id = args[1].replace("duel_", "")
        await join_duel_by_link(message, duel_id)
        return

    save_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    name = message.from_user.first_name
    await message.answer(
        f"Salom, {name}!\n\n"
        "Men ingliz tili organishga yordam beraman!\n\n"
        "Imkoniyatlarim:\n"
        "/translate - Tarjima + audio\n"
        "/topic - AI mavzu malumoti\n"
        "/wordofday - Kunlik yangi soz\n"
        "/flashcard - Soz oyini\n"
        "/duel - Dust bilan bellashuv\n"
        "/learn - Ingliz tili darslari\n"
        "/help - Yordam"
    )

# ==================== /help ====================
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "Yordam:\n\n"
        "/translate - Tarjima + audio\n"
        "/topic - AI mavzu malumoti\n"
        "/wordofday - Kunlik yangi soz\n"
        "/flashcard - Soz oyini (3 daraja)\n"
        "/duel - Dust bilan bellashuv (AI sozlar)\n"
        "/learn - Ingliz tili darslari + test\n"
    )

# ==================== /translate ====================
@dp.message(Command("translate"))
async def translate_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_translate"
    await message.answer("Inglizcha yoki ozbekcha soz yuboring:")

# ==================== /topic ====================
@dp.message(Command("topic"))
async def topic_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_topic"
    await message.answer("Qaysi mavzuda inglizcha malumot olmoqchisiz?\n\nMasalan: sport, food, technology")

# ==================== /wordofday ====================
@dp.message(Command("wordofday"))
async def word_of_day(message: types.Message):
    await message.answer("Kunlik soz tayyorlanmoqda...")
    try:
        result = ask_ai(
            "Give me one interesting English word for Uzbek learners. "
            "Format:\nWord: ...\nTranslation (Uzbek): ...\nExample sentence: ...\nPronunciation tip: ..."
        )
        await message.answer(f"Bugungi soz:\n\n{result}")
    except Exception as e:
        await message.answer(f"Xatolik: {str(e)}")

# ==================== /users (admin) ====================
@dp.message(Command("users"))
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Bu komanda faqat admin uchun!")
        return
    users = get_all_users()
    if not users:
        await message.answer("Hali hech kim botdan foydalanmagan!")
        return
    text = f"Foydalanuvchilar soni: {len(users)} ta\n\n"
    for user in users:
        text += f"Ism: {user[1]}\nUsername: @{user[2]}\nID: {user[0]}\n\n"
    await message.answer(text)

# ==================== /flashcard ====================
@dp.message(Command("flashcard"))
async def flashcard_start(message: types.Message):
    user_states[message.from_user.id] = None
    await message.answer(
        "Qaysi darajani tanlaysiz?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Oson", callback_data="level_easy"),
                types.InlineKeyboardButton(text="Orta", callback_data="level_medium"),
                types.InlineKeyboardButton(text="Qiyin", callback_data="level_hard"),
            ]
        ])
    )

# ==================== /learn ====================
@dp.message(Command("learn"))
async def learn_start(message: types.Message):
    await message.answer(
        "Ingliz tili darajangizni tanlang:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Boshlangich", callback_data="learn_level_beginner"),
                types.InlineKeyboardButton(text="Orta", callback_data="learn_level_intermediate"),
                types.InlineKeyboardButton(text="Yuqori", callback_data="learn_level_advanced"),
            ]
        ])
    )

# ==================== /duel ====================
@dp.message(Command("duel"))
async def duel_start(message: types.Message):
    await message.answer(
        "Qanday o'ynashni xohlaysiz?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Dust bilan (havola)", callback_data="duel_mode_friend"),
            ],
            [
                types.InlineKeyboardButton(text="Raqib qidirish", callback_data="duel_mode_search"),
            ]
        ])
    )

# ==================== DUEL HELPER ====================
async def start_duel_topic_selection(message_or_callback, user_id):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="Hayvonlar", callback_data="dueltopic_hayvonlar"),
            types.InlineKeyboardButton(text="Ovqat", callback_data="dueltopic_ovqat"),
        ],
        [
            types.InlineKeyboardButton(text="Sport", callback_data="dueltopic_sport"),
            types.InlineKeyboardButton(text="Tabiat", callback_data="dueltopic_tabiat"),
        ],
        [
            types.InlineKeyboardButton(text="Kasb-hunar", callback_data="dueltopic_kasb-hunar"),
            types.InlineKeyboardButton(text="Texnologiya", callback_data="dueltopic_texnologiya"),
        ],
        [
            types.InlineKeyboardButton(text="Oila", callback_data="dueltopic_oila"),
            types.InlineKeyboardButton(text="Shahar", callback_data="dueltopic_shahar"),
        ],
    ])
    if hasattr(message_or_callback, 'message'):
        await message_or_callback.message.answer("Mavzu tanlang:", reply_markup=kb)
    else:
        await message_or_callback.answer("Mavzu tanlang:", reply_markup=kb)

async def join_duel_by_link(message: types.Message, duel_id: str):
    user_id = message.from_user.id
    if duel_id not in active_duels:
        await message.answer("Bu oyin topilmadi yoki muddati tugagan!")
        return
    duel = active_duels[duel_id]
    if duel["player1_id"] == user_id:
        await message.answer("Siz oz oyiningizga qoshila olmaysiz!")
        return
    if duel["status"] != "waiting":
        await message.answer("Bu oyin allaqachon boshlangan!")
        return
    await launch_duel(duel_id, user_id, message.from_user.first_name, message)

async def launch_duel(duel_id, player2_id, player2_name, message):
    duel = active_duels[duel_id]
    duel["player2_id"] = player2_id
    duel["player2_name"] = player2_name
    duel["status"] = "active"
    user_duel[player2_id] = duel_id
    word = duel["words"][0]
    await bot.send_message(
        duel["player1_id"],
        f"{player2_name} oyinga qoshildi!\n\n"
        f"Oyin boshlanadi! Mavzu: {duel['topic']}\n\n"
        f"1-soz: {word['en']}\n"
        f"Ozbekcha tarjimasini yozing:"
    )
    await message.answer(
        f"{duel['player1_name']} bilan oyin boshlanadi!\n"
        f"Mavzu: {duel['topic']}\n\n"
        f"1-soz: {word['en']}\n"
        f"Ozbekcha tarjimasini yozing:"
    )

# ==================== CALLBACKS ====================
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    # --- FLASHCARD ---
    if data.startswith("level_"):
        level = data.replace("level_", "")
        level_names = {"easy": "Oson", "medium": "Orta", "hard": "Qiyin"}
        last_word = user_current_word.get(user_id)
        available_words = [w for w in flashcard_words[level] if w != last_word]
        word = random.choice(available_words)
        user_current_word[user_id] = word
        user_states[user_id] = f"waiting_flashcard_{level}"
        if user_id not in user_scores:
            user_scores[user_id] = {"correct": 0, "wrong": 0}
        await callback.message.answer(
            f"Daraja: {level_names[level]}\n\n"
            f"Inglizcha soz: {word['en']}\n\n"
            f"Ozbekcha tarjimasini yozing:"
        )

    # --- DUEL MODE ---
    elif data == "duel_mode_friend":
        user_states[user_id] = "duel_friend"
        await start_duel_topic_selection(callback, user_id)

    elif data == "duel_mode_search":
        if user_id in waiting_queue:
            await callback.message.answer("Siz allaqachon qidiryapsiz, kuting...")
        elif waiting_queue:
            opponent_id = waiting_queue.pop(0)
            user_states[user_id] = "duel_search"
            await callback.message.answer("Raqib topildi! Mavzu tanlang:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="Hayvonlar", callback_data=f"duelsearch_hayvonlar_{opponent_id}"),
                        types.InlineKeyboardButton(text="Ovqat", callback_data=f"duelsearch_ovqat_{opponent_id}"),
                    ],
                    [
                        types.InlineKeyboardButton(text="Sport", callback_data=f"duelsearch_sport_{opponent_id}"),
                        types.InlineKeyboardButton(text="Tabiat", callback_data=f"duelsearch_tabiat_{opponent_id}"),
                    ],
                    [
                        types.InlineKeyboardButton(text="Kasb-hunar", callback_data=f"duelsearch_kasb-hunar_{opponent_id}"),
                        types.InlineKeyboardButton(text="Texnologiya", callback_data=f"duelsearch_texnologiya_{opponent_id}"),
                    ],
                ])
            )
        else:
            waiting_queue.append(user_id)
            await callback.message.answer(
                "Raqib qidirilmoqda...\n\n"
                "Boshqa birov ham raqib qidirganda, oyin boshlanadi!\n"
                "Havolani guruhga tashlang: do'stlaringizdan biri /duel bosib 'Raqib qidirish' tanlasa birlashtiradi!"
            )

    # --- DUEL SEARCH TOPIC ---
    elif data.startswith("duelsearch_"):
        parts = data.replace("duelsearch_", "").rsplit("_", 1)
        topic = parts[0]
        opponent_id = int(parts[1])
        await callback.message.answer(f"So'zlar tayyorlanmoqda... (AI {topic} mavzusidan so'z olmoqda)")
        words = get_duel_words_ai(topic)
        random.shuffle(words)
        duel_id = str(uuid.uuid4())[:8]
        active_duels[duel_id] = {
            "player1_id": opponent_id,
            "player1_name": "Raqib",
            "player2_id": user_id,
            "player2_name": callback.from_user.first_name,
            "topic": topic,
            "words": words,
            "score1": 0,
            "score2": 0,
            "current_word": 0,
            "p1_answered": False,
            "p2_answered": False,
            "status": "active"
        }
        user_duel[user_id] = duel_id
        user_duel[opponent_id] = duel_id
        word = words[0]
        await bot.send_message(
            opponent_id,
            f"Raqib topildi! Mavzu: {topic}\n\n"
            f"1-soz: {word['en']}\n"
            f"Ozbekcha tarjimasini yozing:"
        )
        await callback.message.answer(
            f"Oyin boshlanadi! Mavzu: {topic}\n\n"
            f"1-soz: {word['en']}\n"
            f"Ozbekcha tarjimasini yozing:"
        )

    # --- DUEL TOPIC (friend) ---
    elif data.startswith("dueltopic_"):
        topic = data.replace("dueltopic_", "")
        await callback.message.answer(f"So'zlar tayyorlanmoqda... (AI {topic} mavzusidan so'z olmoqda)")
        words = get_duel_words_ai(topic)
        random.shuffle(words)
        duel_id = str(uuid.uuid4())[:8]
        active_duels[duel_id] = {
            "player1_id": user_id,
            "player1_name": callback.from_user.first_name,
            "player2_id": None,
            "player2_name": None,
            "topic": topic,
            "words": words,
            "score1": 0,
            "score2": 0,
            "current_word": 0,
            "p1_answered": False,
            "p2_answered": False,
            "status": "waiting"
        }
        user_duel[user_id] = duel_id
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=duel_{duel_id}"
        await callback.message.answer(
            f"Mavzu: {topic}\n\n"
            f"Dustingizga yoki guruhga quyidagi havolani yuboring:\n\n"
            f"{link}\n\n"
            f"Dustingiz qoshilishini kuting..."
        )

    # --- LEARN LEVEL ---
    elif data.startswith("learn_level_"):
        level = data.replace("learn_level_", "")
        level_names = {"beginner": "Boshlangich", "intermediate": "Orta", "advanced": "Yuqori"}
        learn_sessions[user_id] = {"level": level}
        await callback.message.answer(
            f"Daraja: {level_names[level]}\n\nMavzu tanlang:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="Zamonlar (Tenses)", callback_data="learn_topic_tenses"),
                    types.InlineKeyboardButton(text="Prepositions", callback_data="learn_topic_prepositions"),
                ],
                [
                    types.InlineKeyboardButton(text="Vocabulary", callback_data="learn_topic_vocabulary"),
                    types.InlineKeyboardButton(text="Phrasal Verbs", callback_data="learn_topic_phrasal_verbs"),
                ],
                [
                    types.InlineKeyboardButton(text="Articles (a/an/the)", callback_data="learn_topic_articles"),
                    types.InlineKeyboardButton(text="Modal Verbs", callback_data="learn_topic_modal_verbs"),
                ],
            ])
        )

    # --- LEARN TOPIC ---
    elif data.startswith("learn_topic_"):
        topic = data.replace("learn_topic_", "").replace("_", " ")
        if user_id not in learn_sessions:
            await callback.message.answer("Iltimos qaytadan /learn bosing!")
            return
        level = learn_sessions[user_id]["level"]
        await callback.message.answer(f"Savollar tayyorlanmoqda... ({topic} mavzusi)")
        questions = get_learn_questions_ai(topic, level)
        if not questions:
            await callback.message.answer("Xatolik! Qaytadan urinib koring.")
            return
        learn_sessions[user_id] = {
            "level": level,
            "topic": topic,
            "questions": questions,
            "current": 0,
            "score": 0
        }
        await send_learn_question(callback.message, user_id)

    # --- LEARN ANSWER ---
    elif data.startswith("learn_answer_"):
        answer = data.replace("learn_answer_", "")
        if user_id not in learn_sessions or "questions" not in learn_sessions[user_id]:
            await callback.message.answer("Iltimos qaytadan /learn bosing!")
            return
        session = learn_sessions[user_id]
        current_q = session["questions"][session["current"]]
        correct = current_q["correct"]
        if answer == correct:
            session["score"] += 1
            await callback.message.answer(f"Togri! \n\n{current_q['explanation']}")
        else:
            await callback.message.answer(f"Notogri!\nTogri javob: {correct}\n\n{current_q['explanation']}")
        session["current"] += 1
        if session["current"] >= len(session["questions"]):
            score = session["score"]
            total = len(session["questions"])
            if score == total:
                result_text = f"Ajoyib! {score}/{total} - Mukammal natija!"
            elif score >= total * 0.6:
                result_text = f"Yaxshi! {score}/{total} - Davom eting!"
            else:
                result_text = f"{score}/{total} - Ko'proq mashq qiling!"
            await callback.message.answer(
                f"Test tugadi!\n\n{result_text}\n\n"
                f"Yana sinash uchun /learn bosing!"
            )
            del learn_sessions[user_id]
        else:
            await send_learn_question(callback.message, user_id)

    await callback.answer()

async def send_learn_question(message, user_id):
    session = learn_sessions[user_id]
    q = session["questions"][session["current"]]
    num = session["current"] + 1
    total = len(session["questions"])
    options = q["options"]
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=options[0], callback_data=f"learn_answer_{options[0]}")],
        [types.InlineKeyboardButton(text=options[1], callback_data=f"learn_answer_{options[1]}")],
        [types.InlineKeyboardButton(text=options[2], callback_data=f"learn_answer_{options[2]}")],
        [types.InlineKeyboardButton(text=options[3], callback_data=f"learn_answer_{options[3]}")],
    ])
    await message.answer(
        f"Savol {num}/{total}:\n\n{q['question']}",
        reply_markup=kb
    )

# ==================== XABARLAR ====================
@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    try:
        # DUEL O'YIN
        if user_id in user_duel and active_duels.get(user_duel[user_id], {}).get("status") == "active":
            duel_id = user_duel[user_id]
            duel = active_duels[duel_id]
            current_idx = duel["current_word"]
            word = duel["words"][current_idx]
            correct = word["uz"].lower()
            answer = text.lower().strip()
            is_player1 = duel["player1_id"] == user_id
            already_answered = duel["p1_answered"] if is_player1 else duel["p2_answered"]

            if already_answered:
                await message.answer("Siz allaqachon javob berdingiz, sherigingizni kuting!")
                return

            if is_player1:
                duel["p1_answered"] = True
            else:
                duel["p2_answered"] = True

            if answer == correct:
                if is_player1:
                    duel["score1"] += 1
                else:
                    duel["score2"] += 1
                await message.answer("Togri!")
            else:
                await message.answer(f"Notogri! Togri javob: {correct}")

            if duel["p1_answered"] and duel["p2_answered"]:
                duel["current_word"] += 1
                duel["p1_answered"] = False
                duel["p2_answered"] = False

                if duel["current_word"] >= len(duel["words"]):
                    s1 = duel["score1"]
                    s2 = duel["score2"]
                    p1 = duel["player1_name"]
                    p2 = duel["player2_name"]
                    if s1 > s2:
                        result = f"Golib: {p1}!\n{p1}: {s1} | {p2}: {s2}"
                    elif s2 > s1:
                        result = f"Golib: {p2}!\n{p1}: {s1} | {p2}: {s2}"
                    else:
                        result = f"Durang!\nIkkalangiz: {s1}"
                    await bot.send_message(duel["player1_id"], f"Oyin tugadi!\n\n{result}")
                    await bot.send_message(duel["player2_id"], f"Oyin tugadi!\n\n{result}")
                    p1_id = duel["player1_id"]
                    p2_id = duel["player2_id"]
                    del active_duels[duel_id]
                    if p1_id in user_duel:
                        del user_duel[p1_id]
                    if p2_id in user_duel:
                        del user_duel[p2_id]
                else:
                    next_word = duel["words"][duel["current_word"]]
                    num = duel["current_word"] + 1
                    await bot.send_message(duel["player1_id"], f"{num}-soz: {next_word['en']}\nOzbekcha tarjimasini yozing:")
                    await bot.send_message(duel["player2_id"], f"{num}-soz: {next_word['en']}\nOzbekcha tarjimasini yozing:")

        # FLASHCARD
        elif user_states.get(user_id, "").startswith("waiting_flashcard"):
            user_states[user_id] = None
            word = user_current_word.get(user_id)
            correct_answer = word["uz"].lower()
            user_answer = text.lower().strip()
            if user_answer == correct_answer:
                user_scores[user_id]["correct"] += 1
                score = user_scores[user_id]
                await message.answer(
                    f"Togri! Barakalla!\n\n"
                    f"Natija: {score['correct']} togri | {score['wrong']} notogri\n\n"
                    f"Davom etish uchun /flashcard bosing!"
                )
            else:
                user_scores[user_id]["wrong"] += 1
                score = user_scores[user_id]
                await message.answer(
                    f"Notogri!\n\nTogri javob: {correct_answer}\n\n"
                    f"Natija: {score['correct']} togri | {score['wrong']} notogri\n\n"
                    f"Davom etish uchun /flashcard bosing!"
                )

        # TOPIC
        elif user_states.get(user_id) == "waiting_topic":
            user_states[user_id] = None
            await message.answer("AI javob tayyorlanmoqda...")
            result = ask_ai(
                f"Give a short, simple English explanation about '{text}' "
                f"for Uzbek English learners. Max 5 sentences. "
                f"Then provide 3 key vocabulary words with Uzbek translations."
            )
            await message.answer(f"{text.upper()} haqida:\n\n{result}")

        # TRANSLATE
        else:
            detected = GoogleTranslator(source='auto', target='en').translate(text)
            if detected.lower() != text.lower():
                await message.answer(f"Ozbekcha: {text}\nInglizcha: {detected}")
                tts = gTTS(text=detected, lang='en')
            else:
                translated = GoogleTranslator(source='en', target='uz').translate(text)
                await message.answer(f"Inglizcha: {text}\nOzbekcha: {translated}")
                tts = gTTS(text=text, lang='en')
            audio_file = "audio.mp3"
            tts.save(audio_file)
            await message.answer_voice(types.FSInputFile(audio_file))
            os.remove(audio_file)

    except Exception as e:
        await message.answer(f"Xatolik: {str(e)}")

# ==================== MAIN ====================
async def main():
    init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Botni boshlash"),
        types.BotCommand(command="translate", description="Tarjima + audio"),
        types.BotCommand(command="topic", description="AI mavzu malumoti"),
        types.BotCommand(command="wordofday", description="Kunlik yangi soz"),
        types.BotCommand(command="flashcard", description="Soz oyini"),
        types.BotCommand(command="duel", description="Dust bilan bellashuv"),
        types.BotCommand(command="learn", description="Ingliz tili darslari"),
        types.BotCommand(command="help", description="Yordam"),
    ])
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
