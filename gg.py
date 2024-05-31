import telebot
import requests
import os
import zipfile
import base64
import threading
from datetime import datetime, timedelta

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
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('⚙️ قسم هيروكو', callback_data='heroku_section')
    itembtn2 = telebot.types.InlineKeyboardButton('🗃️ قسم GitHub', callback_data='github_section')
    itembtn3 = telebot.types.InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/q_w_c')
    markup.add(itembtn1, itembtn2)
    markup.add(itembtn3)
    return markup

def create_heroku_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('📋 عرض التطبيقات في هيروكو', callback_data='list_heroku_apps')
    itembtn2 = telebot.types.InlineKeyboardButton('➕ إنشاء تطبيق جديد في هيروكو', callback_data='create_heroku_app')
    itembtn3 = telebot.types.InlineKeyboardButton('🗑️ حذف تطبيق في هيروكو', callback_data='prompt_delete_heroku_app')
    itembtn4 = telebot.types.InlineKeyboardButton('🚀 نشر كود إلى هيروكو', callback_data='deploy_to_heroku')
    itembtn5 = telebot.types.InlineKeyboardButton('🔙 العودة', callback_data='back_to_main')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    markup.add(itembtn5)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:", 
        reply_markup=create_main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'heroku_section':
        bot.edit_message_text(
            "قسم هيروكو:", 
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_heroku_menu()
        )
    elif call.data == 'github_section':
        bot.edit_message_text(
            "قسم GitHub:", 
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_github_menu()
        )
    elif call.data == 'list_heroku_apps':
        list_heroku_apps(call.message)
    elif call.data == 'list_github_repos':
        list_github_repos(call.message)
    elif call.data == 'create_heroku_app':
        prompt_for_heroku_app_name(call.message)
    elif call.data == 'prompt_delete_heroku_app':
        prompt_for_heroku_app_deletion_method(call.message)
    elif call.data == 'create_github_repo':
        prompt_for_github_repo_name(call.message)
    elif call.data == 'delete_github_repo':
        prompt_for_github_repo_to_delete(call.message)
    elif call.data == 'upload_files_to_github':
        prompt_for_github_repo_for_upload(call.message)
    elif call.data == 'delete_files_from_github':
        prompt_for_github_repo_for_delete(call.message)
    elif call.data == 'deploy_to_heroku':
        prompt_for_github_repo_for_deploy(call.message)
    elif call.data == 'back_to_main':
        bot.edit_message_text(
            "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:", 
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            replymarkup=create_main_menu()
        )

def list_heroku_apps(message):
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.send_message(message.chat.id, f"التطبيقات المتواجدة في هيروكو:\n{apps_list}", parse_mode='Markdown', reply_markup=create_heroku_menu())
    else:
        bot.send_message(message.chat.id, "حدث خطأ في جلب التطبيقات من هيروكو.", reply_markup=create_heroku_menu())

def list_github_repos(message):
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repos = response.json()
        repos_list = "\n".join([f"`{repo['name']}`" for repo in repos])
        bot.send_message(message.chat.id, f"المستودعات المتاحة في GitHub:\n{repos_list}", parse_mode='Markdown', reply_markup=create_github_menu())
    else:
        bot.send_message(message.chat.id, "حدث خطأ في جلب المستودعات من GitHub.", reply_markup=create_github_menu())

def prompt_for_heroku_app_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الجديد في هيروكو:")
    bot.register_next_step_handler(msg, process_create_heroku_app_step)

def process_create_heroku_app_step(message):
    app_name = message.text
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if response.status_code == 201:
        bot.send_message(message.chat.id, f"تم إنشاء التطبيق `{app_name}` بنجاح في هيروكو.", parse_mode='Markdown', reply_markup=create_heroku_menu())
    elif response.status_code == 422:
        bot.send_message(message.chat.id, "الاسم موجود بالفعل، يرجى اختيار اسم آخر.", reply_markup=create_heroku_menu())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء إنشاء التطبيق في هيروكو.", reply_markup=create_heroku_menu())

def prompt_for_heroku_app_deletion_method(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    itembtn1 = telebot.types.InlineKeyboardButton('حذف ذاتي مع المؤقت', callback_data='auto_delete_heroku_app')
    itembtn2 = telebot.types.InlineKeyboardButton('حذف عادي', callback_data='regular_delete_heroku_app')
    itembtn3 = telebot.types.InlineKeyboardButton('🔙 العودة', callback_data='back_to_main')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.edit_message_text(
        "يرجى اختيار طريقة الحذف:", 
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=markup
    )

def prompt_for_heroku_app_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الذي تريد حذفه من هيروكو:")
    bot.register_next_step_handler(msg, process_delete_heroku_app_step)

def process_delete_heroku_app_step(message):
    app_name = message.text
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 200 or response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", parse_mode='Markdown', reply_markup=create_heroku_menu())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف التطبيق من هيروكو.", reply_markup=create_heroku_menu())

def auto_delete_heroku_app(app_name, time_to_delete):
    time_to_delete = int(time_to_delete)
    threading.Timer(time_to_delete * 60,delete_heroku_app, args=[app_name]).start()

def delete_heroku_app(app_name):
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 200 or response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", parse_mode='Markdown', reply_markup=create_heroku_menu())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف التطبيق من هيروكو.", reply_markup=create_heroku_menu())

def prompt_for_heroku_auto_delete_time(message):
    msg = bot.send_message(message.chat.id, "أدخل الوقت بالدقائق بعد الذي تريد حذف التطبيق:")
    bot.register_next_step_handler(msg, process_heroku_auto_delete_time)

