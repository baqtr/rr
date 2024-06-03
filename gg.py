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
# تخزين نسخ الاحتياطية لكل مستخدم
user_backups = {}
# تخزين حالة الوضع الامن لكل مستخدم
user_safe_mode = {}

# قائمة لتخزين الأحداث
events = []

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("إضافة حساب ➕", callback_data="add_account")
    button2 = telebot.types.InlineKeyboardButton("حساباتك 🗂️", callback_data="list_accounts")
    button3 = telebot.types.InlineKeyboardButton("قسم جيتهاب 🛠️", callback_data="github_section")
    button4 = telebot.types.InlineKeyboardButton("الأحداث 🔄", callback_data="show_events")
    button5 = telebot.types.InlineKeyboardButton("الإعدادات ⚙", callback_data="settings")
    button6 = telebot.types.InlineKeyboardButton("المطور ✅", url="https://t.me/xx44g")
    markup.add(button1, button2)
    markup.add(button3)
    markup.add(button4, button5)
    markup.add(button6)
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

# دالة لإنشاء أزرار الإعدادات
def create_settings_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    backup_button = telebot.types.InlineKeyboardButton("إنشاء نسخة احتياطية 💾", callback_data="create_backup")
    restore_button = telebot.types.InlineKeyboardButton("استعادة نسخة احتياطية ♻️", callback_data="restore_backup")
    delete_accounts_button = telebot.types.InlineKeyboardButton("حذف جميع الحسابات ❌", callback_data="delete_all_accounts")
    safe_mode_button = telebot.types.InlineKeyboardButton("الوضع الآمن: معطل ❌", callback_data="toggle_safe_mode")
    markup.add(backup_button)
    markup.add(restore_button)
    markup.add(delete_accounts_button)
    markup.add(safe_mode_button)
    markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back"))
    return markup

# دالة لإعداد الوضع الآمن لكل مستخدم
def initialize_safe_mode(user_id):
    if user_id not in user_safe_mode:
        user_safe_mode[user_id] = False

