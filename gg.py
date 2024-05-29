import telebot
import requests
import os
import random
import zipfile
from io import BytesIO
import base64

# إعدادات البوت
bot_token = '6595406565:AAElCKv4vu_J_RpUIqha_XKS7FTCmPXn2WE'  # استبدل توكن البوت هنا
heroku_api_key = 'HRKU-55457b4c-efd0-4bde-85f3-00195e76dc77'  # استبدل توكن هيروكو هنا
github_token = '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'  # استبدل توكن GitHub هنا

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

GITHUB_USER = 'raed052'  # اسم المستخدم الموحد

# إعداد الأوامر للقائمة الجانبية
commands = [
    telebot.types.BotCommand("/start", "بدء البوت"),
    telebot.types.BotCommand("/heroku_apps", "عرض التطبيقات في هيروكو"),
    telebot.types.BotCommand("/github_repos", "عرض مستودعات GitHub"),
    telebot.types.BotCommand("/create_heroku_app", "إنشاء تطبيق جديد في هيروكو"),
    telebot.types.BotCommand("/delete_heroku_app", "حذف تطبيق في هيروكو"),
    telebot.types.BotCommand("/create_github_repo", "إنشاء مستودع جديد في GitHub"),
    telebot.types.BotCommand("/delete_github_repo", "حذف مستودع في GitHub"),
    telebot.types.BotCommand("/upload_files", "تحميل ملفات إلى مستودع GitHub"),
    telebot.types.BotCommand("/delete_files", "حذف ملفات من مستودع GitHub"),
    telebot.types.BotCommand("/deploy", "نشر كود إلى هيروكو")
]

bot.set_my_commands(commands)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:\n"
                          "/heroku_apps - عرض التطبيقات في هيروكو\n"
                          "/github_repos - عرض مستودعات GitHub\n"
                          "/create_heroku_app - إنشاء تطبيق جديد في هيروكو\n"
                          "/delete_heroku_app - حذف تطبيق في هيروكو\n"
                          "/create_github_repo - إنشاء مستودع جديد في GitHub\n"
                          "/delete_github_repo - حذف مستودع في GitHub\n"
                          "/upload_files - تحميل ملفات إلى مستودع GitHub\n"
                          "/delete_files - حذف ملفات من مستودع GitHub\n"
                          "/deploy - نشر كود إلى هيروكو")

@bot.message_handler(commands=['heroku_apps'])
def list_heroku_apps(message):
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.reply_to(message, f"التطبيقات المتاحة في هيروكو:\n{apps_list}", parse_mode='Markdown')
    else:
        bot.reply_to(message, "حدث خطأ في جلب التطبيقات من هيروكو.")

@bot.message_handler(commands=['github_repos'])
def list_github_repos(message):
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repos = response.json()
        repos_list = "\n".join([f"`{repo['name']}`" for repo in repos])
        bot.reply_to(message, f"المستودعات المتاحة في GitHub:\n{repos_list}", parse_mode='Markdown')
    else:
        bot.reply_to(message, "حدث خطأ في جلب المستودعات من GitHub.")

@bot.message_handler(commands=['create_heroku_app'])
def create_heroku_app(message):
    msg = bot.reply_to(message, "أدخل اسم التطبيق الجديد في هيروكو:")
    bot.register_next_step_handler(msg, process_create_heroku_app_step)

def process_create_heroku_app_step(message):
    app_name = message.text
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if response.status_code == 201:
        bot.reply_to(message, f"تم إنشاء التطبيق `{app_name}` بنجاح في هيروكو.", parse_mode='Markdown')
    elif response.status_code == 422:
        bot.reply_to(message, "الاسم موجود بالفعل، يرجى اختيار اسم آخر.")
    else:
        bot.reply_to(message, "حدث خطأ أثناء إنشاء التطبيق في هيروكو.")

@bot.message_handler(commands=['delete_heroku_app'])
def delete_heroku_app(message):
    msg = bot.reply_to(message, "أدخل اسم التطبيق الذي تريد حذفه من هيروكو:")
    bot.register_next_step_handler(msg, process_delete_heroku_app_step)

def process_delete_heroku_app_step(message):
    app_name = message.text
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 200 or response.status_code == 202:
        bot.reply_to(message, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "حدث خطأ أثناء حذف التطبيق من هيروكو.")

@bot.message_handler(commands=['create_github_repo'])
def create_github_repo(message):
    msg = bot.reply_to(message, "أدخل اسم المستودع الجديد في GitHub:")
    bot.register_next_step_handler(msg, process_github_repo_visibility_step)

def process_github_repo_visibility_step(message):
    repo_name = message.text
    msg = bot.reply_to(message, "هل تريد أن يكون المستودع خاصًا؟ (نعم/لا):")
    bot.register_next_step_handler(msg, process_create_github_repo_step, repo_name)