def process_heroku_auto_delete_time(message):
    time_to_delete = message.text
    app_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل الوقت بالدقائق بعد الذي تريد حذف التطبيق:")
    bot.register_next_step_handler(msg, auto_delete_heroku_app, app_name, time_to_delete)

def prompt_for_github_repo_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الجديد في GitHub:")
    bot.register_next_step_handler(msg, process_github_repo_visibility_step)

def process_github_repo_visibility_step(message, repo_name):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "هل تريد أن يكون المستودع خاصًا؟ (نعم/لا):")
    bot.register_next_step_handler(msg, process_create_github_repo_step, repo_name)

def process_create_github_repo_step(message, repo_name):
    is_private = message.text.lower() in ['نعم', 'yes']
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 404:
        response = requests.post(
            f'{GITHUB_BASE_URL}/user/repos',
            headers=GITHUB_HEADERS,
            json={"name": repo_name, "private": is_private}
        )
        if response.status_code == 201:
            bot.send_message(message.chat.id, f"تم إنشاء المستودع `{repo_name}` بنجاح في GitHub.", parse_mode='Markdown', reply_markup=create_github_menu())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء إنشاء المستودع في GitHub.", reply_markup=create_github_menu())
    else:
        bot.send_message(message.chat.id, "اسم المستودع موجود بالفعل، يرجى اختيار اسم آخر.", reply_markup=create_github_menu())

def prompt_for_github_repo_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذفه من GitHub:")
    bot.register_next_step_handler(msg, process_delete_github_repo_step)

def process_delete_github_repo_step(message):
    repo_name = message.text
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 204:
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح من GitHub.", parse_mode='Markdown', reply_markup=create_github_menu())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف المستودع من GitHub.", reply_markup=create_github_menu())

def prompt_for_github_repo_for_upload(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد تحميل الملفات إليه:")
    bot.register_next_step_handler(msg, process_upload_files_step)

def process_upload_files_step(message):
    global repo_name
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أرسل الملفات التي تريد تحميلها:")
    bot.register_next_step_handler(msg, receive_files)

def receive_files(message):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name
        encoded_content = base64.b64encode(downloaded_file).decode()
        response = requests.put(
            f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_name}',
            headers=GITHUB_HEADERS,
            json={
                "message": f"Uploading {file_name}",
                "content": encoded_content
            }
        )
        if response.status_code== 201:
            bot.send_message(message.chat.id, f"تم تحميل الملف `{file_name}` بنجاح إلى المستودع `{repo_name}` على GitHub.", parse_mode='Markdown', reply_markup=create_github_menu())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء تحميل الملف إلى المستودع على GitHub.", reply_markup=create_github_menu())
    else:
        bot.send_message(message.chat.id, "يرجى إرسال ملف.", reply_markup=create_github_menu())

def prompt_for_github_repo_for_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذف الملفات منه:")
    bot.register_next_step_handler(msg, process_repo_for_files_deletion)

def process_repo_for_files_deletion(message):
    global repo_name
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل اسم الملف الذي تريد حذفه:")
    bot.register_next_step_handler(msg, process_delete_files_step)

def process_delete_files_step(message):
    global file_name
    file_name = message.text
    response = requests.get(
        f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_name}',
        headers=GITHUB_HEADERS
    )
    if response.status_code == 200:
        content = response.json()
        response = requests.delete(
            f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_name}',
            headers=GITHUB_HEADERS,
            json={
                "message": f"Deleting {file_name}",
                "sha": content['sha']
            }
        )
        if response.status_code == 200:
            bot.send_message(message.chat.id, f"تم حذف الملف `{file_name}` بنجاح من المستودع `{repo_name}` على GitHub.", parse_mode='Markdown', reply_markup=create_github_menu())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء حذف الملف من المستودع على GitHub.", reply_markup=create_github_menu())
    else:
        bot.send_message(message.chat.id, f"الملف `{file_name}` غير موجود في المستودع `{repo_name}` على GitHub.", parse_mode='Markdown', reply_markup=create_github_menu())

def prompt_for_github_repo_for_deploy(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد نشره على هيروكو:")
    bot.register_next_step_handler(msg, process_github_repo_for_deploy)

def process_github_repo_for_deploy(message):
    global repo_name_for_deploy
    repo_name_for_deploy = message.text
    msg = bot.send_message(message.chat.id, "أدخل اسم المجلد في المستودع الذي تريد نشر محتواه:")
    bot.register_next_step_handler(msg, process_repo_folder_for_deploy)

def process_repo_folder_for_deploy(message):
    folder_name = message.text
    response = requests.get(
        f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name_for_deploy}/contents/{folder_name}',
        headers=GITHUB_HEADERS
    )
    if response.status_code == 200:
        content = response.json()
        zip_file_path = f'/tmp/{folder_name}.zip'
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for file in content:
                file_content = requests.get(file['download_url']).content
                zip_file.writestr(file['name'], file_content)
        with open(zip_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f'{HEROKU_BASE_URL}/apps/{repo_name_for_deploy}/slug/sources',
                headers=HEROKU_HEADERS,
                files=files
            )
        os.remove(zip_file_path)
        if response.status_code == 202:
            bot.send_message(message.chat.id, f"جارٍ نشر المجلد `{folder_name}` من المستودع `{repo_name_for_deploy}` على Heroku.", parse_mode='Markdown', reply_markup=create_heroku_menu())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء نشر المجلد على Heroku.", reply_markup=create_heroku_menu())
    else:
        bot.send_message(message.chat.id, f"المجلد `{folder_name}` غير موجود في المستودع `{repo_name_for_deploy}` على GitHub.", parse_mode='Markdown', reply_markup=create_heroku_menu())

bot.polling()
