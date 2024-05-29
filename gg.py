import telebot
import requests
import os
import zipfile
import base64
import random
import time
import threading

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

main_buttons = [
    {'text': '📱 عرض التطبيقات في هيروكو', 'callback_data': 'list_heroku_apps'},
    {'text': '📂 عرض مستودعات GitHub', 'callback_data': 'list_github_repos'},
    {'text': '🆕 إنشاء تطبيق جديد في هيروكو', 'callback_data': 'create_heroku_app'},
    {'text': '❌ حذف تطبيق في هيروكو', 'callback_data': 'delete_heroku_app'},
    {'text': '🆕 إنشاء مستودع جديد في GitHub', 'callback_data': 'create_github_repo'},
    {'text': '❌ حذف مستودع في GitHub', 'callback_data': 'delete_github_repo'},
    {'text': '📤 تحميل ملفات إلى مستودع GitHub', 'callback_data': 'upload_files_to_github'},
    {'text': '🗑 حذف ملفات من مستودع GitHub', 'callback_data': 'delete_files_from_github'},
    {'text': '🚀 نشر كود إلى هيروكو', 'callback_data': 'deploy_to_heroku'},
    {'text': '🔄 تبديل ترتيب الأزرار', 'callback_data': 'shuffle_buttons'},
    {'text': '🗑 حذف ذاتي', 'callback_data': 'self_delete_menu'},
    {'text': '🔚 إلغاء الحذف الذاتي', 'callback_data': 'cancel_self_delete'},
    {'text': '🕒 عرض الوقت المتبقي للحذف', 'callback_data': 'show_self_delete_time'},
]

self_delete_apps = {}

def create_main_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    shuffled_buttons = random.sample(main_buttons, len(main_buttons))
    for button in shuffled_buttons:
        itembtn = telebot.types.InlineKeyboardButton(button['text'], callback_data=button['callback_data'])
        markup.add(itembtn)
    dev_btn = telebot.types.InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/q_w_c')
    markup.add(dev_btn)
    return markup

def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_btn = telebot.types.InlineKeyboardButton('🔙 العودة', callback_data='back_to_main')
    dev_btn = telebot.types.InlineKeyboardButton('👨‍💻 المطور', url='https://t.me/q_w_c')
    markup.add(back_btn, dev_btn)
    return markup

def create_self_delete_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    self_delete_btn = telebot.types.InlineKeyboardButton('🗑 حذف ذاتي', callback_data='self_delete_app')
    back_btn = telebot.types.InlineKeyboardButton('🔙 العودة', callback_data='back_to_main')
    markup.add(self_delete_btn, back_btn)
    return markup

def create_heroku_section_button():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    heroku_btn = telebot.types.InlineKeyboardButton('قسم هيروكو', callback_data='heroku_section')
    markupheroku_btn = telebot.types.InlineKeyboardButton('قسم هيروكو', callback_data='heroku_section')
    markup.add(heroku_btn)
    return markup

def create_github_section_button():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    github_btn = telebot.types.InlineKeyboardButton('قسم جيتهاب', callback_data='github_section')
    markup.add(github_btn)
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
    if call.data == 'list_heroku_apps':
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
    elif call.data == 'shuffle_buttons':
        bot.edit_message_reply_markup(
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_main_menu()
        )
    elif call.data == 'back_to_main':
        bot.edit_message_reply_markup(
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_main_menu()
        )
    elif call.data == 'self_delete_menu':
        list_self_delete_apps(call.message)
    elif call.data == 'self_delete_app':
        prompt_for_self_delete_app(call.message)
    elif call.data == 'cancel_self_delete':
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_main_menu()
        )
    elif call.data == 'show_self_delete_time':
        show_self_delete_time(call.message)
    elif call.data == 'heroku_section':
        bot.send_message(call.message.chat.id, "قسم هيروكو", reply_markup=create_main_menu())
    elif call.data == 'github_section':
        bot.send_message(call.message.chat.id, "قسم جيتهاب", reply_markup=create_main_menu())

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

# الدالة لإنشاء التطبيق في هيروكو
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

# الدالة لحذف التطبيق في هيروكو
def process_delete_heroku_app_step(message):
    app_name = message.text
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 200 or response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف التطبيق من هيروكو.", reply_markup=create_back_button())

def prompt_for_github_repo_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الجديد في GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_repo_visibility_step)

# الدالة لإنشاء المستودع في جيتهاب
def process_github_repo_visibility_step(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "هل تريد أن يكون المستودع خاصًا؟ (نعم/لا):", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_create_github_repo_step, repo_name)

def process_create_github_repo_step(message, repo_name):
    is_private = message.text.lower() in ['نعم', 'yes']
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 404:
        response = requests.post(
            f'{GITHUB_BASE_URL}/user/repos',
            headers=GITHUB_HEADERS,
            json={"name": repo_name, "private": is_private})
        if response.status_code == 201:
            bot.send_message(message.chat.id, f"تم إنشاء المستودع `{repo_name}` بنجاح في GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء إنشاء المستودع في GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "اسم المستودع موجود بالفعل، يرجى اختيار اسم آخر.", reply_markup=create_back_button())

def prompt_for_github_repo_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذفه من GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_delete_github_repo_step)

