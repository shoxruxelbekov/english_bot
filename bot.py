import sqlite3
import asyncio
import os
import random
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from gtts import gTTS
from deep_translator import GoogleTranslator
from groq import Groq

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, username TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS duels (id TEXT PRIMARY KEY, player1_id INTEGER, player2_id INTEGER, topic TEXT, words TEXT, score1 INTEGER DEFAULT 0, score2 INTEGER DEFAULT 0, current_word INTEGER DEFAULT 0, status TEXT DEFAULT "waiting")''')
    conn.commit()
    conn.close()

BOT_TOKEN = "8460732938:AAEXxdsq7uzI9VwgKEIWCAbRUcwMw2crwaw"
GROQ_KEY = "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"
ADMIN_ID = 6202785302

groq_client = Groq(api_key=GROQ_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_states = {}
user_scores = {}
user_current_word = {}
users_db = {}
active_duels = {}
user_duel = {}

def ask_ai(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

flashcard_words = {
    "easy": [
        {"en": "apple", "uz": "olma"},
        {"en": "book", "uz": "kitob"},
        {"en": "water", "uz": "suv"},
        {"en": "house", "uz": "uy"},
        {"en": "sun", "uz": "quyosh"},
        {"en": "moon", "uz": "oy"},
        {"en": "cat", "uz": "mushuk"},
        {"en": "dog", "uz": "it"},
        {"en": "food", "uz": "ovqat"},
        {"en": "car", "uz": "mashina"},
        {"en": "hand", "uz": "qol"},
        {"en": "eye", "uz": "koz"},
        {"en": "bread", "uz": "non"},
        {"en": "milk", "uz": "sut"},
        {"en": "egg", "uz": "tuxum"},
        {"en": "tea", "uz": "choy"},
        {"en": "fire", "uz": "olov"},
        {"en": "rain", "uz": "yomgir"},
        {"en": "bird", "uz": "qush"},
        {"en": "fish", "uz": "baliq"},
    ],
    "medium": [
        {"en": "school", "uz": "maktab"},
        {"en": "friend", "uz": "dust"},
        {"en": "bridge", "uz": "koprik"},
        {"en": "market", "uz": "bozor"},
        {"en": "hospital", "uz": "kasalxona"},
        {"en": "teacher", "uz": "oqituvchi"},
        {"en": "student", "uz": "talaba"},
        {"en": "mountain", "uz": "tog"},
        {"en": "forest", "uz": "ormon"},
        {"en": "desert", "uz": "chol"},
        {"en": "driver", "uz": "haydovchi"},
        {"en": "doctor", "uz": "shifokor"},
        {"en": "village", "uz": "qishloq"},
        {"en": "window", "uz": "deraza"},
        {"en": "flower", "uz": "gul"},
        {"en": "chicken", "uz": "tovuq"},
        {"en": "finger", "uz": "barmoq"},
        {"en": "sugar", "uz": "shakar"},
        {"en": "cloud", "uz": "bulut"},
        {"en": "river", "uz": "daryo"},
    ],
    "hard": [
        {"en": "beautiful", "uz": "chiroyli"},
        {"en": "difficult", "uz": "qiyin"},
        {"en": "comfortable", "uz": "qulay"},
        {"en": "government", "uz": "hukumat"},
        {"en": "environment", "uz": "atrof-muhit"},
        {"en": "opportunity", "uz": "imkoniyat"},
        {"en": "responsible", "uz": "masuliyatli"},
        {"en": "independent", "uz": "mustaqil"},
        {"en": "experience", "uz": "tajriba"},
        {"en": "development", "uz": "rivojlanish"},
        {"en": "achievement", "uz": "yutuq"},
        {"en": "imagination", "uz": "tasavvur"},
        {"en": "volunteer", "uz": "kongilli"},
        {"en": "agriculture", "uz": "qishloq xojaligi"},
        {"en": "technology", "uz": "texnologiya"},
        {"en": "electricity", "uz": "elektr"},
        {"en": "university", "uz": "universitet"},
        {"en": "competition", "uz": "musobaqa"},
        {"en": "celebration", "uz": "bayram"},
        {"en": "profession", "uz": "kasb"},
    ]
}

duel_words = {
    "animals": [
        {"en": "cat", "uz": "mushuk"},
        {"en": "dog", "uz": "it"},
        {"en": "bird", "uz": "qush"},
        {"en": "fish", "uz": "baliq"},
        {"en": "horse", "uz": "ot"},
        {"en": "cow", "uz": "sigir"},
        {"en": "sheep", "uz": "qoy"},
        {"en": "lion", "uz": "sher"},
        {"en": "tiger", "uz": "yolbars"},
        {"en": "elephant", "uz": "fil"},
    ],
    "food": [
        {"en": "bread", "uz": "non"},
        {"en": "milk", "uz": "sut"},
        {"en": "egg", "uz": "tuxum"},
        {"en": "meat", "uz": "gosht"},
        {"en": "rice", "uz": "guruch"},
        {"en": "apple", "uz": "olma"},
        {"en": "water", "uz": "suv"},
        {"en": "tea", "uz": "choy"},
        {"en": "sugar", "uz": "shakar"},
        {"en": "salt", "uz": "tuz"},
    ],
    "sport": [
        {"en": "ball", "uz": "top"},
        {"en": "run", "uz": "yugurish"},
        {"en": "swim", "uz": "suzish"},
        {"en": "jump", "uz": "sakrash"},
        {"en": "team", "uz": "jamoa"},
        {"en": "win", "uz": "galaba"},
        {"en": "lose", "uz": "yutqazish"},
        {"en": "game", "uz": "oyin"},
        {"en": "player", "uz": "oyinchi"},
        {"en": "score", "uz": "hisob"},
    ],
    "nature": [
        {"en": "sun", "uz": "quyosh"},
        {"en": "moon", "uz": "oy"},
        {"en": "rain", "uz": "yomgir"},
        {"en": "river", "uz": "daryo"},
        {"en": "mountain", "uz": "tog"},
        {"en": "forest", "uz": "ormon"},
        {"en": "flower", "uz": "gul"},
        {"en": "tree", "uz": "daraxt"},
        {"en": "cloud", "uz": "bulut"},
        {"en": "wind", "uz": "shamol"},
    ],
}

@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("duel_"):
        duel_id = args[1].replace("duel_", "")
        await join_duel(message, duel_id)
        return
    users_db[message.from_user.id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username or "yoq"
    }
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)',
              (message.from_user.id,
               message.from_user.full_name,
               message.from_user.username or "yoq"))
    conn.commit()
    conn.close()
    name = message.from_user.first_name
    await message.answer(
        f"Salom, {name}!\n\n"
        "Men ingliz tili organishga yordam beraman!\n\n"
        "Mening imkoniyatlarim:\n"
        "/translate - Soz tarjimasi + audio\n"
        "/topic - Mavzu boyicha AI malumot\n"
        "/wordofday - Kunlik yangi soz\n"
        "/flashcard - Soz oyini\n"
        "/duel - Dust bilan bellashuv\n"
        "/help - Yordam"
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "Yordam:\n\n"
        "/translate - Soz yoki jumla yuboring, tarjima + audio olasiz\n"
        "/topic - Mavzu yozing, AI malumot beradi\n"
        "/wordofday - Bugungi yangi soz\n"
        "/flashcard - Soz oyini, darajali\n"
        "/duel - Dust bilan bellashuv\n"
    )

@dp.message(Command("translate"))
async def translate_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_translate"
    await message.answer("Inglizcha yoki ozbekcha soz yuboring:")

@dp.message(Command("topic"))
async def topic_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_topic"
    await message.answer("Qaysi mavzuda inglizcha malumot olmoqchisiz?\n\nMasalan: sport, food, technology, nature")

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

@dp.message(Command("users"))
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Bu komanda faqat admin uchun!")
        return
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()
    if not users:
        await message.answer("Hali hech kim botdan foydalanmagan!")
        return
    text = f"Foydalanuvchilar soni: {len(users)} ta\n\n"
    for user in users:
        text += f"Ism: {user[1]}\nUsername: @{user[2]}\nID: {user[0]}\n\n"
    await message.answer(text)

@dp.message(Command("flashcard"))
async def flashcard_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = None
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

@dp.message(Command("duel"))
async def duel_start(message: types.Message):
    await message.answer(
        "Mavzu tanlang:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Hayvonlar", callback_data="duel_animals"),
                types.InlineKeyboardButton(text="Ovqat", callback_data="duel_food"),
            ],
            [
                types.InlineKeyboardButton(text="Sport", callback_data="duel_sport"),
                types.InlineKeyboardButton(text="Tabiat", callback_data="duel_nature"),
            ]
        ])
    )

async def join_duel(message: types.Message, duel_id: str):
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
    duel["player2_id"] = user_id
    duel["status"] = "active"
    user_duel[user_id] = duel_id
    p1_name = duel["player1_name"]
    p2_name = message.from_user.first_name
    word = duel["words"][0]
    await bot.send_message(
        duel["player1_id"],
        f"{p2_name} oyinga qoshildi!\n\n"
        f"Oyin boshlanadi!\n\n"
        f"1-soz: {word['en']}\n"
        f"Ozbekcha tarjimasini yozing:"
    )
    await message.answer(
        f"{p1_name} bilan oyin boshlanadi!\n\n"
        f"1-soz: {word['en']}\n"
        f"Ozbekcha tarjimasini yozing:"
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

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

    elif data.startswith("duel_"):
        topic = data.replace("duel_", "")
        topic_names = {"animals": "Hayvonlar", "food": "Ovqat", "sport": "Sport", "nature": "Tabiat"}
        words = duel_words[topic].copy()
        random.shuffle(words)
        duel_id = str(uuid.uuid4())[:8]
        active_duels[duel_id] = {
            "player1_id": user_id,
            "player1_name": callback.from_user.first_name,
            "player2_id": None,
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
            f"Mavzu: {topic_names[topic]}\n\n"
            f"Dustingizga quyidagi havolani yuboring:\n\n"
            f"{link}\n\n"
            f"Dustingiz qoshilishini kuting..."
        )

    await callback.answer()

@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    try:
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
                    p1_name = duel["player1_name"]
                    if s1 > s2:
                        result = f"Golib: {p1_name}!\n{p1_name}: {s1} | Raqib: {s2}"
                    elif s2 > s1:
                        result = f"Golib: Raqibingiz!\n{p1_name}: {s1} | Raqib: {s2}"
                    else:
                        result = f"Durang!\nIkkalangiz: {s1}"
                    await bot.send_message(duel["player1_id"], f"Oyin tugadi!\n\n{result}")
                    await bot.send_message(duel["player2_id"], f"Oyin tugadi!\n\n{result}")
                    del active_duels[duel_id]
                    if duel["player1_id"] in user_duel:
                        del user_duel[duel["player1_id"]]
                    if duel["player2_id"] in user_duel:
                        del user_duel[duel["player2_id"]]
                else:
                    next_word = duel["words"][duel["current_word"]]
                    num = duel["current_word"] + 1
                    await bot.send_message(duel["player1_id"], f"{num}-soz: {next_word['en']}\nOzbekcha tarjimasini yozing:")
                    await bot.send_message(duel["player2_id"], f"{num}-soz: {next_word['en']}\nOzbekcha tarjimasini yozing:")

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
                    f"Notogri!\n\n"
                    f"Togri javob: {correct_answer}\n\n"
                    f"Natija: {score['correct']} togri | {score['wrong']} notogri\n\n"
                    f"Davom etish uchun /flashcard bosing!"
                )
        elif user_states.get(user_id) == "waiting_topic":
            user_states[user_id] = None
            await message.answer("AI javob tayyorlanmoqda...")
            result = ask_ai(
                f"Give a short, simple English explanation about '{text}' "
                f"for Uzbek English learners. Max 5 sentences. "
                f"Then provide 3 key vocabulary words with Uzbek translations."
            )
            await message.answer(f"{text.upper()} haqida:\n\n{result}")
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

async def main():
    init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Botni boshlash"),
        types.BotCommand(command="translate", description="Soz tarjimasi + audio"),
        types.BotCommand(command="topic", description="Mavzu boyicha AI malumot"),
        types.BotCommand(command="wordofday", description="Kunlik yangi soz"),
        types.BotCommand(command="flashcard", description="Soz oyini"),
        types.BotCommand(command="duel", description="Dust bilan bellashuv"),
        types.BotCommand(command="help", description="Yordam"),
    ])
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
