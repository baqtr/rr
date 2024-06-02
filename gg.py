import os
import telebot
import requests
import threading
import time
from datetime import datetime, timedelta
import pytz
import zipfile
import io

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
github_token = "YOUR_GITHUB_TOKEN_HERE"  # ضع توكن جيتهاب هنا

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'
GITHUB_BASE_URL = 'https://api.github.com'

# قائمة التطبيقات المجدولة للحذف الذاتي
self_deleting_apps = {}

# تخزين حسابات المستخدم
user_accounts = {}

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("إضافة حساب ➕", callback_data="add_account")
    button2 = telebot.types.InlineKeyboardButton("حساباتك 🗂️", callback_data="list_accounts")
    button3 = telebot.types.InlineKeyboardButton("قسم جيتهاب 📁", callback_data="github_section")
    markup.add(button1, button2, button3)
    return markup

# دالة لإنشاء زر العودة
def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back")
    markup.add(back_button)
    return markup

# دالة لإنشاء أزرار التحكم بالحسابات
def create_account_control_buttons(account_index):
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("جلب تطبيقات هيروكو 📦", callback_data=f"list_heroku_apps_{account_index}")
    button2 = telebot.types.InlineKeyboardButton("حذف تطبيق ❌", callback_data=f"delete_app_{account_index}")
    button3 = telebot.types.InlineKeyboardButton("الحذف الذاتي ⏲️", callback_data=f"self_delete_app_{account_index}")
    button4 = telebot.types.InlineKeyboardButton("الوقت المتبقي ⏳", callback_data="remaining_time")
    markup.add(button1) 
    markup.add(button2)
    markup.add(button3)
    markup.add(button4)
    markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="list_accounts"))
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_accounts:
        user_accounts[user_id] = []
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_main_buttons())

