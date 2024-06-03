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
    elif call.data.startswith("list_heroku_apps_"):
        list_heroku_apps(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"حسابك المختار هو: `{get_heroku_account_name(user_accounts[call.from_user.id][account_index]['api_key'])}`", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index), parse_mode='Markdown')
    elif call.data == "github_section":
        bot.edit_message_text("قسم جيتهاب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())
    elif call.data == "delete_all_repos":
        delete_all_repos(call)
    elif call.data == "delete_repo":
        delete_repo(call)
    elif call.data == "upload_file":
        upload_file(call)
    elif call.data == "list_github_repos":
        list_github_repos(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# دالة لعرض الأحداث
def show_events(call):
    events_list = "\n".join(events)
    bot.edit_message_text(f"الأحداث الأخيرة:\n{events_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')

# دالة لحذف جميع المستودعات في جيتهاب
def delete_all_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    for repo in repos:
        repo.delete()
    bot.edit_message_text("تم حذف جميع مستودعات GitHub بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

# دالة لحذف مستودع معين في جيتهاب
def delete_repo(call):
    msg = bot.edit_message_text("يرجى إرسال اسم المستودع الذي تريد حذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_delete_repo)

def handle_delete_repo(message):
    repo_name = message.text.strip()
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
        repo.delete()
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح.", reply_markup=create_github_control_buttons(), parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء حذف المستودع `{repo_name}`: {e}", reply_markup=create_github_control_buttons(), parse_mode='Markdown')

# دالة لرفع ملف إلى مستودع جيتهاب
def upload_file(call):
    msg = bot.edit_message_text("يرجى إرسال اسم المستودع والمسار المطلوب للملف بصيغة `repository_name:path/to/file`:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_upload_file)

def handle_upload_file(message):
    try:
        repo_path = message.text.strip()
        repo_name, file_path = repo_path.split(":")
        msg = bot.send_message(message.chat.id, "الرجاء إرسال الملف الذي تريد رفعه:")
        bot.register_next_step_handler(msg, lambda m: handle_upload_file_step_2(m, repo_name, file_path))
    except ValueError:
        bot.send_message(message.chat.id, "الصيغة غير صحيحة. يرجى المحاولة مرة أخرى.", reply_markup=create_github_control_buttons())

def handle_upload_file_step_2(message, repo_name, file_path):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        file_content = bot.download_file(file_info.file_path)
        user = g.get_user()
        try:
            repo = user.get_repo(repo_name)
            repo.create_file(file_path, "Upload file via bot", file_content)
            bot.send_message(message.chat.id, f"تم رفع الملف بنجاح إلى `{repo_name}:{file_path}`.", reply_markup=create_github_control_buttons(), parse_mode='Markdown')
        except Exception as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء رفع الملف إلى `{repo_name}:{file_path}`: {e}", reply_markup=create_github_control_buttons(), parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "لم يتم استلام ملف. يرجى المحاولة مرة أخرى.", reply_markup=create_github_control_buttons())

# دالة لعرض مستودعات جيتهاب
def list_github_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    repos_list = "\n".join([f"`{repo.name}`" for repo in repos])
    bot.edit_message_text(f"مستودعات GitHub:\n{repos_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons(), parse_mode='Markdown')

# تشغيل البوت
bot.polling()
