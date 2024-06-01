import os
import telebot
import requests

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
heroku_api_key = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"  # مفتاح API الخاص بـ Heroku

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'
HEROKU_HEADERS = {
    'Authorization': f'Bearer {heroku_api_key}',
    'Accept': 'application/vnd.heroku+json; version=3'
}

# دالة لإنشاء الأزرار وتخصيصها
def create_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("اضغط هنا", callback_data="show_id1")
    button2 = telebot.types.InlineKeyboardButton("جلب تطبيقات هيروكو", callback_data="list_heroku_apps")
    markup.add(button1, button2)
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_button())

# دالة لجلب تطبيقات هيروكو
def list_heroku_apps(message):
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.send_message(message.chat.id, f"التطبيقات المتاحة في هيروكو:\n{apps_list}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "حدث خطأ في جلب التطبيقات من هيروكو.")

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "show_id1":
        user_id = call.message.chat.id
        bot.send_message(call.message.chat.id, f"معرف المستخدم هو: `{user_id}`", parse_mode='Markdown')
    elif call.data == "list_heroku_apps":
        list_heroku_apps(call.message)

# التشغيل
if __name__ == "__main__":
    bot.polling()
