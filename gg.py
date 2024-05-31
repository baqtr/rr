import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import zipfile
import base64
import time

# تهيئة البوت
bot_token = "YOUR_BOT_TOKEN_HERE"  # توكن البوت في تليجرام
heroku_api_key = "YOUR_HEROKU_API_KEY_HERE"  # مفتاح API الخاص بـ Heroku
github_token = "YOUR_GITHUB_TOKEN_HERE"  # توكن GitHub
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'
HEROKU_HEADERS = {
    'Authorization': f'Bearer {heroku_api_key}',
    'Accept': 'application/vnd.heroku+json; version=3'
}

# GitHub API
GITHUB_BASE_URL = 'https://api.github.com'
GITHUB_HEADERS = {
    'Authorization': f'token {github_token}',
    'Accept': 'application/vnd.github.v3+json'
}

def send_progress_bar(chat_id, message_id, progress):
    # تحويل النسبة إلى عدد الرموز
    num_symbols = int(progress * 10)
    bar = ''.join(['⬜' if i < num_symbols else '⬛' for i in range(10)])
    # إرسال الرسالة مع شريط التقدم
    bot.edit_message_text(f"{bar}: {progress*100:.2f}%", chat_id, message_id)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = InlineKeyboardMarkup()
    repo_button = InlineKeyboardButton(text="اختر مستودع GitHub", callback_data="choose_repo")
    app_button = InlineKeyboardButton(text="اختر تطبيق Heroku", callback_data="choose_app")
    keyboard.row(repo_button, app_button)
    bot.send_message(
        message.chat.id, 
        "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "choose_repo":
        bot.answer_callback_query(call.id)
        repos = get_github_repositories()
        if repos:
            keyboard = InlineKeyboardMarkup()
            for repo in repos:
                repo_button = InlineKeyboardButton(text=repo, callback_data=f"repo_{repo}")
                keyboard.row(repo_button)
            bot.send_message(call.message.chat.id, "اختر المستودع الذي تريد نشره على Heroku:", reply_markup=keyboard)
        else:
            bot.send_message(call.message.chat.id, "❌ لا يوجد مستودعات متاحة على GitHub.")
    elif call.data.startswith("repo_"):
        repo_name = call.data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, f"أدخل اسم التطبيق الذي تريد إنشاؤه على Heroku:")
        bot.register_next_step_handler(msg, lambda msg: create_app_and_deploy(repo_name, msg.text, call.message.chat.id))
    elif call.data == "choose_app":
        bot.answer_callback_query(call.id)
        apps = get_heroku_apps()
        if apps:
            keyboard = InlineKeyboardMarkup()
            for app in apps:
                app_button = InlineKeyboardButton(text=app, callback_data=f"app_{app}")
                keyboard.row(app_button)
            bot.send_message(call.message.chat.id, "اختر التطبيق الذي تريد نشر المستودع عليه:", reply_markup=keyboard)
        else:
            bot.send_message(call.message.chat.id, "❌ لا يوجد تطبيقات متاحة على Heroku.")

def get_github_repositories():
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repos = [repo['name'] for repo in response.json()]
        return repos
    else:
        return None

def get_heroku_apps():
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = [app['name'] for app in response.json()]
        return apps
    else:
        return None

def create_app_and_deploy(repo_name, app_name, chat_id):
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if response.status_code == 201:
        bot.send_message(chat_id, f"تم إنشاء التطبيق {app_name} بنجاح على Heroku. جارٍ النشر...")
        message = bot.send_message(chat_id, "⬜⬛⬛⬛⬛⬛⬛⬛⬛⬛: 0%")
        app_url = f'https://{app_name}.herokuapp.com'
        repo_url = f'https://github.com/{repo_name}'
        repo_zip_url = f'{repo_url}/archive/refs/heads/main.zip'
        repo_zip_response = requests.get(repo_zip_url)
        if repo_zip_response.status_code == 200:
            with open('/tmp/repo.zip', 'wb') as f:
                f.write(repo_zip_response.content)
            deploy_response = requests.post(
                f'{HEROKU_BASE_URL}/apps/{app_name}/slugs',
                headers=HEROKU_HEADERS,
                files={'file': open('/tmp/repo.zip', 'rb')}
            )
            os.remove('/tmp/repo.zip')
            if deploy_response.status_code == 201:
                bot.send_message(chat_id, f"✅ تم نشر التطبيق {app_name} بنجاح على Heroku!")
                bot.send_message(chat_id, f"يمكنك الآن زيارة التطبيق على الرابط التالي: {app_url}")
            else:
                bot.send_message(chat_id, f"❌ حدث خطأ أثناء عملية النشر.")
                bot.delete_message(chat_id, message.message_id)
        else:
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء تنزيل المستودع من GitHub.")
            bot.delete_message(chat_id, message.message_id)
    else:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء إنشاء التطبيك على Heroku."
        bot.delete_message(chat_id, message.message_id)

bot.polling()