def process_create_github_repo_step(message, repo_name):
    is_private = message.text.lower() in ['نعم', 'yes']
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{GITHUB_USER}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 404:
        response = requests.post(
            f'{GITHUB_BASE_URL}/user/repos',
            headers=GITHUB_HEADERS,
            json={"name": repo_name, "private": is_private}
        )
        if response.status_code == 201:
            bot.reply_to(message, f"تم إنشاء المستودع `{repo_name}` بنجاح في GitHub.", parse_mode='Markdown')
        else:
            bot.reply_to(message, "حدث خطأ أثناء إنشاء المستودع في GitHub.")
    else:
        bot.reply_to(message, "الاسم موجود بالفعل، يرجى اختيار اسم آخر.")

@bot.message_handler(commands=['delete_github_repo'])
def delete_github_repo(message):
    msg = bot.reply_to(message, "أدخل اسم المستودع الذي تريد حذفه من GitHub:")
    bot.register_next_step_handler(msg, process_delete_github_repo_step)

def process_delete_github_repo_step(message):
    repo_name = message.text
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{GITHUB_USER}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 204:
        bot.reply_to(message, f"تم حذف المستودع `{repo_name}` بنجاح من GitHub.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "حدث خطأ أثناء حذف المستودع من GitHub.")

@bot.message_handler(commands=['upload_files'])
def upload_files_to_github(message):
    msg = bot.reply_to(message, "أدخل اسم المستودع:")
    bot.register_next_step_handler(msg, process_upload_files_step)

def process_upload_files_step(message):
    global repo_name
    repo_name = message.text
    msg = bot.reply_to(message, "قم بإرسال الملف أو الملفات التي تريد تحميلها:")
    bot.register_next_step_handler(msg, process_file_upload)

def process_file_upload(message):
    try:
        if message.document:
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            file = requests.get(f'https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}')
            
            if file_info.file_path.endswith('.zip'):
                zip_file = zipfile.ZipFile(BytesIO(file.content))
                for file_name in zip_file.namelist():
                    with zip_file.open(file_name) as file:
                        content = file.read()
                        upload_file_to_github(file_name, content, message)
            else:
                file_name = message.document.file_name
                content = file.content
                upload_file_to_github(file_name, content, message)
        else:
            bot.reply_to(message, "الرجاء إرسال ملف صالح.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء معالجة الملف: {str(e)}")

def upload_file_to_github(file_name, content, message):
    try:
        encoded_content = base64.b64encode(content).decode('utf-8')
        response = requests.put(
            f'{GITHUB_BASE_URL}/repos/{GITHUB_USER}/{repo_name}/contents/{file_name}',
            headers=GITHUB_HEADERS,
            json={"message": f"Upload {file_name}", "content": encoded_content}
        )
        if response.status_code == 201:
            bot.reply_to(message, f"تم تحميل الملف {file_name} بنجاح إلى GitHub.")
        elif response.status_code == 422:
            bot.reply_to(message, "الاسم موجود بالفعل، يرجى اختيار اسم آخر.")
        else:
            bot.reply_to(message, f"حدث خطأ أثناء تحميل الملف {file_name} إلى GitHub.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء تحميل الملف: {str(e)}")

@bot.message_handler(commands=['delete_files'])
def delete_files_from_github(message):
    msg = bot.reply_to(message, "أدخل اسم المستودع واسم الملف الذي تريد حذفه (بصيغة: repo_name/file_path):")
    bot.register_next_step_handler(msg, process_delete_file_step)

def process_delete_file_step(message):
    try:
        repo_name, file_path = message.text.split('/')
        response = requests.get(f'{GITHUB_BASE_URL}/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}', headers=GITHUB_HEADERS)
        if response.status_code == 200:
            sha = response.json()['sha']
            response = requests.delete(
                f'{GITHUB_BASE_URL}/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}',
                headers=GITHUB_HEADERS,
                json={"message": f"Delete {file_path}", "sha": sha}
            )
            if response.status_code == 200:
                bot.reply_to(message, f"تم حذف الملف {file_path} بنجاح من GitHub.")
            else:
                bot.reply_to(message, f"حدث خطأ أثناء حذف الملف {file_path} من GitHub.")
        else:
            bot.reply_to(message, "الملف غير موجود في المستودع.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {str(e)}")

@bot.message_handler(commands=['deploy'])
def deploy_to_heroku(message):
    msg = bot.reply_to(message, "أدخل اسم التطبيق في هيروكو واسم المستودع في GitHub (بصيغة: heroku_app_name github_repo_name):")
    bot.register_next_step_handler(msg, process_deploy_step)

def process_deploy_step(message):
    try:
        heroku_app_name, github_repo_name = message.text.split()
        response = requests.post(
            f'{HEROKU_BASE_URL}/apps/{heroku_app_name}/builds',
            headers=HEROKU_HEADERS,
            json={"source_blob": {"url": f"https://github.com/{GITHUB_USER}/{github_repo_name}/tarball/main"}}
        )
        if response.status_code == 201:
            bot.reply_to(message, "تم نشر الكود بنجاح إلى هيروكو.")
        else:
            bot.reply_to(message, "حدث خطأ أثناء نشر الكود إلى هيروكو.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {str(e)}")

bot.polling()
