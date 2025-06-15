import telebot
from telebot import types
import os
import json
from datetime import datetime
import threading
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "user_data.json"

# تحميل أو تهيئة البيانات
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

# حفظ البيانات
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

# تحديث النقاط يومياً
def daily_reset():
    while True:
        now = datetime.utcnow().strftime("%Y-%m-%d")
        for uid in user_data:
            user_data[uid]["date"] = now
            user_data[uid]["count"] = 0
        save_data()
        time.sleep(86400)

threading.Thread(target=daily_reset, daemon=True).start()

student_lookup = {}

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👀 تخيّل صورتك تتعدّل بثواني…\n"
        "💋 تقدر تشوفها بدون ملابس، أو بملامح أحلى.\n"
        "📸 أرسل صورة الآن وخلّنا نبدأ...\n\n"
        "👀 Imagine your photo transformed in seconds…\n"
        "💋 See it with no clothes, or with enhanced features.\n"
        "📸 Send a photo now... let’s get started.")

# عند إرسال صورة من الطالب
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = str(message.chat.id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    user = user_data.get(uid, {"date": today, "count": 0})

    if user["date"] != today:
        user = {"date": today, "count": 0}

    if user["count"] >= 3:
        bot.send_message(message.chat.id, "🚫 استهلكت الحد اليومي (3 صور). جرّب غدًا.")
        return

    user["count"] += 1
    user_data[uid] = user
    save_data()

    remaining = 3 - user["count"]
    bot.send_message(message.chat.id, f"✅ تم استلام الصورة. تبقّى لديك {remaining} صور اليوم.")

    # خيارات وهمية
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس 🔞 / Remove Clothes", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه 💄 / Edit Face", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة 📸 / Enhance Photo", callback_data="quality"))

    bot.send_message(message.chat.id,
        "اختر نوع التعديل المطلوب (لن يتم تنفيذ أي تعديل حقيقي):",
        reply_markup=markup)

    try:
        photo_file_id = message.photo[-1].file_id
        caption = f"📥 صورة جديدة من الطالب: {message.from_user.first_name}\nID: {message.chat.id}"
        sent = bot.send_photo(ADMIN_ID, photo_file_id, caption=caption)
        student_lookup[sent.message_id] = message.chat.id
    except Exception as e:
        print(f"❌ فشل إرسال للمشرف: {e}")

# رد المشرف على صورة
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message is not None)
def reply_to_student(message):
    msg_id = message.reply_to_message.message_id
    student_id = student_lookup.get(msg_id)

    if student_id:
        bot.send_message(student_id, f"📩 رسالة من المشرف:\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ تم إرسال ردك للطالب.")
    else:
        bot.send_message(ADMIN_ID, "❗ لم يتم العثور على الطالب.")

# رد يدوي
@bot.message_handler(commands=['رد'])
def manual_reply(message):
    if message.chat.id != ADMIN_ID:
        return

    args = message.text.split(" ", 2)
    if len(args) < 3:
        bot.send_message(ADMIN_ID, "❗ استخدم الصيغة:\n/رد ID الرسالة")
        return

    try:
        student_id = int(args[1])
        bot.send_message(student_id, f"📩 رسالة من المشرف:\n{args[2]}")
        bot.send_message(ADMIN_ID, "✅ تم إرسال الرسالة.")
    except:
        bot.send_message(ADMIN_ID, "⚠️ فشل الإرسال. تأكد من ID الطالب.")

# ردود الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.send_message(call.message.chat.id,
        "*⚠️ تحذير أخلاقي وقانوني / Ethical & Legal Warning ⚠️*\n\n"
        "لقد حاولت استخدام خاصية \"إزالة الملابس\" – هذا سلوك مرفوض تمامًا ❌\n"
        "You attempted to use the 'Remove Clothes' feature – this is completely unacceptable ❌\n\n"
        "📛 يُعتبر هذا تعدّي على خصوصية الآخرين، ويخضع للملاحقة القانونية.\n"
        "This is a violation of privacy and may result in legal consequences 📛\n\n"
        "هذا البوت محاكاة توعوية فقط، ولا يقوم بأي تعديل فعلي 🧠\n"
        "This bot is for awareness simulation only. No actual editing is performed 🧠\n\n"
        "⚠️ لا ترسل صورك لأي جهة مجهولة أو غير موثوقة.\n"
        "Do not share your photos with any unknown or untrusted service ⚠️\n\n"
        "🚫 تم إنهاء المحاكاة.\nSimulation ended 🚫",
        parse_mode="Markdown")

print("✅ Bot is running...")
bot.polling()
