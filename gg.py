import telebot
import requests
import os
import zipfile
import time

# إعدادات البوت
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

def create_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    itembtn1 = telebot.types.KeyboardButton('/start')
    itembtn2 = telebot.types.KeyboardButton('/help')
    itembtn3 = telebot.types.KeyboardButton('/list_apps')
    markup.add(itembtn1, itembtn2, itembtn3)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "مرحبًا! أرسل اسم المستودع على GitHub الذي تريد نشره على Heroku:",
        reply_markup=create_main_menu()
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
        message.chat.id,
        "الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه القائمة\n"
        "/list_apps - عرض التطبيقات المنشورة في Heroku"
    )

@bot.message_handler(commands=['list_apps'])
def list_heroku_apps(message):
    bot.send_message(message.chat.id, "📋 جارٍ جلب قائمة التطبيقات المنشورة في Heroku...")
    
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"- {app['name']}" for app in apps])
        bot.send_message(message.chat.id, f"📋 التطبيقات المنشورة في Heroku:\n{apps_list}")
    else:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء جلب قائمة التطبيقات من Heroku.")

@bot.message_handler(func=lambda message: True)
def process_github_repo_for_deploy(message):
    repo_name = message.text
    bot.send_message(message.chat.id, f"🔍 جارٍ التحقق من وجود المستودع `{repo_name}` على GitHub...")
    
    response = requests.get(
        f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}',
        headers=GITHUB_HEADERS
    )
    
    if response.status_code == 200:
        msg = bot.send_message(message.chat.id, "✅ المستودع موجود! أدخل اسم التطبيق الذي تريد نشره على Heroku:")
        bot.register_next_step_handler(msg, process_deploy_to_heroku, repo_name)
    else:
        bot.send_message(message.chat.id, "❌ المستودع غير موجود. تأكد من الاسم وحاول مرة أخرى.")

def process_deploy_to_heroku(message, repo_name):
    app_name = message.text
    zip_file_path = f'/tmp/{repo_name}.zip'
    
    bot.send_message(message.chat.id, f"📦 جارٍ تنزيل المستودع `{repo_name}` من GitHub...")
    start_time = time.time()
    
    response = requests.get(
        f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/zipball/main',
        headers=GITHUB_HEADERS
    )
    
    if response.status_code == 200:
        with open(zip_file_path, 'wb') as f:
            f.write(response.content)
        
        elapsed_time = time.time() - start_time
        bot.send_message(message.chat.id, f"📤 تم تنزيل المستودع في {elapsed_time:.2f} ثانية! جارٍ نشره على Heroku كتطبيق `{app_name}`...")
        
        with open(zip_file_path, 'rb') as f:
            files = {'file': f}
            deploy_response = requests.post(
                f'{HEROKU_BASE_URL}/apps/{app_name}/slugs',
                headers=HEROKU_HEADERS,
                files=files
            )
        
        os.remove(zip_file_path)
        
        if deploy_response.status_code == 201:
            bot.send_message(message.chat.id, f"✅ تم نشر المستودع `{repo_name}` بنجاح على Heroku كتطبيق `{app_name}`.")
        else:
            bot.send_message(message.chat.id, "❌ حدث خطأ أثناء نشر المستودع على Heroku.")
    else:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء تنزيل المستودع من GitHub.")

bot.polling()
