import telebot
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:"
    )

@bot.message_handler(commands=['deploy'])
def deploy_repo(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع في GitHub الذي تريد نشره على Heroku:")
    bot.register_next_step_handler(msg, process_deploy_repo_step)

def process_deploy_repo_step(message):
    repo_name = message.text
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repo_data = response.json()
        repo_url = repo_data['html_url']
        msg = bot.send_message(message.chat.id, f"تم العثور على المستودع {repo_name} على GitHub. أرسل اسم التطبيق الذي تريد إنشاؤه على Heroku:")
        bot.register_next_step_handler(msg, lambda msg: create_app_and_deploy(repo_name, msg.text, repo_url, message.chat.id))
    else:
        bot.send_message(message.chat.id, f"❌ المستودع {repo_name} غير موجود على GitHub.")

def create_app_and_deploy(repo_name, app_name, repo_url, chat_id):
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if response.status_code == 201:
        bot.send_message(chat_id, f"تم إنشاء التطبيق {app_name} بنجاح على Heroku. جارٍ النشر...")
        message = bot.send_message(chat_id, "⬜⬛⬛⬛⬛⬛⬛⬛⬛⬛: 0%")
        app_url = f'https://{app_name}.herokuapp.com'
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
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء إنشاء التطبيق على Heroku.")

bot.polling()
