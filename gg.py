import os
import telebot

# استيراد توكن البوت من المتغيرات البيئية
bot_token ="7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# دالة لإنشاء الزر وتخصيصه
def create_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("اضغط هنا", callback_data="test_button")
    markup.add(button)
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الزر لإرسال رسالة تجريبية.", reply_markup=create_button())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "test_button":
        bot.send_message(call.message.chat.id, "تم الضغط على الزر بنجاح!")

# التشغيل
if __name__ == "__main__":
    bot.polling()
