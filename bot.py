import sqlite3
import asyncio
import os
import random
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
        {"en": "hand", "uz": "qo'l"},
        {"en": "eye", "uz": "ko'z"},
        {"en": "bread", "uz": "non"},
        {"en": "milk", "uz": "sut"},
        {"en": "egg", "uz": "tuxum"},
        {"en": "tea", "uz": "choy"},
        {"en": "fire", "uz": "olov"},
        {"en": "rain", "uz": "yomg'ir"},
        {"en": "bird", "uz": "qush"},
        {"en": "fish", "uz": "baliq"},
    ],
    "medium": [
        {"en": "school", "uz": "maktab"},
        {"en": "friend", "uz": "do'st"},
        {"en": "bridge", "uz": "ko'prik"},
        {"en": "market", "uz": "bozor"},
        {"en": "hospital", "uz": "kasalxona"},
        {"en": "teacher", "uz": "o'qituvchi"},
        {"en": "student", "uz": "talaba"},
        {"en": "mountain", "uz": "tog'"},
        {"en": "forest", "uz": "o'rmon"},
        {"en": "desert", "uz": "cho'l"},
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
        {"en": "responsible", "uz": "mas'uliyatli"},
        {"en": "independent", "uz": "mustaqil"},
        {"en": "experience", "uz": "tajriba"},
        {"en": "development", "uz": "rivojlanish"},
        {"en": "achievement", "uz": "yutuq"},
        {"en": "imagination", "uz": "tasavvur"},
        {"en": "volunteer", "uz": "ko'ngilli"},
        {"en": "agriculture", "uz": "qishloq xo'jaligi"},
        {"en": "technology", "uz": "texnologiya"},
        {"en": "electricity", "uz": "elektr"},
        {"en": "university", "uz": "universitet"},
        {"en": "competition", "uz": "musobaqa"},
        {"en": "celebration", "uz": "bayram"},
        {"en": "profession", "uz": "kasb"},
    ]
}

@dp.message(Command("start"))
async def start(message: types.Message):
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

@dp.callback_query()
async def level_chosen(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    level = callback.data.replace("level_", "")
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
    await callback.answer()

@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    try:
        if user_states.get(user_id, "").startswith("waiting_flashcard"):
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
            os.remove(audio_file)    except Exception as e:
        await message.answer(f"Xatolik: {str(e)}")
async def main():
    init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Botni boshlash"),
        types.BotCommand(command="translate", description="Soz tarjimasi + audio"),
        types.BotCommand(command="topic", description="Mavzu boyicha AI malumot"),
        types.BotCommand(command="wordofday", description="Kunlik yangi soz"),
        types.BotCommand(command="flashcard", description="Soz oyini"),
        types.BotCommand(command="help", description="Yordam"),
    ])
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
