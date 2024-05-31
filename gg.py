import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

# تهيئة البوت
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"  # توكن البوت في تليجرام
bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = InlineKeyboardMarkup()
    api_button = InlineKeyboardButton(text="تبديل API", callback_data="api")
    keyboard.add(api_button)
    bot.send_message(
        message.chat.id, 
        "مرحبًا! يمكنك استخدام الأزرار التالية للتحكم في البوت:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "api":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "أدخل API الجديد:")
        bot.register_next_step_handler(msg, process_api_step)

def process_api_step(message):
    bot.send_message(message.chat.id, "API تم تحديثه بنجاح!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        duration = int(message.text)
        if duration <= 0:
            bot.send_message(message.chat.id, "الرجاء إدخال قيمة صحيحة أكبر من صفر.")
        else:
            bot.send_message(message.chat.id, f"سيتم حذف التطبيق بعد {duration} دقيقة.")
            start_auto_delete(message.chat.id, duration)
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إدخال رقم صحيح.")

def start_auto_delete(chat_id, duration):
    progress = 0
    while progress <= 100:
        send_progress_bar(chat_id, progress)
        progress += 1
        time.sleep(60 * duration / 100)  # يزداد الوقت بنسبة التقدم المتوقعة
    send_result_message(chat_id)

def send_progress_bar(chat_id, progress):
    bar = '⬜' * (progress // 5) + '⬛' * (20 - progress // 5)
    bot.send_message(chat_id, f"{bar} {progress}%")

def send_result_message(chat_id):
    bot.send_message(chat_id, "تم حذف التطبيق بنجاح!")

bot.polling()
