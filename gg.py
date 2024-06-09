import os
import telebot
import requests
import threading
import time
import zipfile
import tempfile
import random
import string
import shutil
import json
from datetime import datetime, timedelta
import pytz
from github import Github
import psycopg2

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAF-BrYHNEcX8VyGBzY1mastEG3SWod4_uI"
github_token = "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"

database_url = os.getenv("DATABASE_URL", "postgres://u7sp4pi4bkcli5:p8084ef55d7306694913f43fe18ae8f1e24bf9d4c33b1bdae2e9d49737ea39976@ec2-18-210-84-56.compute-1.amazonaws.com:5432/dbdstma1phbk1e")


# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'

# إعداد قاعدة البيانات
connection = psycopg2.connect(database_url)
cursor = connection.cursor()

# دالة لإنشاء الجداول إذا لم تكن موجودة
def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        user_id BIGINT PRIMARY KEY,
                        api_keys TEXT[]
                      );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        event TEXT,
                        timestamp TIMESTAMPTZ
                      );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS self_deleting_apps (
                        app_name TEXT PRIMARY KEY,
                        minutes INTEGER,
                        start_time TIMESTAMPTZ
                      );''')
    connection.commit()

create_tables()

# دالة لحفظ البيانات إلى قاعدة البيانات
def save_account(user_id, api_key):
    cursor.execute('''INSERT INTO accounts (user_id, api_keys)
                      VALUES (%s, ARRAY[%s])
                      ON CONFLICT (user_id) DO UPDATE
                      SET api_keys = array_append(accounts.api_keys, %s);''', (user_id, api_key, api_key))
    connection.commit()

def load_accounts(user_id):
    cursor.execute('SELECT api_keys FROM accounts WHERE user_id = %s;', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else []

def save_event(event):
    cursor.execute('''INSERT INTO events (event, timestamp)
                      VALUES (%s, %s);''', (event, datetime.now(pytz.timezone('Asia/Baghdad'))))
    connection.commit()

def load_events():
    cursor.execute('SELECT event FROM events;')
    return [row[0] for row in cursor.fetchall()]

def save_self_deleting_app(app_name, minutes):
    cursor.execute('''INSERT INTO self_deleting_apps (app_name, minutes, start_time)
                      VALUES (%s, %s, %s);''', (app_name, minutes, datetime.now(pytz.timezone('Asia/Baghdad'))))
    connection.commit()

def load_self_deleting_apps():
    cursor.execute('SELECT app_name, minutes, start_time FROM self_deleting_apps;')
    return {row[0]: {'minutes': row[1], 'start_time': row[2]} for row in cursor.fetchall()}

def remove_self_deleting_app(app_name):
    cursor.execute('DELETE FROM self_deleting_apps WHERE app_name = %s;', (app_name,))
    connection.commit()

# قائمة لتخزين الأحداث في الذاكرة
events = []

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("إضافة حساب ➕", callback_data="add_account")
    button2 = telebot.types.InlineKeyboardButton("حساباتك 🗂️", callback_data="list_accounts")
    button3 = telebot.types.InlineKeyboardButton("قسم جيتهاب 🛠️", callback_data="github_section")
    button4 = telebot.types.InlineKeyboardButton("الأحداث 🔄", callback_data="show_events")
    markup.add(button1, button2)
    markup.add(button3)
    markup.add(button4)
    return markup

def create_github_control_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    delete_all_button = telebot.types.InlineKeyboardButton("حذف الكل 🗑️", callback_data="delete_all_repos")
    delete_repo_button = telebot.types.InlineKeyboardButton("حذف مستودع 🗑️", callback_data="delete_repo")
    upload_file_button = telebot.types.InlineKeyboardButton("رفع ملف 📤", callback_data="upload_file")
    list_repos_button = telebot.types.InlineKeyboardButton(" عرض المستودعات 📂", callback_data="list_github_repos")
    markup.row(delete_all_button, delete_repo_button)
    markup.row(upload_file_button)
    markup.add(list_repos_button)
    markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back"))
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
    if not load_accounts(user_id):
        save_account(user_id, '')
        save_event(f"انضم مستخدم جديد: [{message.from_user.first_name}](tg://user?id={user_id})")
    bot.send_message(message.chat.id, "اهلا وسهلا نورتنا اختار من بين الازرار ماذا تريد", reply_markup=create_main_buttons())

# دالة لإضافة حساب جديد
def add_account(call):
    msg = bot.edit_message_text("يرجى إرسال مفتاح API الخاص بحساب Heroku:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_new_account)

def handle_new_account(message):
    api_key = message.text.strip()
    user_id = message.from_user.id
    if api_key in load_accounts(user_id):
        bot.send_message(message.chat.id, "هذا الحساب مضاف مسبقًا.", reply_markup=create_main_buttons())
    elif validate_heroku_api_key(api_key):
        save_account(user_id, api_key)
        save_event(f"أضاف [{message.from_user.first_name}](tg://user?id={user_id}) حساب جديد: `{api_key[:-4]}****`")
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
    api_keys = load_accounts(user_id)
    if api_keys:
        accounts_list = "\n".join([f"حساب {index + 1}: `{get_heroku_account_name(api_key)}`" for index, api_key in enumerate(api_keys)])
        markup = telebot.types.InlineKeyboardMarkup()
        for index in range(len(api_keys)):
            account_name = get_heroku_account_name(api_keys[index])
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
def list_heroku_apps(call, account_index):
    user_id = call.from_user.id
    api_key = load_accounts(user_id)[account_index]
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    if response.status_code == 200:
        apps = response.json()
        if apps:
            apps_list = "\n".join([f"تطبيق: {app['name']}" for app in apps])
            bot.edit_message_text(f"تطبيقاتك:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
        else:
            bot.edit_message_text("لا توجد تطبيقات في هذا الحساب.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    else:
        bot.edit_message_text("فشل في جلب التطبيقات. تأكد من صحة مفتاح API.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))

# دالة لحذف تطبيق
def delete_app(call, account_index):
    msg = bot.send_message(call.message.chat.id, "يرجى إرسال اسم التطبيق الذي تريد حذفه:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, lambda m: handle_delete_app(m, account_index))

def handle_delete_app(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    api_key = load_accounts(user_id)[account_index]
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
    if response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق {app_name} بنجاح.", reply_markup=create_main_buttons())
    else:
        bot.send_message(message.chat.id, f"فشل في حذف التطبيق {app_name}. تأكد من صحة اسم التطبيق.", reply_markup=create_main_buttons())

# دالة لتفعيل الحذف الذاتي للتطبيق
def self_delete_app(call, account_index):
    msg = bot.send_message(call.message.chat.id, "يرجى إرسال اسم التطبيق وعدد الدقائق (بصيغة 'app_name,minutes'):", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, lambda m: handle_self_delete_app(m, account_index))

def handle_self_delete_app(message, account_index):
    try:
        app_name, minutes = map(str.strip, message.text.split(','))
        minutes = int(minutes)
        save_self_deleting_app(app_name, minutes)
        user_id = message.from_user.id
        api_key = load_accounts(user_id)[account_index]
        threading.Thread(target=auto_delete_app, args=(app_name, minutes, api_key)).start()
        bot.send_message(message.chat.id, f"تم تفعيل الحذف الذاتي للتطبيق {app_name} بعد {minutes} دقيقة.", reply_markup=create_main_buttons())
    except ValueError:
        bot.send_message(message.chat.id, "صيغة غير صحيحة. يرجى المحاولة مرة أخرى.", reply_markup=create_main_buttons())

# دالة لحذف التطبيق تلقائيًا
def auto_delete_app(app_name, minutes, api_key):
    time.sleep(minutes * 60)
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
    if response.status_code == 202:
        remove_self_deleting_app(app_name)

# دالة لعرض الوقت المتبقي للتطبيقات المحذوفة ذاتيًا
def show_remaining_time(call):
    apps = load_self_deleting_apps()
    if apps:
        remaining_times = []
        for app_name, info in apps.items():
            elapsed_time = datetime.now(pytz.timezone('Asia/Baghdad')) - info['start_time']
            remaining_minutes = info['minutes'] - int(elapsed_time.total_seconds() // 60)
            if remaining_minutes > 0:
                remaining_times.append(f"التطبيق: {app_name}, الوقت المتبقي: {remaining_minutes} دقيقة")
            else:
                remove_self_deleting_app(app_name)
        if remaining_times:
            bot.edit_message_text("\n".join(remaining_times), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        else:
            bot.edit_message_text("لا توجد تطبيقات محذوفة ذاتيًا.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    else:
        bot.edit_message_text("لا توجد تطبيقات محذوفة ذاتيًا.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# عرض الأحداث
def show_events(call):
    events = load_events()
    if events:
        events_text = "\n".join(events)
        bot.edit_message_text(f"الأحداث:\n{events_text}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("لا توجد أحداث.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# عرض المستودعات في جيتهاب
def list_github_repos(call):
    g = Github(github_token)
    user = g.get_user()
    repos = user.get_repos()
    repo_list = "\n".join([f"مستودع: {repo.name}" for repo in repos])
    bot.edit_message_text(f"المستودعات:\n{repo_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

# دالة لحذف جميع المستودعات
def delete_all_repos(call):
    g = Github(github_token)
    user = g.get_user()
    repos = user.get_repos()
    for repo in repos:
        repo.delete()
    bot.edit_message_text("تم حذف جميع المستودعات بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

# دالة لحذف مستودع
def delete_repo(call):
    msg = bot.edit_message_text("يرجى إرسال اسم المستودع الذي تريد حذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_delete_repo)

def handle_delete_repo(message):
    repo_name = message.text.strip()
    g = Github(github_token)
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
        repo.delete()
        bot.send_message(message.chat.id, f"تم حذف المستودع {repo_name} بنجاح.", reply_markup=create_main_buttons())
    except:
        bot.send_message(message.chat.id, f"فشل في حذف المستودع {repo_name}. تأكد من صحة اسم المستودع.", reply_markup=create_main_buttons())

# دالة لرفع ملف إلى جيتهاب
def upload_file(call):
    msg = bot.edit_message_text("يرجى إرسال اسم المستودع والملف الذي تريد رفعه (بصيغة 'repo_name,file_path'):", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_upload_file)

def handle_upload_file(message):
    try:
        repo_name, file_path = map(str.strip, message.text.split(','))
        g = Github(github_token)
        user = g.get_user()
        repo = user.get_repo(repo_name)
        with open(file_path, 'rb') as file:
            content = file.read()
        repo.create_file(file_path, "Upload file via bot", content)
        bot.send_message(message.chat.id, f"تم رفع الملف إلى المستودع {repo_name} بنجاح.", reply_markup=create_main_buttons())
    except Exception as e:
        bot.send_message(message.chat.id, f"فشل في رفع الملف. تأكد من صحة اسم المستودع ومسار الملف.", reply_markup=create_main_buttons())

# دالة للعودة إلى القائمة الرئيسية
def go_back(call):
    bot.edit_message_text("اهلا وسهلا نورتنا اختار من بين الازرار ماذا تريد", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# التعامل مع الردود على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data == "github_section":
        bot.edit_message_text("قسم جيتهاب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())
    elif call.data == "show_events":
        show_events(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text("التحكم بالحساب:", chat_id=call.message.chat.id, message_id=call.message.message_idbot.edit_message_text("التحكم بالحساب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_apps_"):
        account_index = int(call.data.split("_")[-1])
        list_heroku_apps(call, account_index)
    elif call.data.startswith("delete_app_"):
        account_index = int(call.data.split("_")[-1])
        delete_app(call, account_index)
    elif call.data.startswith("self_delete_app_"):
        account_index = int(call.data.split("_")[-1])
        self_delete_app(call, account_index)
    elif call.data == "show_remaining_time":
        show_remaining_time(call)
    elif call.data == "list_repos":
        list_github_repos(call)
    elif call.data == "delete_all_repos":
        delete_all_repos(call)
    elif call.data == "delete_repo":
        delete_repo(call)
    elif call.data == "upload_file":
        upload_file(call)
    elif call.data == "go_back":
        go_back(call)

# بدء البوت
if __name__ == "__main__":
    bot.polling(none_stop=True)
