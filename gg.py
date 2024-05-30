import telebot
import requests
import os
import zipfile
import base64

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
    itembtn3 = telebot.types.InlineKeyboardButton('🗑️ حذف تطبيق في هيروكو', callback_data='delete_heroku_app')
    itembtn4 = telebot.types.InlineKeyboardButton('🚀 نشر كود إلى هيروكو', callback_data='deploy_to_heroku')
    itembtn5 = telebot.types.InlineKeyboardButton('🔙 العودة', callback_data='back_to_main')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    markup.add(itembtn5)
    return markup

def create_github_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('📋 عرض مستودعات GitHub', callback_data='list_github_repos')
    itembtn2 = telebot.types.InlineKeyboardButton('➕ إنشاء مستودع جديد في GitHub', callback_data='create_github_repo')
    itembtn3 = telebot.types.InlineKeyboardButton('🗑️ حذف مستودع في GitHub', callback_data='delete_github_repo')
    itembtn4 = telebot.types.InlineKeyboardButton('📤 تحميل ملفات إلى مستودع GitHub', callback_data='upload_files_to_github')
    itembtn5 = telebot.types.InlineKeyboardButton('🗑️ حذف ملفات من مستودع GitHub', callback_data='delete_files_from_github')
    itembtn6 = telebot.types.InlineKeyboardButton('🔙 العودة', callback_data='back_to_main')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
    markup.add(itembtn6)
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
        bot.edit_message_text("قسم هيروكو:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_heroku_menu())
    elif call.data == 'github_section':
        bot.edit_message_text("قسم GitHub:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_menu())
    elif call.data == 'list_heroku_apps':
        list_heroku_apps(call.message)
    elif call.data == 'list_github_repos':
        list_github_repos(call.message)
    elif call.data == 'create_heroku_app':
        prompt_for_heroku_app_name(call.message)
    elif call.data == 'delete_heroku_app':
        prompt_for_heroku_app_to_delete(call.message)
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
            chat_id=call.message.chat.id, message_id=call.message.message_id, 
            reply_markup=create_main_menu()
        )

def list_heroku_apps(message):
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if (response.status_code == 200):
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.edit_message_text(f"التطبيقات المتاحة في هيروكو:\n{apps_list}", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_heroku_menu())
    else:
        bot.edit_message_text("حدث خطأ في جلب التطبيقات من هيروكو.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_heroku_menu())

def list_github_repos(message):
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repos = response.json()
        repos_list = "\n".join([f"`{repo['name']}`" for repo in repos])
        bot.edit_message_text(f"المستودعات المتاحة في GitHub:\n{repos_list}", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_github_menu())
    else:
        bot.edit_message_text("حدث خطأ في جلب المستودعات من GitHub.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())

def prompt_for_heroku_app_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الجديد في هيروكو:", reply_markup=create_heroku_menu())
    bot.register_next_step_handler(msg, process_create_heroku_app_step)

def process_create_heroku_app_step(message):
    app_name = message.text
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if response.status_code == 201:
        bot.edit_message_text(f"تم إنشاء التطبيق `{app_name}` بنجاح في هيروكو.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_heroku_menu())
    elif response.status_code == 422:
        bot.edit_message_text("الاسم موجود بالفعل، يرجى اختيار اسم آخر.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_heroku_menu())
    else:
        bot.edit_message_text("حدث خطأ أثناء إنشاء التطبيق في هيروكو.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_heroku_menu())

def prompt_for_heroku_app_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الذي تريد حذفه من هيروكو:", reply_markup=create_heroku_menu())
    bot.register_next_step_handler(msg, process_delete_heroku_app_step)

def process_delete_heroku_app_step(message):
    app_name = message.text
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 204:
        bot.edit_message_text(f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_heroku_menu())
    elif response.status_code == 404:
        bot.edit_message_text(f"التطبيق `{app_name}` غير موجود في هيروكو.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_heroku_menu())
    else:
        bot.edit_message_text("حدث خطأ أثناء حذف التطبيق من هيروكو.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_heroku_menu())

def prompt_for_github_repo_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الجديد في GitHub:", reply_markup=create_github_menu())
    bot.register_next_step_handler(msg, process_create_github_repo_step)

def process_create_github_repo_step(message):
    repo_name = message.text
    response = requests.post(
        f'{GITHUB_BASE_URL}/user/repos',
        headers=GITHUB_HEADERS,
        json={"name": repo_name, "private": False}
    )
    if response.status_code == 201:
        bot.edit_message_text(f"تم إنشاء المستودع `{repo_name}` بنجاح في GitHub.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_github_menu())
    elif response.status_code == 422:
        bot.edit_message_text("الاسم موجود بالفعل، يرجى اختيار اسم آخر.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())
    else:
        bot.edit_message_text("حدث خطأ أثناء إنشاء المستودع في GitHub.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())

def prompt_for_github_repo_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذفه من GitHub:", reply_markup=create_github_menu())
    bot.register_next_step_handler(msg, process_delete_github_repo_step)

def process_delete_github_repo_step(message):
    repo_name = message.text
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{your_github_username}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 204:
        bot.edit_message_text(f"تم حذف المستودع `{repo_name}` بنجاح من GitHub.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_github_menu())
    elif response.status_code == 404:
        bot.edit_message_text(f"المستودع `{repo_name}` غير موجود في GitHub.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_github_menu())
    else:
        bot.edit_message_text("حدث خطأ أثناء حذف المستودع من GitHub.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())

def prompt_for_github_repo_for_upload(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد تحميل الملفات إليه في GitHub:", reply_markup=create_github_menu())
    bot.register_next_step_handler(msg, prompt_for_file_upload)

def prompt_for_file_upload(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أرسل الملف الذي تريد تحميله إلى المستودع:", reply_markup=create_github_menu())
    bot.register_next_step_handler(msg, process_file_upload_step, repo_name)

def process_file_upload_step(message, repo_name):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_path = os.path.join("uploads", message.document.file_name)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        with open(file_path, 'rb') as f:
            content = f.read()

        base64_content = base64.b64encode(content).decode('utf-8')
        response = requests.put(
            f'{GITHUB_BASE_URL}/repos/{your_github_username}/{repo_name}/contents/{message.document.file_name}',
            headers=GITHUB_HEADERS,
            json={
                "message": f"Upload {message.document.file_name}",
                "content": base64_content
            }
        )

        if response.status_code == 201:
            bot.edit_message_text(f"تم تحميل الملف `{message.document.file_name}` بنجاح إلى المستودع `{repo_name}` في GitHub.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_github_menu())
        else:
            bot.edit_message_text("حدث خطأ أثناء تحميل الملف إلى GitHub.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())
        os.remove(file_path)
    else:
        bot.edit_message_text("يرجى إرسال ملف صالح.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())

def prompt_for_github_repo_for_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذف الملفات منه في GitHub:", reply_markup=create_github_menu())
    bot.register_next_step_handler(msg, prompt_for_file_delete)

def prompt_for_file_delete(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل اسم الملف الذي تريد حذفه من المستودع:", reply_markup=create_github_menu())
    bot.register_next_step_handler(msg, process_file_delete_step, repo_name)

def process_file_delete_step(message, repo_name):
    file_name = message.text
    response = requests.get(
        f'{GITHUB_BASE_URL}/repos/{your_github_username}/{repo_name}/contents/{file_name}',
        headers=GITHUB_HEADERS
    )
    if response.status_code == 200:
        file_sha = response.json().get('sha')
        delete_response = requests.delete(
            f'{GITHUB_BASE_URL}/repos/{your_github_username}/{repo_name}/contents/{file_name}',
            headers=GITHUB_HEADERS,
            json={
                "message": f"Delete {file_name}",
                "sha": file_sha
            }
        )
        if delete_response.status_code == 200:
            bot.edit_message_text(f"تم حذف الملف `{file_name}` بنجاح من المستودع `{repo_name}` في GitHub.", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_github_menu())
        else:
            bot.edit_message_text("حدث خطأ أثناء حذف الملف من GitHub.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())
    else:
        bot.edit_message_text("الملف غير موجود في المستودع.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_github_menu())

def prompt_for_github_repo_for_deploy(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد نشره على هيروكو:", reply_markup=create_heroku_menu())
    bot.register_next_step_handler(msg, process_deploy_to_heroku_step)

def process_deploy_to_heroku_step(message):
    repo_name = message.text
    app_name = repo_name.replace('_', '-')
    create_app_response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if create_app_response.status_code == 201:
        bot.edit_message_text(f"تم إنشاء التطبيق `{app_name}` في هيروكو. جاري نشر الكود...", chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=create_heroku_menu())
        # تنفيذ عملية نشر الكود إلى هيروكو هنا
    else:
        bot.edit_message_text("حدث خطأ أثناء إنشاء التطبيق في هيروكو.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=create_heroku_menu())

bot.polling()
