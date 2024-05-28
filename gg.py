import telebot
import requests
import os
import zipfile
import base64

# إعدادات البوت
bot_token =input( "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20 = ")
heroku_api_key = input('HRKU-bffcce5a-db84-4c17-97ed-160f04745271 = ')  # استبدل توكن هيروكو هنا
github_token =input("GITHUB TOKEN = ")

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
    itembtn1 = telebot.types.InlineKeyboardButton('عرض التطبيقات في هيروكو', callback_data='list_heroku_apps')
    itembtn2 = telebot.types.InlineKeyboardButton('عرض مستودعات GitHub', callback_data='list_github_repos')
    itembtn3 = telebot.types.InlineKeyboardButton('إنشاء تطبيق جديد في هيروكو', callback_data='create_heroku_app')
    itembtn4 = telebot.types.InlineKeyboardButton('حذف تطبيق في هيروكو', callback_data='delete_heroku_app')
    itembtn5 = telebot.types.InlineKeyboardButton('إنشاء مستودع جديد في GitHub', callback_data='create_github_repo')
    itembtn6 = telebot.types.InlineKeyboardButton('حذف مستودع في GitHub', callback_data='delete_github_repo')
    itembtn7 = telebot.types.InlineKeyboardButton('تحميل ملفات إلى مستودع GitHub', callback_data='upload_files_to_github')
    itembtn8 = telebot.types.InlineKeyboardButton('حذف ملفات من مستودع GitHub', callback_data='delete_files_from_github')
    itembtn9 = telebot.types.InlineKeyboardButton('نشر كود إلى هيروكو', callback_data='deploy_to_heroku')
    itembtn10 = telebot.types.InlineKeyboardButton('المطور', url='https://t.me/q_w_c')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6, itembtn7, itembtn8, itembtn9)
    markup.add(itembtn10)
    return markup

def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_btn = telebot.types.InlineKeyboardButton('العودة', callback_data='back_to_main')
    dev_btn = telebot.types.InlineKeyboardButton('المطور', url='https://t.me/q_w_c')
    markup.add(back_btn, dev_btn)
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
    elif call.data == 'back_to_main':
        bot.send_message(
            call.message.chat.id, 
            "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:", 
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
    if response.status_code == 200 or response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح من هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف التطبيق من هيروكو.", reply_markup=create_back_button())

def prompt_for_github_repo_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الجديد في GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_repo_visibility_step)

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
            json={"name": repo_name, "private": is_private}
        )
        if response.status_code == 201:
            bot.send_message(message.chat.id, f"تم إنشاء المستودع `{repo_name}` بنجاح في GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء إنشاء المستودع في GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "اسم المستودع موجود بالفعل، يرجى اختيار اسم آخر.", reply_markup=create_back_button())

def prompt_for_github_repo_to_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد حذفه من GitHub:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_delete_github_repo_step)

def process_delete_github_repo_step(message):
    repo_name = message.text
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}', headers=GITHUB_HEADERS)
    if response.status_code == 204:
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح من GitHub.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء حذف المستودع من GitHub.", reply_markup=create_back_button())

def prompt_for_github_repo_for_upload(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد تحميل الملفات إليه:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_upload_files_step)

def process_upload_files_step(message):
    global repo_name
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أرسل الملفات التي تريد تحميلها:", reply_markup=create_back_button())
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
        if response.status_code == 201:
            bot.send_message(message.chat.id, f"تم تحميل الملف `{file_name}` بنجاح إلى المستودع `{repo_name}`.", parse_mode='Markdown', reply_markup=create_back_button())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء تحميل الملف إلى GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "يرجى إرسال ملف صحيح.", reply_markup=create_back_button())

def prompt_for_github_repo_for_delete(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_delete_files_step)

def process_delete_files_step(message):
    global repo_name
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل مسار الملف الذي تريد حذفه:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, confirm_delete_file)

def confirm_delete_file(message):
    file_path = message.text
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_path}', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        file_sha = response.json()['sha']
        response = requests.delete(
            f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/contents/{file_path}',
            headers=GITHUB_HEADERS,
            json={"message": f"Deleting {file_path}", "sha": file_sha}
        )
        if response.status_code == 200:
            bot.send_message(message.chat.id, f"تم حذف الملف `{file_path}` بنجاح من المستودع `{repo_name}`.", parse_mode='Markdown', reply_markup=create_back_button())
        else:
            bot.send_message(message.chat.id, "حدث خطأ أثناء حذف الملف من GitHub.", reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على الملف، يرجى التأكد من المسار الصحيح.", reply_markup=create_back_button())

def prompt_for_github_repo_for_deploy(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع المراد نشره:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_deploy_step)

def process_deploy_step(message):
    repo_name = message.text
    response = requests.get(f'{GITHUB_BASE_URL}/repos/{message.from_user.username}/{repo_name}/zipball', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        zip_data = response.content
        tmp_dir = f'/tmp/{repo_name}'
        with open(f'{tmp_dir}.zip', 'wb') as f:
            f.write(zip_data)
        with zipfile.ZipFile(f'{tmp_dir}.zip', 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
        app_name = repo_name
        os.system(f'heroku git:remote -a {app_name}')
        os.system('git add .')
        os.system('git commit -m "Deploying to Heroku"')
        os.system('git push heroku master')
        bot.send_message(message.chat.id, f"تم نشر المستودع `{repo_name}` بنجاح إلى هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء تنزيل المستودع من GitHub.", reply_markup=create_back_button())

bot.polling()
