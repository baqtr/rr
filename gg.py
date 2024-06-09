import os
import telebot
import requests
import threading
import time
import pytz
import psycopg2
from datetime import datetime, timedelta

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAF-BrYHNEcX8VyGBzY1mastEG3SWod4_uI"
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
    markup.add(button1, button2)
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
    msg = bot.edit_message_text("يرجى إرسال اسم التطبيق الذي تريد حذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, lambda message: handle_delete_app(message, account_index))

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
        bot.send_message(message.chat.id, "فشل في حذف التطبيق. تأكد من صحة اسم التطبيق.", reply_markup=create_main_buttons())

# دالة لإعداد الحذف الذاتي
def self_delete_app(call, account_index):
    msg = bot.edit_message_text("يرجى إرسال اسم التطبيق ومدة الحذف الذاتي بالدقائق (مثال: app_name 30):", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, lambda message: handle_self_delete_app(message, account_index))

def handle_self_delete_app(message, account_index):
    try:
        app_name, minutes = message.text.strip().split()
        minutes = int(minutes)
        user_id = message.from_user.id
        api_key = load_accounts(user_id)[account_index]
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/vnd.heroku+json; version=3'
        }
        response = requests.get(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
        if response.status_code == 200:
            save_self_deleting_app(app_name, minutes)
            bot.send_message(message.chat.id, f"تم إعداد الحذف الذاتي للتطبيق {app_name} بعد {minutes} دقيقة.", reply_markup=create_main_buttons())
        else:
            bot.send_message(message.chat.id, "اسم التطبيق غير صحيح. تأكد من صحة اسم التطبيق.", reply_markup=create_main_buttons())
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء التأكد من التنسيق الصحيح (مثال: app_name 30).", reply_markup=create_main_buttons())

# دالة لحساب الوقت المتبقي للحذف الذاتي
def remaining_time(call):
    now = datetime.now(pytz.timezone('Asia/Baghdad'))
    apps = load_self_deleting_apps()
    remaining_times = []
    for app_name, data in apps.items():
        end_time = data['start_time'] + timedelta(minutes=data['minutes'])
        remaining = end_time - now
        if remaining.total_seconds() > 0:
            remaining_times.append(f"{app_name}: {remaining}")
        else:
            remove_self_deleting_app(app_name)
    if remaining_times:
        bot.edit_message_text("\n".join(remaining_times), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    else:
        bot.edit_message_text("لا توجد تطبيقات معدة للحذف الذاتي.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# دالة لتنفيذ الحذف الذاتي بشكل دوري
def auto_delete_apps():
    while True:
        now = datetime.now(pytz.timezone('Asia/Baghdad'))
        apps = load_self_deleting_apps()
        for app_name, data in apps.items():
            end_time = data['start_time'] + timedelta(minutes=data['minutes'])
            if now >= end_time:
                # حدد الحساب الذي يجب استخدامه لحذف التطبيق
                cursor.execute('SELECT user_id, api_keys FROM accounts WHERE %s = ANY(api_keys);', (app_name,))
                result = cursor.fetchone()
                if result:
                    user_id, api_keys = result
                    api_key = api_keys[0]  # باستخدام أول مفتاح API لحذف التطبيق
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Accept': 'application/vnd.heroku+json; version=3'
                    }
                    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
                    if response.status_code == 202:
                        remove_self_deleting_app(app_name)
        time.sleep(60)

# بدء خيط الحذف الذاتي
threading.Thread(target=auto_delete_apps, daemon=True).start()

# دالة للاستجابة للضغط على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text("ماذا تريد أن تفعل؟", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_heroku_apps_"):
        account_index = int(call.data.split("_")[-1])
        list_heroku_apps(call, account_index)
    elif call.data.startswith("delete_app_"):
        account_index = int(call.data.split("_")[-1])
        delete_app(call, account_index)
    elif call.data.startswith("self_delete_app_"):
        account_index = int(call.data.split("_")[-1])
        self_delete_app(call, account_index)
    elif call.data == "remaining_time":
        remaining_time(call)
    elif call.data == "go_back":
        bot.edit_message_text("اختار من بين الازرار ماذا تريد", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# بدء تشغيل البوت
bot.polling()
