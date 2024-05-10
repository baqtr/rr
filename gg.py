import telebot
import requests
from datetime import datetime

# توكن البوت الخاص بك
TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"

# توكن API الخاص بك من هيروكو
HEROKU_API_KEY = "HRKU-adaf6ee5-26b0-451f-8425-327ad117b05a"

# رابط استعلام التطبيقات على هيروكو
HEROKU_APPS_URL = "https://api.heroku.com/apps"

bot = telebot.TeleBot(TOKEN)

# استعلام قائمة التطبيقات على هيروكو
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

# تنسيق وقت الإنشاء بالساعات
def format_creation_time(creation_time):
    now = datetime.now()
    creation_datetime = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%SZ")
    hours_diff = (now - creation_datetime).seconds // 3600
    return hours_diff

# عرض تفاصيل التطبيقات
@bot.message_handler(commands=['apps'])
def show_apps(message):
    apps = get_heroku_apps()
    if apps:
        for app in apps:
            app_name = app['name']
            creation_time = format_creation_time(app['created_at'])
            response = f"اسم التطبيق: {app_name}\nوقت الإنشاء: {creation_time} ساعة\n"
            bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء جلب معلومات التطبيقات.")

# استقبال الأوامر الأخرى
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "مرحباً بك! لعرض جميع التطبيقات، ارسل /apps")

bot.polling()
