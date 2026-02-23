import asyncio
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from gtts import gTTS
from deep_translator import GoogleTranslator
from groq import Groq

# Tokenlar
BOT_TOKEN = "8460732938:AAEXxdsq7uzI9VwgKEIWCAbRUcwMw2crwaw"
GROQ_KEY = "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"
ADMIN_ID = 6202785302  # @userinfobot dan oling

# Groq sozlash
groq_client = Groq(api_key=GROQ_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Foydalanuvchi holatlari
user_states = {}
user_scores = {}
user_current_word = {}
users_db = set()

# AI dan javob olish
def ask_ai(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

# Darajali flashcard so'zlari
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

# /start komandasi
@dp.message(Command("start"))
async def start(message: types.Message):
    users_db.add(message.from_user.id)
    name = message.from_user.first_name
    await message.answer(
        f"Salom, {name}! 👋\n\n"
        "Men ingliz tili o'rganishga yordam beraman! 🇬🇧\n\n"
        "📌 Mening imkoniyatlarim:\n"
        "/translate — So'z tarjimasi + audio\n"
        "/topic — Mavzu bo'yicha AI ma'lumot\n"
        "/wordofday — Kunlik yangi so'z\n"
        "/flashcard — So'z o'yini\n"
        "/help — Yordam"
    )

# /help komandasi
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "🆘 Yordam:\n\n"
        "/translate — So'z yoki jumla yuboring, tarjima + audio olasiz\n"
        "/topic — Mavzu yozing, AI ma'lumot beradi\n"
        "/wordofday — Bugungi yangi so'z\n"
        "/flashcard — So'z o'yini, darajali\n"
    )

# /translate komandasi
@dp.message(Command("translate"))
async def translate_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_translate"
    await message.answer("🔤 Inglizcha yoki o'zbekcha so'z yuboring:")

# /topic komandasi
@dp.message(Command("topic"))
async def topic_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_topic"
    await message.answer("🧠 Qaysi mavzuda inglizcha ma'lumot olmoqchisiz?\n\nMasalan: sport, food, technology, nature")

# /wordofday komandasi
@dp.message(Command("wordofday"))
async def word_of_day(message: types.Message):
    await message.answer("⏳ Kunlik so'z tayyorlanmoqda...")
    try:
        result = ask_ai(
            "Give me one interesting English word for Uzbek learners. "
            "Format:\nWord: ...\nTranslation (Uzbek): ...\nExample sentence: ...\nPronunciation tip: ..."
        )
        await message.answer(f"📅 Bugungi so'z:\n\n{result}")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")

# /users komandasi — faqat admin
@dp.message(Command("users"))
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bu komanda faqat admin uchun!")
        return
    await message.answer(
        f"👥 Botdan foydalanganlar soni: {len(users_db)} ta\n\n"
        f"ID lar:\n" + "\n".join(str(u) for u in users_db)
    )

# /flashcard komandasi
@dp.message(Command("flashcard"))
async def flashcard_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = None
    await message.answer(
        "🎯 Qaysi darajani tanlaysiz?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🟢 Oson", callback_data="level_easy"),
                types.InlineKeyboardButton(text="🟡 O'rta", callback_data="level_medium"),
                types.InlineKeyboardButton(text="🔴 Qiyin", callback_data="level_hard"),
            ]
        ])
    )

# Daraja tanlanganda
@dp.callback_query()
async def level_chosen(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    level = callback.data.replace("level_", "")

    level_names = {"easy": "🟢 Oson", "medium": "🟡 O'rta", "hard": "🔴 Qiyin"}

    last_word = user_current_word.get(user_id)
    available_words = [w for w in flashcard_words[level] if w != last_word]
    word = random.choice(available_words)

    user_current_word[user_id] = word
    user_states[user_id] = f"waiting_flashcard_{level}"

    if user_id not in user_scores:
        user_scores[user_id] = {"correct": 0, "wrong": 0}

    await callback.message.answer(
        f"🃏 Daraja: {level_names[level]}\n\n"
        f"🇬🇧 Inglizcha so'z: *{word['en']}*\n\n"
        f"O'zbekcha tarjimasini yozing:",
        parse_mode="Markdown"
    )
    await callback.answer()

# Foydalanuvchi matn yuborganda
@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    user_id = message.from_user.id

    try:
        if user_states.get(user_id, "").startswith("waiting_flashcard"):
            level = user_states[user_id].replace("waiting_flashcard_", "")
            user_states[user_id] = None
            word = user_current_word.get(user_id)
            correct_answer = word["uz"].lower()
            user_answer = text.lower().strip()

            if user_answer == correct_answer:
                user_scores[user_id]["correct"] += 1
                score = user_scores[user_id]
                await message.answer(
                    f"✅ To'g'ri! Barakalla! 🎉\n\n"
                    f"🏆 Natija: {score['correct']} to'g'ri | {score['wrong']} noto'g'ri\n\n"
                    f"Davom etish uchun /flashcard bosing!"
                )
            else:
                user_scores[user_id]["wrong"] += 1
                score = user_scores[user_id]
                await message.answer(
                    f"❌ Noto'g'ri!\n\n"
                    f"✅ To'g'ri javob: *{correct_answer}*\n\n"
                    f"🏆 Natija: {score['correct']} to'g'ri | {score['wrong']} noto'g'ri\n\n"
                    f"Davom etish uchun /flashcard bosing!",
                    parse_mode="Markdown"
                )

        elif user_states.get(user_id) == "waiting_topic":
            user_states[user_id] = None
            await message.answer("⏳ AI javob tayyorlanmoqda...")
            result = ask_ai(
                f"Give a short, simple English explanation about '{text}' "
                f"for Uzbek English learners. Max 5 sentences. "
                f"Then provide 3 key vocabulary words with Uzbek translations."
            )
            await message.answer(f"🧠 {text.upper()} haqida:\n\n{result}")

        else:
            detected = GoogleTranslator(source='auto', target='en').translate(text)

            if detected.lower() != text.lower():
                await message.answer(f"🇺🇿 O'zbekcha: {text}\n🇬🇧 Inglizcha: {detected}")
                tts = gTTS(text=detected, lang='en')
            else:
                translated = GoogleTranslator(source='en', target='uz').translate(text)
                await message.answer(f"🇬🇧 Inglizcha: {text}\n🇺🇿 O'zbekcha: {translated}")
                tts = gTTS(text=text, lang='en')

            audio_file = "audio.mp3"
            tts.save(audio_file)
            await message.answer_voice(types.FSInputFile(audio_file))
            os.remove(audio_file)

    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")

# Botni ishga tushirish
async def main():
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Botni boshlash"),
        types.BotCommand(command="translate", description="So'z tarjimasi + audio"),
        types.BotCommand(command="topic", description="Mavzu bo'yicha AI ma'lumot"),
        types.BotCommand(command="wordofday", description="Kunlik yangi so'z"),
        types.BotCommand(command="flashcard", description="So'z o'yini — darajali"),
        types.BotCommand(command="help", description="Yordam"),
    ])
    print("Bot ishga tushdi! ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())