# دالة لتحديث زر الوضع الآمن
def update_safe_mode_button(user_id):
    safe_mode_status = "مفعل ✅" if user_safe_mode[user_id] else "معطل ❌"
    return telebot.types.InlineKeyboardButton(f"الوضع الآمن: {safe_mode_status}", callback_data="toggle_safe_mode")

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_accounts:
        user_accounts[user_id] = []
        events.append(f"انضم مستخدم جديد: [{message.from_user.first_name}](tg://user?id={user_id})")
    initialize_safe_mode(user_id)
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
    user_id = call.from_user.id
    account_index = int(call.data.split('_')[-1])
    api_key = user_accounts[user_id][account_index]['api_key']
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"تطبيق: `{app['name']}`" for app in apps])
        bot.edit_message_text(f"تطبيقات هيروكو:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("فشل في جلب التطبيقات. يرجى المحاولة مرة أخرى.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لحذف تطبيق هيروكو
def delete_app(call):
    msg = bot.edit_message_text("يرجى إرسال اسم التطبيق الذي تريد حذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    account_index = int(call.data.split('_')[-1])
    bot.register_next_step_handler(msg, handle_delete_app, account_index)

def handle_delete_app(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    api_key = user_accounts[user_id][account_index]['api_key']
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
    
    if response.status_code == 200:
        bot.send_message(message.chat.id, f"تم حذف التطبيق {app_name} بنجاح.", reply_markup=create_main_buttons())
    else:
        bot.send_message(message.chat.id, f"فشل في حذف التطبيق {app_name}. يرجى المحاولة مرة أخرى.", reply_markup=create_main_buttons())

# دالة لتفعيل الحذف الذاتي لتطبيق هيروكو
def self_delete_app(call):
    msg = bot.edit_message_text("يرجى إرسال اسم التطبيق الذي تريد تفعيله للحذف الذاتي:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    account_index = int(call.data.split('_')[-1])
    bot.register_next_step_handler(msg, handle_self_delete_app, account_index)

def handle_self_delete_app(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    api_key = user_accounts[user_id][account_index]['api_key']
    
    # تحديد الوقت بعد 24 ساعة للحذف الذاتي
    delete_time = datetime.now(pytz.utc) + timedelta(hours=24)
    self_deleting_apps[app_name] = {
        'api_key': api_key,
        'delete_time': delete_time
    }
    bot.send_message(message.chat.id, f"تم تعيين الحذف الذاتي للتطبيق {app_name} بعد 24 ساعة.", reply_markup=create_main_buttons())

# دالة لعرض الوقت المتبقي للحذف الذاتي
def show_remaining_time(call):
    remaining_times = []
    current_time = datetime.now(pytz.utc)
    for app_name, info in self_deleting_apps.items():
        time_diff = info['delete_time'] - current_time
        remaining_hours, remainder = divmod(time_diff.seconds, 3600)
        remaining_minutes, _ = divmod(remainder, 60)
        remaining_times.append(f"التطبيق {app_name}: {time_diff.days} يوم، {remaining_hours} ساعة، {remaining_minutes} دقيقة")
    
    if remaining_times:
        remaining_time_message = "\n".join(remaining_times)
    else:
        remaining_time_message = "لا توجد تطبيقات مفعلة للحذف الذاتي."
    
    bot.edit_message_text(remaining_time_message, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')

# دالة لحذف جميع الحسابات
def delete_all_accounts(call):
    user_id = call.from_user.id
    user_accounts[user_id] = []
    events.append(f"حذف جميع الحسابات الخاصة بالمستخدم: [{call.from_user.first_name}](tg://user?id={user_id})")
    bot.edit_message_text("تم حذف جميع الحسابات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# دالة لعرض قسم جيتهاب
def show_github_section(call):
    bot.edit_message_text("مرحبا بك في قسم GitHub. اختر الإجراء المطلوب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

# دالة لحذف جميع المستودعات في جيتهاب
def delete_all_repos(call):
    user_id = call.from_user.id
    repos = g.get_user().get_repos()
    for repo in repos:
        repo.delete()
    bot.edit_message_text("تم حذف جميع المستودعات بنجاح.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

# دالة لحذف مستودع معين في جيتهاب
def delete_repo(call):
    msg = bot.edit_message_text("يرجى إرسال اسم المستودع الذي تريد حذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_delete_repo)

def handle_delete_repo(message):
    repo_name = message.text.strip()
    try:
        repo = g.get_user().get_repo(repo_name)
        repo.delete()
        bot.send_message(message.chat.id, f"تم حذف المستودع {repo_name} بنجاح.", reply_markup=create_github_control_buttons())
    except:
        bot.send_message(message.chat.id, f"فشل في حذف المستودع {repo_name}. يرجى المحاولة مرة أخرى.", reply_markup=create_github_control_buttons())

# دالة لرفع ملف إلى جيتهاب
def upload_file(call):
    msg = bot.edit_message_text("يرجى إرسال الملف الذي تريد رفعه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_upload_file)

def handle_upload_file(message):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        repo = g.get_user().get_repo("YOUR_REPO_NAME")
        repo.create_file(message.document.file_name, "commit message", downloaded_file)
        bot.send_message(message.chat.id, f"تم رفع الملف {message.document.file_name} بنجاح.", reply_markup=create_github_control_buttons())
    else:
        bot.send_message(message.chat.id, "فشل في رفع الملف. يرجى المحاولة مرة أخرى.", reply_markup=create_github_control_buttons())

# دالة لعرض مستودعات جيتهاب
def list_github_repos(call):
    user_id = call.from_user.id
    repos = g.get_user().get_repos()
    repos_list = "\n".join([f"مستودع: `{repo.name}`" for repo in repos])
    bot.edit_message_text(f"مستودعات جيتهاب:\n{repos_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons(), parse_mode='Markdown')

# دالة للتبديل بين الوضع الآمن وتشغيله أو إيقافه
def toggle_safe_mode(call):
    user_id = call.from_user.id
    user_safe_mode[user_id] = not user_safe_mode[user_id]
    events.append(f"قام المستخدم [{call.from_user.first_name}](tg://user?id={user_id}) بتغيير حالة الوضع الآمن إلى {'مفعل' if user_safe_mode[user_id] else 'معطل'}")
    bot.edit_message_text("تم تحديث حالة الوضع الآمن.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_settings_buttons())

# دالة لعرض الإعدادات
def show_settings(call):
    user_id = call.from_user.id
    markup = create_settings_buttons()
    markup.inline_keyboard[-2][0] = update_safe_mode_button(user_id)
    bot.edit_message_text("إعدادات الحساب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# دالة لعرض الأحداث
def show_events(call):
    events_list = "\n".join(events[-10:])  # عرض آخر 10 أحداث
    bot.edit_message_text(f"الأحداث:\n{events_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')

# دالة لعرض الخيارات الرئيسية
def go_back(call):
    bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# إعداد الأوامر المتعلقة بالأزرار
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_account'))
def callback_add_account(call):
    add_account(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('list_accounts'))
def callback_list_accounts(call):
    list_accounts(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_account'))
def callback_delete_account(call):
    delete_account(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('list_heroku_apps'))
def callback_list_heroku_apps(call):
    list_heroku_apps(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_app'))
def callback_delete_app(call):
    delete_app(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('self_delete_app'))
def callback_self_delete_app(call):
    self_delete_app(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_remaining_time'))
def callback_show_remaining_time(call):
    show_remaining_time(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_all_accounts'))
def callback_delete_all_accounts(call):
    delete_all_accounts(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_github_section'))
def callback_show_github_section(call):
    show_github_section(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_all_repos'))
def callback_delete_all_repos(call):
    delete_all_repos(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_repo'))
def callback_delete_repo(call):
    delete_repo(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('upload_file'))
def callback_upload_file(call):
    upload_file(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('list_github_repos'))
def callback_list_github_repos(call):
    list_github_repos(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_safe_mode'))
def callback_toggle_safe_mode(call):
    toggle_safe_mode(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_settings'))
def callback_show_settings(call):
    show_settings(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_events'))
def callback_show_events(call):
    show_events(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('go_back'))
def callback_go_back(call):
    go_back(call)

# تشغيل الـ Bot
if __name__ == "__main__":
    bot.polling()