# دالة لإضافة حساب جديد
def add_account(call):
    msg = bot.edit_message_text("يرجى إرسال مفتاح API الخاص بحساب Heroku:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_new_account)

def handle_new_account(message):
    api_key = message.text.strip()
    user_id = message.from_user.id
    if api_key in [account['api_key'] for account in user_accounts[user_id]]:
        bot.send_message(message.chat.id, "هذا الحساب مضاف مسبقًا.", reply_markup=create_main_buttons())
    elif validate_heroku_api_key(api_key):
        user_accounts[user_id].append({'api_key': api_key})
        bot.send_message(message.chat.id, "تمت إضافة حساب Heroku بنجاح!", reply_markup=create_main_buttons())
    else:
        bot.send_message(message.chat.id, "مفتاح API غير صحيح. يرجى المحاولة مرة أخرى.", reply_markup=create_main_buttons())

# التحقق من صحة مفتاح API
def validate_heroku_api_key(api_key):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    return response.status_code == 200

# عرض حسابات المستخدم
def list_accounts(call):
    user_id = call.from_user.id
    if user_id in user_accounts and user_accounts[user_id]:
        accounts_list = "\n".join([f"حساب {index + 1}: `{get_heroku_account_name(account['api_key'])}`" for index, account in enumerate(user_accounts[user_id])])
        markup = telebot.types.InlineKeyboardMarkup()
        for index in range(len(user_accounts[user_id])):
            account_name = get_heroku_account_name(user_accounts[user_id][index]['api_key'])
            markup.add(telebot.types.InlineKeyboardButton(f"{account_name}", callback_data=f"select_account_{index}"))
        markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back"))
        bot.edit_message_text(f"حساباتك:\n{accounts_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.edit_message_text("لا توجد حسابات مضافة.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# جلب اسم حساب هيروكو
def get_heroku_account_name(api_key):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/account', headers=headers)
    if response.status_code == 200:
        return response.json().get('email', 'Unknown')
    return 'Unknown'

# دالة لجلب تطبيقات هيروكو
def list_heroku_apps(call):
    account_index = int(call.data.split("_")[-1])
    user_id = call.from_user.id
    if not user_accounts[user_id]:
        bot.edit_message_text("لا توجد حسابات مضافة. يرجى إضافة حساب أولاً.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        return

    headers = {
        'Authorization': f'Bearer {user_accounts[user_id][account_index]["api_key"]}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    bot.edit_message_text("جلب التطبيقات... ⬛⬜ 0%", chat_id=call.message.chat.id, message_id=call.message.message_id)
    time.sleep(2)
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.edit_message_text("جلب التطبيقات... ⬛⬛ 50%", chat_id=call.message.chat.id, message_id=call.message.message_id)
        time.sleep(2)
        bot.edit_message_text(f"التطبيقات المتاحة في هيروكو:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("حدث خطأ في جلب التطبيقات من هيروكو.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data == "github_section":
        github_section(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"إدارة حساب {account_index + 1}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_heroku_apps_"):
        list_heroku_apps(call)
    elif call.data.startswith("delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_deletion(m, account_index))
    elif call.data.startswith("self_delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق للحذف الذاتي:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_self_deletion(m, account_index))
    elif call.data == "remaining_time":
        show_remaining_time(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# دالة لمعالجة اسم التطبيق للحذف
def handle_app_name_for_deletion(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    if validate_heroku_app(app_name, account_index, user_id):
        delete_heroku_app(app_name, message, account_index)
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# تحقق من صحة اسم التطبيق
def validate_heroku_app(app_name, account_index, user_id):
    headers = {
        'Authorization': f'Bearer {user_accounts[user_id][account_index]["api_key"]}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
    return response.status_code == 200

# دالة لمعالجة اسم التطبيق للحذف الذاتي
def handle_app_name_for_self_deletion(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    if validate_heroku_app(app_name, account_index, user_id):
        if app_name in self_deleting_apps:
            bot.send_message(message.chat.id, f"تم وضع التطبيق `{app_name}` مسبقًا في قائمة الحذف الذاتي.", parse_mode='Markdown')
        else:
            msg = bot.send_message(message.chat.id, "يرجى إدخال الوقت المطلوب بالدقائق لحذف التطبيق:")
            bot.register_next_step_handler(msg, lambda m: handle_self_deletion_time(m, app_name, account_index))
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة لمعالجة الوقت للحذف الذاتي
def handle_self_deletion_time(message, app_name, account_index):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
        self_deleting_apps[app_name] = {'minutes': minutes, 'start_time': datetime.now(pytz.timezone('Asia/Baghdad'))}
        bot.send_message(message.chat.id, f"سيتم حذف التطبيق `{app_name}` بعد {minutes} دقيقة.\n", reply_markup=create_remaining_time_button())
        # بدء عملية الحذف الذاتي
        threading.Timer(minutes * 60, lambda: delete_and_remove_app(app_name, message, account_index)).start()
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إدخال عدد صحيح إيجابي للدقائق.")

# زر عرض الوقت المتبقي
def create_remaining_time_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("الوقت المتبقي ⏳", callback_data="remaining_time")
    markup.add(button)
    return markup

# حذف التطبيق وإزالته من القائمة
def delete_and_remove_app(app_name, message, account_index):
    delete_heroku_app(app_name, message, account_index)
    if app_name in self_deleting_apps:
        del self_deleting_apps[app_name]

# حذف التطبيق
def delete_heroku_app(app_name, message, account_index):
    user_id = message.from_user.id
    headers = {
        'Authorization': f'Bearer {user_accounts[user_id][account_index]["api_key"]}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
    if response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء محاولة حذف التطبيق.")

# عرض الوقت المتبقي للحذف الذاتي
def show_remaining_time(call):
    remaining_time_message = "التطبيقات المجدولة للحذف الذاتي:\n"
    for app_name, data in list(self_deleting_apps.items()):
        if app_name in self_deleting_apps:
            elapsed_time = (datetime.now(pytz.timezone('Asia/Baghdad')) - data['start_time']).total_seconds() // 60
            remaining_minutes = max(data['minutes'] - elapsed_time, 0)
            remaining_time_message += f"- {app_name}:\n  الوقت المتبقي: {format_remaining_time(remaining_minutes)}\n  تاريخ الحذف: {calculate_deletion_time(remaining_minutes)}\n"
        else:
            remaining_time_message += f"- {app_name}: تم حذفه."
    bot.edit_message_text(remaining_time_message, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=create_back_button())

# تنسيق الوقت المتبقي
def format_remaining_time(minutes):
    delta = timedelta(minutes=minutes)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} ساعة و{minutes} دقيقة"

# حساب وقت الحذف
def calculate_deletion_time(minutes):
    iraq_timezone = pytz.timezone('Asia/Baghdad')
    now = datetime.now(iraq_timezone)
    deletion_time = now + timedelta(minutes=minutes)
    return deletion_time.strftime("%I:%M %p - %Y-%m-%d")

# قسم جيتهاب
def github_section(call):
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("حذف الكل ❌", callback_data="delete_all_repos")
    button2 = telebot.types.InlineKeyboardButton("حذف مستودع 🗑️", callback_data="delete_repo")
    button3 = telebot.types.InlineKeyboardButton("رفع ملف 📤", callback_data="upload_file")
    markup.add(button1, button2, button3)
    markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back"))
    bot.edit_message_text("قسم جيتهاب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# حذف جميع المستودعات
def delete_all_repos(call):
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers={'Authorization': f'token {github_token}'})
    if response.status_code == 200:
        repos = response.json()
        for repo in repos:
            repo_name = repo['name']
            delete_github_repo(repo_name)
        bot.edit_message_text("تم حذف جميع المستودعات بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    else:
        bot.edit_message_text("حدث خطأ أثناء محاولة جلب المستودعات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# حذف مستودع واحد
def delete_repo(call):
    msg = bot.edit_message_text("يرجى إرسال اسم المستودع لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_repo_name_for_deletion)

def handle_repo_name_for_deletion(message):
    repo_name = message.text.strip()
    if delete_github_repo(repo_name):
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"اسم المستودع `{repo_name}` غير صحيح أو حدث خطأ أثناء الحذف.", parse_mode='Markdown')

# دالة لحذف مستودع من جيتهاب
def delete_github_repo(repo_name):
    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{repo_name}', headers={'Authorization': f'token {github_token}'})
    return response.status_code == 204

# رفع ملف
def upload_file(call):
    msg = bot.edit_message_text("يرجى إرسال الملف المضغوط (zip) لرفعه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_file_upload)

def handle_file_upload(message):
    if message.document and message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_content = io.BytesIO(downloaded_file)
        with zipfile.ZipFile(file_content, 'r') as zip_ref:
            zip_ref.extractall("/tmp/uploaded_files")
        repo_name = f"uploaded_repo_{int(time.time())}"
        create_github_repo_and_upload_files(repo_name, "/tmp/uploaded_files")
        num_files = len(os.listdir("/tmp/uploaded_files"))
        bot.send_message(message.chat.id, f"تم إنشاء المستودع `{repo_name}` بنجاح بعدد {num_files} ملفات.", parse_mode='Markdown')
        os.system("rm -rf /tmp/uploaded_files")
    else:
        bot.send_message(message.chat.id, "يرجى إرسال ملف مضغوط بصيغة zip.", reply_markup=create_back_button())

# دالة لإنشاء مستودع جديد على جيتهاب ورفع الملفات إليه
def create_github_repo_and_upload_files(repo_name, directory):
    response = requests.post(f'{GITHUB_BASE_URL}/user/repos', headers={'Authorization': f'token {github_token}'}, json={'name': repo_name, 'private': False})
    if response.status_code == 201:
        for filenamein os.listdir(directory):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'rb') as file:
                content = file.read()
                encoded_content = base64.b64encode(content).decode('utf-8')
                commit_message = f"Adding {filename}"
                requests.put(
                    f'{GITHUB_BASE_URL}/repos/{github_username}/{repo_name}/contents/{filename}',
                    headers={'Authorization': f'token {github_token}'},
                    json={'message': commit_message, 'content': encoded_content}
                )

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_accounts:
        user_accounts[user_id] = []
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_main_buttons())

# إضافة زر قسم جيتهاب
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("إضافة حساب ➕", callback_data="add_account")
    button2 = telebot.types.InlineKeyboardButton("حساباتك 🗂️", callback_data="list_accounts")
    button3 = telebot.types.InlineKeyboardButton("قسم جيتهاب", callback_data="github_section")
    markup.add(button1, button2, button3)
    return markup

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"إدارة حساب {account_index + 1}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_heroku_apps_"):
        list_heroku_apps(call)
    elif call.data.startswith("delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_deletion(m, account_index))
    elif call.data.startswith("self_delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق للحذف الذاتي:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_self_deletion(m, account_index))
    elif call.data == "remaining_time":
        show_remaining_time(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    elif call.data == "github_section":
        github_section(call)
    elif call.data == "delete_all_repos":
        delete_all_repos(call)
    elif call.data == "delete_repo":
        delete_repo(call)
    elif call.data == "upload_file":
        upload_file(call)

# التشغيل
if __name__ == "__main__":
    bot.polling()