# الدالة لحذف المستودع في جيتهاب
def process_delete_github_repo_step(message):
    repo_name = message.text
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 204:
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح من GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف المستودع من GitHub.", reply_markup=create_back_button())def prompt_for_github_repo_for_upload(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد تحميل الملفات إليه:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_upload_files_step)

# الدالة لتحميل الملفات إلى مستودع جيتهاب
def process_upload_files_step(message):
    global repo_name
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أرسل الملف المضغوط (zip) الذي تريد تحميله:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, receive_zip_file)

def receive_zip_file(message):
    if message.document and message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall('temp_files')
        os.remove(file_name)
        upload_extracted_files('temp_files', message)
    else:
        bot.send_message(message.chat.id, "يرجى إرسال ملف مضغوط (zip) صالح.", reply_markup=create_back_button())

def upload_extracted_files(directory, message):
    for root, _, files in os.listdir(directory):
        for file in files:
            upload_file_to_github(directory, file, message)

def upload_file_to_github(directory, file, message):
    file_path = os.path.join(directory, file)
    with open(file_path, 'rb') as f:
        content = f.read()
    encoded_content = base64.b64encode(content).decode('utf-8')
    response = requests.put(
        f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file}',
        headers=GITHUB_HEADERS,
        json={"message": "Upload file", "content": encoded_content, "branch": "main"}
    )
    if response.status_code == 201:
        bot.send_message(message.chat.id, f"تم رفع الملف `{file}` بنجاح إلى المستودع `{repo_name}` في GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء رفع الملف `{file}` إلى المستودع في GitHub.", reply_markup=create_back_button())

def prompt_for_github_repo_for_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذف الملفات منه في GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_delete_files_step)

def process_delete_files_step(message):
    global repo_name
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل اسم الملف الذي تريد حذفه:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, delete_file_from_github)

def delete_file_from_github(message):
    file_name = message.text
    response = requests.get(
        f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_name}',
        headers=GITHUB_HEADERS
    )
    if response.status_code == 200:
        file_content = response.json()
        response = requests.delete(
            f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_name}?sha={file_content["sha"]}',
            headers=GITHUB_HEADERS,
            json={"message": "Delete file", "branch": "main"}
        )
        if response.status_code == 200:
            bot.send_message(message.chat.id, f"تم حذف الملف `{file_name}` بنجاح من المستودع `{repo_name}` في GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
        else:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء حذف الملف `{file_name}` من المستودع في GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, f"الملف `{file_name}` غير موجود في المستودع `{repo_name}` في GitHub.", parse_mode='Markdown', reply_markup=create_back_button())

def prompt_for_github_repo_for_deploy(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد نشره على هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, deploy_to_heroku)

def deploy_to_heroku(message):
    repo_name = message.text
    response = requests.post(
        f'{HEROKU_BASE_URL}/apps/{repo_name}/builds',
        headers=HEROKU_HEADERS
    )
    if response.status_code == 202:
        bot.send_message(message.chat.id, f"جارٍ نشر الكود من المستودع `{repo_name}` إلى هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء نشر الكود من المستودع `{repo_name}` إلى هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())

def list_self_delete_apps(message):
    if not self_delete_apps:
        bot.send_message(message.chat.id, "لا توجد تطبيقات مفعلة للحذف الذاتي.", reply_markup=create_back_button())
    else:
        apps_list = "\n".join([f"`{app}`" for app in self_delete_apps.keys()])
        bot.send_message(message.chat.id, f"التطبيقات المفعلة للحذف الذاتي:\n{apps_list}", parse_mode='Markdown', reply_markup=create_self_delete_menu())

def prompt_for_self_delete_app(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق الذي تريد تفعيل حذفه الذاتي:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_self_delete_app_step)

def process_self_delete_app_step(message):
    app_name = message.text
    self_delete_apps[app_name] = threading.Timer(86400, delete_heroku_app, args=[app_name])
    self_delete_apps[app_name].start()
    bot.send_message(message.chat.id, f"تم تفعيل حذف التطبيق `{app_name}` بنجاح بعد 24 ساعة.", parse_mode='Markdown', reply_markup=create_self_delete_menu())

def delete_heroku_app(app_name):
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 200 or response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو بناءً على طلب حذف ذاتي.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء حذف التطبيق `{app_name}` من هيروكو بناءً على طلب حذف ذاتي.", parse_mode='Markdown')

# زر لعرض الوقت المتبقي للحذف الذاتي
@bot.callback_query_handler(func=lambda call: call.data == 'self_delete_menu')
def self_delete_menu_callback(call):
    list_self_delete_apps(call.message)

# زر لعرض قسم هيروكو
@bot.message_handler(commands=['heroku'])
def show_heroku_menu(message):
    bot.send_message(message.chat.id, "قسم هيروكو", reply_markup=create_main_menu())

# زر لعرض قسم جيتهاب
@bot.message_handler(commands=['github'])
def show_github_menu(message):
    bot.send_message(message.chat.id, "قسم جيتهاب", reply_markup=create_main_menu())

# تشغيل البوت
bot.polling()
