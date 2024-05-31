import telebot
import requests
import os
import zipfile
import base64
import time

bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"  # توكن البوت في تليجرام
heroku_api_key = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"  # مفتاح API الخاص بـ Heroku
github_token = "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"  # توكن GitHub
dyno_increment = 1

bot = telebot.TeleBot(bot_token)

HEROKU_BASE_URL = 'https://api.heroku.com'
HEROKU_HEADERS = {
    'Authorization': f'Bearer {heroku_api_key}',
    'Accept': 'application/vnd.heroku+json; version=3'
}

GITHUB_BASE_URL = 'https://api.github.com'
GITHUB_HEADERS = {
    'Authorization': f'token {github_token}',
    'Accept': 'application/vnd.github.v3+json'
}

def create_main_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('قسم هيروكو 🏢', callback_data='heroku_section')
    itembtn2 = telebot.types.InlineKeyboardButton('قسم GitHub 🗂️', callback_data='github_section')
    itembtn3 = telebot.types.InlineKeyboardButton('المطور 👨‍💻', url='https://t.me/q_w_c')
    markup.add(itembtn1, itembtn2)
    markup.add(itembtn3)
    return markup

def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_btn = telebot.types.InlineKeyboardButton('العودة 🔙', callback_data='back_to_main')
    dev_btn = telebot.types.InlineKeyboardButton('المطور 👨‍💻', url='https://t.me/q_w_c')
    markup.add(back_btn, dev_btn)
    return markup

def create_heroku_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('عرض التطبيقات 📜', callback_data='list_heroku_apps')
    itembtn2 = telebot.types.InlineKeyboardButton('إنشاء تطبيق 🆕', callback_data='create_heroku_app')
    itembtn3 = telebot.types.InlineKeyboardButton('حذف تطبيق ❌', callback_data='delete_heroku_app')
    itembtn4 = telebot.types.InlineKeyboardButton('نشر كود 🚀', callback_data='deploy_to_heroku')
    itembtn5 = telebot.types.InlineKeyboardButton('تشغيل التطبيق ▶️', callback_data='start_heroku_app')
    itembtn6 = telebot.types.InlineKeyboardButton('إيقاف التطبيق ⏹️', callback_data='stop_heroku_app')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    markup.add(itembtn5, itembtn6)
    markup.add(telebot.types.InlineKeyboardButton('العودة 🔙', callback_data='back_to_main'))
    return markup

def create_github_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('عرض مستودعات 📜', callback_data='list_github_repos')
    itembtn2 = telebot.types.InlineKeyboardButton('إنشاء مستودع 🆕', callback_data='create_github_repo')
    itembtn3 = telebot.types.InlineKeyboardButton('حذف مستودع ❌', callback_data='delete_github_repo')
    itembtn4 = telebot.types.InlineKeyboardButton('تحميل ملفات ⬆️', callback_data='upload_files_to_github')
    itembtn5 = telebot.types.InlineKeyboardButton('حذف ملفات ⬇️', callback_data='delete_files_from_github')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
    markup.add(telebot.types.InlineKeyboardButton('العودة 🔙', callback_data='back_to_main'))
    return markup

def send_progress(chat_id, progress, message_id=None):
    progress_bar = "⬛" * (progress // 10) + "⬜" * (10 - (progress // 10))
    text = f"تحميل... {progress_bar} {progress}%"
    if message_id:
        bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    else:
        return bot.send_message(chat_id, text).message_id

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
    elif call.data == 'start_heroku_app':
        prompt_for_heroku_app_to_start(call.message)
    elif call.data == 'stop_heroku_app':
        prompt_for_heroku_app_to_stop(call.message)
    elif call.data == 'back_to_main':
        bot.edit_message_text(
            "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_main_menu()
        )

def list_heroku_apps(message):
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.send_message(message.chat.id, f"التطبيقات المتاحة في هيروكو:\n{apps_list}", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ في جلب التطبيقات من هيروكو.", reply_markup=create_back_button())

def list_github_repos(message):
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repos = response.json()
        repos_list = "\n".join([f"`{repo['name']}`" for repo in repos])
        bot.send_message(message.chat.id, f"المستودعات المتاحة في GitHub:\n{repos_list}", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ في جلب المستودعات من GitHub.", reply_markup=create_back_button())

def prompt_for_heroku_app_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الجديد في هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_create_heroku_app_step)

def process_create_heroku_app_step(message):
    app_name = message.text
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps',
        headers=HEROKU_HEADERS,
        json={"name": app_name, "region": "eu"}
    )
    if response.status_code == 201:
        bot.send_message(message.chat.id, f"تم إنشاء التطبيق `{app_name}` بنجاح في هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    elif response.status_code == 422:
        bot.send_message(message.chat.id, "الاسم موجود بالفعل، يرجى اختيار اسم آخر.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء إنشاء التطبيق في هيروكو.", reply_markup=create_back_button())

def prompt_for_heroku_app_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الذي تريد حذفه من هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_delete_heroku_app_step)

def process_delete_heroku_app_step(message):
    app_name = message.text
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code ==200:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    elif response.status_code == 404:
        bot.send_message(message.chat.id, "لم يتم العثور على التطبيق، يرجى التأكد من الاسم.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف التطبيق من هيروكو.", reply_markup=create_back_button())

def prompt_for_github_repo_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الجديد في GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_create_github_repo_step)

