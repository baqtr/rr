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
from datetime import datetime, timedelta
import pytz
from github import Github

# استيراد توكن البوت والرمز المميز لـ GitHub من المتغيرات البيئية
bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7913039979:AAFFCNwsBkxPUZNRKlf12reHl8T-d4X-xms")
github_token = os.getenv("GITHUB_TOKEN", "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")

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'

# قائمة التطبيقات المجدولة للحذف الذاتي
self_deleting_apps = {}
g = Github(github_token)

# تخزين حسابات المستخدم
user_accounts = {}

# قائمة لتخزين الأحداث
events = []

# دالة لإنشاء الأزرار وتخصيصها مع تأثيرات بصرية
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    button1 = telebot.types.InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")
    button2 = telebot.types.InlineKeyboardButton("🗂️ حساباتك", callback_data="list_accounts")
    button3 = telebot.types.InlineKeyboardButton("🛠️ قسم جيتهاب", callback_data="github_section")
    button4 = telebot.types.InlineKeyboardButton("🔄 الأحداث", callback_data="show_events")
    button5 = telebot.types.InlineKeyboardButton("⚙️ الإعدادات المتقدمة", callback_data="advanced_settings")
    markup.add(button1, button2, button3, button4, button5)
    return markup

def create_advanced_settings_buttons():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    heroku_info_button = telebot.types.InlineKeyboardButton("📄 جلب معلومات حساب هيروكو", callback_data="fetch_heroku_info")
    github_info_button = telebot.types.InlineKeyboardButton("📄 جلب معلومات جيتهاب", callback_data="fetch_github_info")
    clear_events_button = telebot.types.InlineKeyboardButton("🗑️ حذف الأحداث", callback_data="clear_events")
    markup.add(heroku_info_button, github_info_button, clear_events_button)
    markup.add(telebot.types.InlineKeyboardButton("↩️ العودة للقائمة الرئيسية", callback_data="go_back_main"))
    return markup

def create_github_control_buttons():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    delete_all_button = telebot.types.InlineKeyboardButton("🗑️ حذف الكل", callback_data="delete_all_repos")
    delete_repo_button = telebot.types.InlineKeyboardButton("🗑️ حذف مستودع", callback_data="delete_repo")
    upload_file_button = telebot.types.InlineKeyboardButton("📤 رفع ملف", callback_data="upload_file")
    list_repos_button = telebot.types.InlineKeyboardButton("📂 عرض المستودعات", callback_data="list_github_repos")
    markup.add(delete_all_button, delete_repo_button, upload_file_button, list_repos_button)
    markup.add(telebot.types.InlineKeyboardButton("↩️ العودة", callback_data="go_back"))
    return markup

# دالة لإنشاء زر العودة
def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton("↩️ العودة", callback_data="go_back")
    markup.add(back_button)
    return markup

