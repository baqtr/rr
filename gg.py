import telebot
import requests
from datetime import datetime

TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"
HEROKU_API_KEY = "HRKU-adaf6ee5-26b0-451f-8425-327ad117b05a"
HEROKU_APPS_URL = "https://api.heroku.com/apps"

bot = telebot.TeleBot(TOKEN)

def get_heroku_apps():
    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": f"Bearer {HEROKU_API_KEY}"
    }
    response = requests.get(HEROKU_APPS_URL, headers=headers)
    if response.status_code == 200:
        apps = response.json()
        return apps
    else:
        return None

def format_creation_time(creation_time):
    now = datetime.now()
    creation_datetime = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%SZ")
    hours_diff = (now - creation_datetime).seconds // 3600
    return hours_diff

@bot.message_handler(commands=['apps'])
def show_apps(message):
    apps = get_heroku_apps()
    if apps:
        markup = telebot.types.InlineKeyboardMarkup()
        for app in apps:
            app_name = app['name']
            creation_time = format_creation_time(app['created_at'])
            emoji = "✅" if creation_time >= 24 else "🕓"
            response = f"{app_name} {emoji}"
            markup.add(telebot.types.InlineKeyboardButton(text=response, callback_data=app_name))
        bot.send_message(message.chat.id, "قائمة التطبيقات:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء جلب معلومات التطبيقات.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, text=f"تم نسخ اسم التطبيق: {call.data}")
    bot.send_message(call.message.chat.id, call.data)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "مرحباً بك! لعرض جميع التطبيقات، ارسل /apps")

bot.polling()
