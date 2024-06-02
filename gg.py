import os
import telebot
import requests
import threading
import time
from datetime import datetime, timedelta
import pytz
import zipfile
import shutil

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
github_token = "YOUR_GITHUB_TOKEN_HERE"

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'

# جيتهاب API
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
    button3 = telebot.types.InlineKeyboardButton("قسم جيتهاب 🌐", callback_data="github_section")
    markup.add(button1, button2)
    markup.add(button3)
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

# دالة لإنشاء زري الحذف للمستودعات
def create_delete_repo_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("حذف الكل 🗑️", callback_data="delete_all_repos")
    button2 = telebot.types.InlineKeyboardButton("حذف مستودع 📁", callback_data="delete_repo")
    markup.add(button1)
    markup.add(button2)
    markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="list_accounts"))
    return markup

# دالة لإنشاء زر الرفع
def create_upload_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("رفع ملف 📤", callback_data="upload_file")
    markup.add(button)
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
    # دالة لإضافة حساب جديد
def add_account(call):
    msg = bot.edit_message_text("يرجى إرسال مفتاح API الخاص بحساب Heroku:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_new_account)  # الخطأ هنا في السطر 90
    api_key = message.text.strip()
    user_id = message.from_user.id
    if api_key in [account['api_key'] for account in user_accounts[user_id]]:
        bot.send_message(message.chat.id, "هذا الحساب مضاف مسبقًا.", reply_markup=create_main_buttons())
    elif validate_heroku_api_key(api_key):
        user_accounts[user_id].append({'api_key': api_key})
        bot.send_message(message.chat.id, "تمت إضافة حساب Heroku بنجاح!", reply_markup=create_main_buttons())
    else:
        bot.send_message(message.chat.id, "مفتاح API غير صحيح. يرجى المحاولة مرة أخرى.", reply_markup=create_main_buttons())

# دالة للتحقق من صحة مفتاح API لهيروكو
def validate_heroku_api_key(api_key):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    return response.status_code == 200

# دالة لجلب اسم حساب هيروكو
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

# دالة لحذف التطبيق من هيروكو
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

# دالة لعرض الوقت المتبقي للحذف الذاتي
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

# دالة لعرض الوقت المتبقي
def format_remaining_time(minutes):
    delta = timedelta(minutes=minutes)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} ساعة و{minutes} دقيقة"

# دالة لحساب وقت الحذف
def calculate_deletion_time(minutes):
    iraq_timezone = pytz.timezone('Asia/Baghdad')
    now = datetime.now(iraq_timezone)
    deletion_time = now + timedelta(minutes=minutes)
    return deletion_time.strftime("%I:%M %p - %Y-%m-%d")

# دالة للتعامل مع الأوامر الداخلية للبوت
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data == "github_section":
        bot.send_message(call.message.chat.id, "اختر الإجراء الذي تريد تنفيذه:", reply_markup=create_github_buttons())
    elif call.data.startswith("list_heroku_apps_"):
        list_herokudef callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data == "github_section":
        bot.send_message(call.message.chat.id, "اختر الإجراء الذي تريد تنفيذه:", reply_markup=create_github_buttons())
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
    elif call.data == "delete_all_repos":
        delete_all_repos(call)
    elif call.data == "delete_repo":
        msg = bot.edit_message_text("يرجى إرسال اسم المستودع لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, handle_repo_deletion)
    elif call.data == "upload_file":
        msg = bot.edit_message_text("يرجى إرسال الملف المضغوط (ZIP) لرفعه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, handle_zip_file)

# دالة لإنشاء أزرار جيتهاب
def create_github_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("حذف المستودعات 🗑️", callback_data="delete_all_repos")
    button2 = telebot.types.InlineKeyboardButton("حذف مستودع 📁", callback_data="delete_repo")
    button3 = telebot.types.InlineKeyboardButton("رفع ملف 📤", callback_data="upload_file")
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="list_accounts"))
    return markup