# دالة لإنشاء أزرار التحكم بالحسابات
def create_account_control_buttons(account_index):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    button1 = telebot.types.InlineKeyboardButton("📦 جلب تطبيقات هيروكو", callback_data=f"list_heroku_apps_{account_index}")
    button2 = telebot.types.InlineKeyboardButton("❌ حذف تطبيق", callback_data=f"delete_app_{account_index}")
    button3 = telebot.types.InlineKeyboardButton("⏲️ الحذف الذاتي", callback_data=f"self_delete_app_{account_index}")
    button4 = telebot.types.InlineKeyboardButton("⏳ الوقت المتبقي", callback_data="remaining_time")
    markup.add(button1, button2, button3, button4)
    markup.add(telebot.types.InlineKeyboardButton("↩️ العودة", callback_data="list_accounts"))
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_accounts:
        user_accounts[user_id] = []
        events.append(f"انضم مستخدم جديد: [{message.from_user.first_name}](tg://user?id={user_id})")
    welcome_text = (
        "🌟 أهلاً وسهلاً بك في البوت! 🌟\n"
        "اختر من بين الأزرار أدناه لتبدأ:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_buttons())

# دالة لإضافة حساب جديد
def add_account(call):
    msg = bot.edit_message_text("يرجى إرسال مفتاح API الخاص بحساب Heroku:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_new_account)

def handle_new_account(message):
    api_key = message.text.strip()
    user_id = message.from_user.id
    if api_key in [account['api_key'] for account in user_accounts[user_id]]:
        bot.send_message(message.chat.id, "⚠️ هذا الحساب مضاف مسبقًا.", reply_markup=create_main_buttons())
    elif validate_heroku_api_key(api_key):
        user_accounts[user_id].append({'api_key': api_key})
        events.append(f"أضاف [{message.from_user.first_name}](tg://user?id={user_id}) حساب جديد: `{api_key[:-4]}****`")
        bot.send_message(message.chat.id, "✅ تمت إضافة حساب Heroku بنجاح!", reply_markup=create_main_buttons())
    else:
        bot.send_message(message.chat.id, "❌ مفتاح API غير صحيح. يرجى المحاولة مرة أخرى.", reply_markup=create_main_buttons())

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
        markup.add(telebot.types.InlineKeyboardButton("↩️ العودة", callback_data="go_back_main"))
        bot.edit_message_text(f"🔐 حساباتك:\n{accounts_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.edit_message_text("🚫 لا توجد حسابات مضافة.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

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
        bot.edit_message_text("🚫 لا توجد حسابات مضافة. يرجى إضافة حساب أولاً.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        return

    headers = {
        'Authorization': f'Bearer {user_accounts[user_id][account_index]["api_key"]}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    bot.edit_message_text("⬛⬜ جلب التطبيقات... 0%", chat_id=call.message.chat.id, message_id=call.message.message_id)
    time.sleep(2)
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.edit_message_text("⬛⬛ جلب التطبيقات... 50%", chat_id=call.message.chat.id, message_id=call.message.message_id)
        time.sleep(2)
        bot.edit_message_text(f"📦 التطبيقات المتاحة في هيروكو:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("❌ حدث خطأ في جلب التطبيقات من هيروكو.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data == "show_events":
        show_events(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"⚙️ إدارة حساب {account_index + 1}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
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
        list_accounts(call)
    elif call.data == "go_back_main":
        bot.edit_message_text("🌟 مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    elif call.data == "github_section":
        bot.edit_message_text("🛠️ قسم جيتهاب:\nيرجى اختيار إحدى الخيارات:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())
    elif call.data == "upload_file":
        msg = bot.send_message(call.message.chat.id, "يرجى إرسال ملف مضغوط بصيغة ZIP.")
        bot.register_next_step_handler(msg, handle_zip_file)
    elif call.data == "list_github_repos":
        list_github_repos(call)
    elif call.data == "delete_repo":
        msg = bot.send_message(call.message.chat.id, "يرجى إرسال اسم المستودع لحذفه.")
        bot.register_next_step_handler(msg, handle_repo_deletion)
    elif call.data == "delete_all_repos":
        delete_all_repos(call)
    elif call.data == "advanced_settings":
        bot.edit_message_text("⚙️ الإعدادات المتقدمة:\nاختر إحدى الخيارات:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_advanced_settings_buttons())
    elif call.data == "fetch_heroku_info":
        fetch_heroku_info(call)
    elif call.data == "fetch_github_info":
        fetch_github_info(call)
    elif call.data == "clear_events":
        clear_events(call)

# دالة الحذف
def handle_app_name_for_deletion(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    if validate_heroku_app(app_name, account_index, user_id):
        delete_heroku_app(app_name, message, account_index)
    else:
        bot.send_message(message.chat.id, f"❌ اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

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
            bot.send_message(message.chat.id, f"⚠️ تم وضع التطبيق `{app_name}` مسبقًا في قائمة الحذف الذاتي.", parse_mode='Markdown')
        else:
            msg = bot.send_message(message.chat.id, "يرجى إدخال الوقت المطلوب بالدقائق لحذف التطبيق:")
            bot.register_next_step_handler(msg, lambda m: handle_self_deletion_time(m, app_name, account_index))
    else:
        bot.send_message(message.chat.id, f"❌ اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة لمعالجة الوقت للحذف الذاتي
def handle_self_deletion_time(message, app_name, account_index):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
        self_deleting_apps[app_name] = {'minutes': minutes, 'start_time': datetime.now(pytz.timezone('Asia/Baghdad'))}
        bot.send_message(message.chat.id, f"⏳ سيتم حذف التطبيق `{app_name}` بعد {minutes} دقيقة.\n", reply_markup=create_remaining_time_button())
        # بدء عملية الحذف الذاتي
        threading.Timer(minutes * 60, lambda: delete_and_remove_app(app_name, message, account_index)).start()
    except ValueError:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال عدد صحيح إيجابي للدقائق.")

# زر عرض الوقت المتبقي
def create_remaining_time_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("⏳ الوقت المتبقي", callback_data="remaining_time")
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
        bot.send_message(message.chat.id, f"✅ تم حذف التطبيق `{app_name}` بنجاح.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء محاولة حذف التطبيق.")

# عرض الوقت المتبقي للحذف الذاتي
def show_remaining_time(call):
    remaining_time_message = "⏳ التطبيقات المجدولة للحذف الذاتي:\n"
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

def list_github_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    repo_list = ""
    loading_message = bot.send_message(call.message.chat.id, "🔄 جارٍ جلب المستودعات، يرجى الانتظار...")

    for repo in repos:
        try:
            contents = repo.get_contents("")
            num_files = sum(1 for _ in contents)
            repo_list += f"📂 *اسم المستودع*: `{repo.name}`\n📁 *عدد الملفات*: {num_files}\n\n"
        except:
            pass

    if repo_list:
        bot.edit_message_text(f"📂 مستودعات GitHub:\n{repo_list}", chat_id=call.message.chat.id, message_id=loading_message.message_id, parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.edit_message_text("🚫 لا توجد مستودعات لعرضها.", chat_id=call.message.chat.id, message_id=loading_message.message_id, parse_mode='Markdown', reply_markup=create_back_button())

def handle_zip_file(message):
    if message.document and message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, message.document.file_name)
            with open(zip_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                repo_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                user = g.get_user()
                repo = user.create_repo(repo_name, private=True)
                
                for root, dirs, files in os.walk(temp_dir):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        relative_path = os.path.relpath(file_path, temp_dir)
                        with open(file_path, 'rb') as file_data:
                            repo.create_file(relative_path, f"Add {relative_path}", file_data.read())
                
                num_files = sum([len(files) for r, d, files in os.walk(temp_dir)])
                bot.send_message(message.chat.id, f"✅ تم إنشاء المستودع بنجاح.\nاسم المستودع: `{repo_name}`\nعدد الملفات: {num_files}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ الملف الذي تم إرساله ليس ملف ZIP. يرجى المحاولة مرة أخرى.")

# دالة لعرض الأحداث
def show_events(call):
    if not events:
        bot.edit_message_text("🚫 لا توجد أحداث لعرضها.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    else:
        events_list = "\n".join(events)
        bot.edit_message_text(f"📝 الأحداث:\n{events_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')

# دالة لجلب معلومات هيروكو
def fetch_heroku_info(call):
    user_id = call.from_user.id
    if user_id in user_accounts and user_accounts[user_id]:
        markup = telebot.types.InlineKeyboardMarkup()
        for index in range(len(user_accounts[user_id])):
            account_name = get_heroku_account_name(user_accounts[user_id][index]['api_key'])
            markup.add(telebot.types.InlineKeyboardButton(f"{account_name}", callback_data=f"heroku_info_{index}"))
        markup.add(telebot.types.InlineKeyboardButton("↩️ العودة", callback_data="advanced_settings"))
        bot.edit_message_text("🔍 اختر الحساب لجلب المعلومات:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        bot.edit_message_text("🚫 لا توجد حسابات مضافة.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

@bot.callback_query_handler(func=lambda call: call.data.startswith("heroku_info_"))
def heroku_info(call):
    account_index = int(call.data.split("_")[-1])
    user_id = call.from_user.id
    api_key = user_accounts[user_id][account_index]['api_key']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    
    account_response = requests.get(f'{HEROKU_BASE_URL}/account', headers=headers)
    apps_response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)

    if account_response.status_code == 200 and apps_response.status_code == 200:
        account_info = account_response.json()
        apps_info = apps_response.json()

        num_apps = len(apps_info)
        connected_to_github = sum(1 for app in apps_info if app.get('repo_size', 0) > 0)

        message = (
            f"🔍 معلومات حساب هيروكو:\n"
            f"📧 البريد الإلكتروني: {account_info.get('email', 'غير معروف')}\n"
            f"💳 الفاتورة: {account_info.get('billing', {}).get('payment_method', 'غير متوفر')}\n"
            f"🔗 متصل بجيتهاب: {'نعم' if connected_to_github > 0 else 'لا'}\n"
            f"📦 عدد التطبيقات: {num_apps}\n"
            f"📦 التطبيقات المرتبطة بجيتهاب: {connected_to_github}\n"
        )
        bot.edit_message_text(message, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("❌ حدث خطأ أثناء جلب معلومات الحساب.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لجلب معلومات جيتهاب
def fetch_github_info(call):
    user = g.get_user()
    repos = user.get_repos()

    public_repos_count = user.public_repos
    private_repos_count = user.total_private_repos

    message = (
        f"🔍 معلومات جيتهاب:\n"
        f"👤 المستخدم: {user.login}\n"
        f"📂 المستودعات العامة: {public_repos_count}\n"
        f"🔒 المستودعات الخاصة: {private_repos_count}\n"
    )

    bot.edit_message_text(message, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')

# دالة لحذف الأحداث
def clear_events(call):
    num_events = len(events)
    if num_events > 0:
        events.clear()
        bot.edit_message_text(f"🗑️ تم حذف {num_events} حدث بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    else:
        bot.edit_message_text("🚫 لا توجد أحداث لحذفها.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

def handle_repo_deletion(message):
    repo_name = message.text.strip()
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
        repo.delete()
        bot.send_message(message.chat.id, f"🗑️ تم حذف المستودع `{repo_name}` بنجاح.", parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id, f"❌ المستودع `{repo_name}` غير موجود أو لا تملك صلاحية حذفه.", parse_mode='Markdown')

# دالة لحذف جميع المستودعات
def delete_all_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    repo_count = repos.totalCount
    for repo in repos:
        repo.delete()
    bot.edit_message_text(f"🗑️ تم حذف جميع المستودعات بنجاح.\nعدد المستودعات المحذوفة: {repo_count}", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=create_back_button())

# التشغيل
if __name__ == "__main__":
    bot.polling()