def process_create_github_repo_step(message):
    repo_name = message.text
    response = requests.post(
        f'{GITHUB_BASE_URL}/user/repos',
        headers=GITHUB_HEADERS,
        json={"name": repo_name}
    )
    if response.status_code == 201:
        bot.send_message(message.chat.id, f"تم إنشاء المستودع `{repo_name}` بنجاح في GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
    elif response.status_code == 422:
        bot.send_message(message.chat.id, "الاسم موجود بالفعل، يرجى اختيار اسم آخر.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء إنشاء المستودع في GitHub.", reply_markup=create_back_button())

def prompt_for_github_repo_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذفه من GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_delete_github_repo_step)

def process_delete_github_repo_step(message):
    repo_name = message.text
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/YOUR_GITHUB_USERNAME/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 204:
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح من GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
    elif response.status_code == 404:
        bot.send_message(message.chat.id, "لمتم العثور على المستودع، يرجى التأكد من الاسم.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف المستودع من GitHub.", reply_markup=create_back_button())

def prompt_for_github_repo_for_upload(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد رفع الملفات إليه في GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_repo_for_upload_step)

def process_github_repo_for_upload_step(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "الرجاء تحميل الملفات التي تريد رفعها (بصيغة ZIP):", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_file_upload_step, repo_name)

def process_github_file_upload_step(message, repo_name):
    if message.document and message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('temp.zip', 'wb') as new_file:
            new_file.write(downloaded_file)
        with zipfile.ZipFile('temp.zip', 'r') as zip_ref:
            zip_ref.extractall('temp_files')
        os.remove('temp.zip')

        for root, _, files in os.walk('temp_files'):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                relative_path = os.path.relpath(file_path, 'temp_files')
                response = requests.put(
                    f'{GITHUB_BASE_URL}/repos/YOUR_GITHUB_USERNAME/{repo_name}/contents/{relative_path}',
                    headers=GITHUB_HEADERS,
                    json={
                        "message": f"Add {relative_path}",
                        "content": content
                    }
                )
                if response.status_code != 201:
                    bot.send_message(message.chat.id, f"فشل رفع الملف: {relative_path}", reply_markup=create_back_button())
                    return
        bot.send_message(message.chat.id, "تم رفع الملفات بنجاح إلى GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "يرجى تحميل ملف بصيغة ZIP.", reply_markup=create_back_button())

def prompt_for_github_repo_for_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذف الملفات منه في GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_repo_for_delete_step)

def process_github_repo_for_delete_step(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل مسار الملف الذي تريد حذفه من المستودع:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_file_delete_step, repo_name)

def process_github_file_delete_step(message, repo_name):
    file_path = message.text
    response = requests.get(f'{GITHUB_BASE_URL}/repos/YOUR_GITHUB_USERNAME/{repo_name}/contents/{file_path}', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        file_sha = response.json()['sha']
        delete_response = requests.delete(
            f'{GITHUB_BASE_URL}/repos/YOUR_GITHUB_USERNAME/{repo_name}/contents/{file_path}',
            headers=GITHUB_HEADERS,
            json={"message": f"Delete {file_path}", "sha": file_sha}
        )
        if delete_response.status_code == 200:
            bot.send_message(message.chat.id, f"تم حذف الملف `{file_path}` بنجاح من GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء حذف الملف من GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على الملف، يرجى التأكد من المسار.", reply_markup=create_back_button())

def prompt_for_github_repo_for_deploy(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد نشره في هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_repo_for_deploy_step)

def process_github_repo_for_deploy_step(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق في هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_deploy_to_heroku_step, repo_name)

def process_deploy_to_heroku_step(message, repo_name):
    app_name = message.text
    deploy_response = requests.post(
        f'https://api.heroku.com/apps/{app_name}/builds',
        headers={
            'Authorization': f'Bearer {heroku_api_key}',
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json'
        },
        json={"source_blob": {"url": f"https://github.com/YOUR_GITHUB_USERNAME/{repo_name}/tarball/master"}}
    )
    if deploy_response.status_code == 201:
        bot.send_message(message.chat.id, f"تم نشر المستودع `{repo_name}` بنجاح على التطبيق `{app_name}` في هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء نشر المستودع في هيروكو.", reply_markup=create_back_button())

bot.polling()
