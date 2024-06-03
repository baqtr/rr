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

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
github_token = "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"

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'

g = Github(github_token)
# قائمة التطبيقات المجدولة للحذف الذاتي
self_deleting_apps = {}

# تخزين حسابات المستخدم
user_accounts = {}

# قائمة لتخزين الأحداث
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
    list_repos_button = telebot.types.InlineKeyboardButton("عرض مستودعات GitHub 📂", callback_data="list_github_repos")
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
    if user_id not in user_accounts:
        user_accounts[user_id] = []
        events.append(f"انضم مستخدم جديد: [{message.from_user.first_name}](tg://user?id={user_id})")
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
        events.append(f"أضاف [{message.from_user.first_name}](tg://user?id={user_id}) حساب جديد: `{api_key[:-4]}****`")
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
    elif call.data == "show_events":
        show_events(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"تم اختيار حساب {account_index + 1}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_heroku_apps_"):
        list_heroku_apps(call)
    elif call.data == "github_section":
        show_github_section(call)
    elif call.data == "delete_all_repos":
        confirm_delete_all_repos(call)
    elif call.data == "delete_repo":
        confirm_delete_repo(call)
    elif call.data == "upload_file":
        prompt_for_file_upload(call)
    elif call.data == "list_github_repos":
        list_github_repos(call)
    elif call.data == "go_back":
        bot.edit_message_text("تم الرجوع", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    elif call.data == "remaining_time":
        show_remaining_time(call)

def show_events(call):
    if events:
        events_list = "\n".join(events)
        bot.edit_message_text(f"الأحداث:\n{events_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("لا توجد أحداث حتى الآن.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

def show_github_section(call):
    bot.edit_message_text("قسم جيتهاب", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

def confirm_delete_all_repos(call):
    markup = telebot.types.InlineKeyboardMarkup()
    yes_button = telebot.types.InlineKeyboardButton("نعم ✅", callback_data="confirm_delete_all_repos_yes")
    no_button = telebot.types.InlineKeyboardButton("لا ❌", callback_data="github_section")
    markup.add(yes_button, no_button)
    bot.edit_message_text("هل أنت متأكد من أنك تريد حذف جميع المستودعات؟", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

def confirm_delete_repo(call):
    bot.send_message(call.message.chat.id, "يرجى إرسال اسم المستودع المراد حذفه:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_delete_repo)

def handle_delete_repo(message):
    repo_name = message.text.strip()
    try:
        repo = g.get_user().get_repo(repo_name)
        repo.delete()
        bot.send_message(message.chat.id, f"تم حذف المستودع '{repo_name}' بنجاح.", reply_markup=create_main_buttons())
    except:
        bot.send_message(message.chat.id, f"فشل في حذف المستودع '{repo_name}'. تأكد من الاسم وحاول مرة أخرى.", reply_markup=create_main_buttons())

def prompt_for_file_upload(call):
    bot.send_message(call.message.chat.id, "يرجى إرسال الملف المراد رفعه:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_file_upload)

def handle_file_upload(message):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(downloaded_file)
            temp_file_name = temp_file.name
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("نعم ✅", callback_data=f"confirm_upload_file_{temp_file_name}"))
        markup.add(telebot.types.InlineKeyboardButton("لا ❌", callback_data="github_section"))
        bot.send_message(message.chat.id, "هل ترغب في رفع هذا الملف إلى جيتهاب؟", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "الملف غير مدعوم. يرجى المحاولة مرة أخرى.")

def list_github_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    repos_list = "\n".join([repo.name for repo in repos])
    bot.edit_message_text(f"مستودعات جيتهاب:\n{repos_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

def show_remaining_time(call):
    user_id = call.from_user.id
    if user_id in self_deleting_apps:
        apps_info = self_deleting_apps[user_id]
        remaining_times = "\n".join([f"تطبيق {app_name} سيتم حذفه في {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(delete_time))}" for app_name, delete_time in apps_info.items()])
        bot.edit_message_text(f"الوقت المتبقي للتطبيقات:\n{remaining_times}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    else:
        bot.edit_message_text("لا توجد تطبيقات مجدولة للحذف الذاتي.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_upload_file_"))
def confirm_upload_file(call):
    temp_file_name = call.data.split("_")[-1]
    user = g.get_user()
    try:
        repo_name = f"uploaded_file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        repo = user.create_repo(repo_name)
        with open(temp_file_name, "rb") as file:
            content = file.read()
        repo.create_file("uploaded_file.zip", "Initial commit", content)
        bot.edit_message_text(f"تم رفع الملف إلى مستودع جديد '{repo_name}' بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    except Exception as e:
        bot.edit_message_text(f"فشل في رفع الملف إلى جيتهاب. الخطأ: {e}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    finally:
        os.remove(temp_file_name)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete_all_repos_yes")
def delete_all_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    for repo in repos:
        repo.delete()
    bot.edit_message_text("تم حذف جميع المستودعات بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

bot.polling()
