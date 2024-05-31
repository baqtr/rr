import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import zipfile
import base64
import time

# تهيئة البوت
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"  # توكن البوت في تليجرام
heroku_api_key = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"  # مفتاح API الخاص بـ Heroku
github_token = "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"  # توكن GitHub
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

def send_heroku_apps(chat_id, repo_name, repo_url):
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        keyboard = InlineKeyboardMarkup()
        for app in apps:
            app_name = app['name']
            callback_data = f"deploy_{repo_name}_{app_name}_{repo_url}"
            button = InlineKeyboardButton(text=app_name, callback_data=callback_data)
            keyboard.add(button)
        bot.send_message(chat_id, "اختر التطبيق الذي تريد نشر المستودع عليه:", reply_markup=keyboard)
    else:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء جلب قائمة التطبيقات من Heroku.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = InlineKeyboardMarkup()
    deploy_button = InlineKeyboardButton(text="نشر مستودع GitHub على Heroku", callback_data="deploy")
    keyboard.add(deploy_button)
    bot.send_message(
        message.chat.id, 
        "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "deploy":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "أدخل اسم المستودع في GitHub الذي تريد نشره على Heroku:")
        bot.register_next_step_handler(msg, process_deploy_repo_step)
    elif call.data.startswith("deploy"):
        repo_name, app_name, repo_url = call.data.split("_")[1:]
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"جارٍ نشر المستودع {repo_name} على التطبيق {app_name}...")
        deploy_repo_to_heroku(repo_name, app_name, repo_url, call.message.chat.id)

def process_deploy_repo_step(message):
    repo_name = message.text
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repo_data = response.json()
        repo_url = repo_data['html_url']
        send_heroku_apps(message.chat.id, repo_name, repo_url)
    else:
        bot.send_message(message.chat.id, f"❌ المستودع {repo_name} غير موجود على GitHub.")

def deploy_repo_to_heroku(repo_name, app_name, repo_url, chat_id):
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps/{app_name}/builds',
        headers=HEROKU_HEADERS,
        json={"source_blob": {"url": f'{repo_url}/archive/refs/heads/main.zip'}}
    )
    if response.status_code == 201:
        bot.send_message(chat_id, f"✅ تم نشر المستودع {repo_name} بنجاح على التطبيق {app_name} في Heroku!")
    else:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء عملية النشر.")

bot.polling()
