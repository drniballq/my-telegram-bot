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

# ملف المستخدمين
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
            user_data[uid]["points"] = 3
            user_data[uid]["last_reset"] = now
        save_data()
        time.sleep(86400)

# التحقق من تجديد النقاط
def check_reset(user_id):
    uid = str(user_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if uid not in user_data or user_data[uid].get("last_reset") != today:
        user_data[uid] = {"points": 3, "last_reset": today}
        save_data()

# الحصول على النقاط
def get_points(user_id):
    check_reset(user_id)
    return user_data[str(user_id)]["points"]

# خصم نقطة
def deduct_point(user_id):
    uid = str(user_id)
    user_data[uid]["points"] -= 1
    save_data()

# /start
@bot.message_handler(commands=["start"])
def welcome(msg):
    bot.send_message(msg.chat.id,
        "👋 مرحباً! يمكنك إرسال 3 صور فقط يوميًا.\n"
        "📸 أرسل صورة الآن لبدء التعديل.")

# استقبال الصور
@bot.message_handler(content_types=["photo"])
def handle_photo(msg):
    user_id = msg.chat.id

    if user_id != ADMIN_ID:
        points = get_points(user_id)
        if points <= 0:
            bot.send_message(user_id, "❌ انتهت صورك المجانية اليوم، عد غدًا.")
            return
        elif points == 3:
            bot.send_message(user_id, "✅ لديك 3 صور مجانية اليوم.")
        elif points == 2:
            bot.send_message(user_id, "🟡 تبقّت لك صورتين.")
        elif points == 1:
            bot.send_message(user_id, "🔴 هذه آخر صورة مسموحة اليوم.")
        deduct_point(user_id)

    photo_id = msg.photo[-1].file_id
    bot.send_photo(ADMIN_ID, photo_id, caption=f"📥 من {msg.chat.first_name} ({user_id})")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✉️ رد عليه", callback_data=f"reply_{user_id}"))
    bot.send_message(ADMIN_ID, "📨 اضغط للرد على هذا المستخدم:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_to_user(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(ADMIN_ID, f"🖊 أرسل رسالتك الآن وسيتم إرسالها لـ {user_id}")
    bot.register_next_step_handler_by_chat_id(ADMIN_ID, forward_reply, user_id)

def forward_reply(msg, target_id):
    bot.send_message(target_id, f"📩 رسالة من المشرف:\n{msg.text}")
    bot.send_message(ADMIN_ID, "✅ تم إرسال الرد.")

# رسائل خاطئة
@bot.message_handler(func=lambda m: True, content_types=["text"])
def wrong_type(msg):
    if msg.chat.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "📸 أرسل صورة فقط للاستمرار.")

# تشغيل التحديث اليومي في الخلفية
threading.Thread(target=daily_reset, daemon=True).start()

bot.polling()