# دالة لحذف كل المستودعات
def delete_all_repos(call):
    user_id = call.from_user.id
    if not user_id in user_accounts or not user_accounts[user_id]:
        bot.edit_message_text("لا توجد حسابات مضافة. يرجى إضافة حساب أولاً.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        return
    for account in user_accounts[user_id]:
        github_headers = {'Authorization': f'token {github_token}'}
        response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=github_headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                response = requests.delete(f'{GITHUB_BASE_URL}/repos/{repo["full_name"]}', headers=github_headers)
                if response.status_code == 204:
                    bot.send_message(call.message.chat.id, f"تم حذف المستودع {repo['full_name']} بنجاح.")
                else:
                    bot.send_message(call.message.chat.id, f"حدث خطأ أثناء محاولة حذف المستودع {repo['full_name']}.")
        else:
            bot.edit_message_text("حدث خطأ في جلب المستودعات من جيتهاب.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لحذف مستودع محدد
def handle_repo_deletion(message):
    repo_name = message.text.strip()
    user_id = message.from_user.id
    if user_id in user_accounts and user_accounts[user_id]:
        github_headers = {'Authorization': f'token {github_token}'}
        response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=github_headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                if repo["full_name"] == repo_name:
                    response = requests.delete(f'{GITHUB_BASE_URL}/repos/{repo["full_name"]}', headers=github_headers)
                    if response.status_code == 204:
                        bot.send_message(message.chat.id, f"تم حذف المستودع {repo_name} بنجاح.")
                        return
            bot.send_message(message.chat.id, f"المستودع {repo_name} غير موجود.")
        else:
            bot.send_message(message.chat.id, "حدث خطأ في جلب المستودعات من جيتهاب.")
    else:
        bot.sendelse:
        bot.send_message(message.chat.id, "لا توجد حسابات مضافة. يرجى إضافة حساب أولاً.", reply_markup=create_back_button())

# دالة لرفع ملف مضغوط إلى جيتهاب
def handle_zip_file(message):
    user_id = message.from_user.id
    if user_id in user_accounts and user_accounts[user_id]:
        # تأكد من وجود الملف المرسل
        if message.content_type != 'document':
            bot.send_message(message.chat.id, "الرجاء إرسال ملف مضغوط (ZIP).", reply_markup=create_back_button())
            return

        # حمل الملف وفك الضغط
        file_info = bot.get_file(message.document.file_id)
        file = requests.get(f'https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}')
        with open('file.zip', 'wb') as f:
            f.write(file.content)
        import zipfile
        with zipfile.ZipFile('file.zip', 'r') as zip_ref:
            zip_ref.extractall('extracted_files')

        # رفع الملفات المستخرجة إلى جيتهاب
        for account in user_accounts[user_id]:
            github_headers = {'Authorization': f'token {github_token}'}
            repo_name = f"repo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            response = requests.post(f'{GITHUB_BASE_URL}/user/repos', headers=github_headers, json={'name': repo_name})
            if response.status_code == 201:
                bot.send_message(message.chat.id, f"تم إنشاء المستودع {repo_name} بنجاح.")
                # قم بتحميل كل ملف من الملفات المستخرجة وأضفه إلى المستودع الجديد
                files = os.listdir('extracted_files')
                for file_name in files:
                    with open(f'extracted_files/{file_name}', 'rb') as file_content:
                        response = requests.post(f'{GITHUB_BASE_URL}/repos/{account["username"]}/{repo_name}/contents/{file_name}', headers=github_headers, json={'message': 'Add file', 'content': base64.b64encode(file_content.read()).decode()})
                        if response.status_code == 201:
                            bot.send_message(message.chat.id, f"تم رفع الملف {file_name} إلى المستودع {repo_name} بنجاح.")
                        else:
                            bot.send_message(message.chat.id, f"حدث خطأ أثناء محاولة رفع الملف {file_name} إلى المستودع {repo_name}.")
            else:
                bot.send_message(message.chat.id, f"حدث خطأ أثناء محاولة إنشاء المستودع {repo_name}.")
        # قم بحذف الملفات المؤقتة
        os.remove('file.zip')
        shutil.rmtree('extracted_files')
    else:
        bot.send_message(message.chat.id, "لا توجد حسابات مضافة. يرجى إضافة حساب أولاً.", reply_markup=create_back_button())

# التشغيل
if __name__ == "__main__":
    bot.polling()
