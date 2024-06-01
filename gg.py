import os
import telebot
import requests
import threading
import time
from datetime import datetime, timedelta
import pytz  # استيراد مكتبة pytz

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# قاعدة بيانات مؤقتة لتخزين حسابات المستخدمين
user_accounts = {}

# قائمة التطبيقات المجدولة للحذف الذاتي
self_deleting_apps = {}

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("إضافة حساب 🆕", callback_data="add_account")
    button2 = telebot.types.InlineKeyboardButton("حساباتك 🔐", callback_data="list_accounts")
    markup.add(button1, button2)
    return markup

def create_action_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("جلب تطبيقات هيروكو 📦", callback_data="list_heroku_apps")
    button2 = telebot.types.InlineKeyboardButton("حذف تطبيق ❌", callback_data="delete_app")
    button3 = telebot.types.InlineKeyboardButton("الحذف الذاتي ⏲️", callback_data="self_delete_app")
    button4 = telebot.types.InlineKeyboardButton("الوقت المتبقي ⏳", callback_data="remaining_time")
    markup.add(button1, button2)
    markup.add(button3, button4)
    return markup

# دالة لإنشاء زر العودة
def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back")
    markup.add(back_button)
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_main_buttons())

# دالة لإضافة حساب جديد
def add_account(call):
    msg = bot.edit_message_text("يرجى إرسال مفتاح API الخاص بحسابك في هيروكو:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
    bot.register_next_step_handler(msg, handle_new_account)

def handle_new_account(message):
    api_key = message.text.strip()
    response = requests.get('https://api.heroku.com/account', headers={'Authorization': f'Bearer {api_key}', 'Accept': 'application/vnd.heroku+json; version=3'})
    if response.status_code == 200:
        account_info = response.json()
        user_id = message.from_user.id
        if user_id not in user_accounts:
            user_accounts[user_id] = []
        user_accounts[user_id].append({'api_key': api_key, 'email': account_info['email']})
        bot.send_message(message.chat.id, f"تمت إضافة الحساب بنجاح: {account_info['email']}", reply_markup=create_main_buttons())
    else:
        bot.send_message(message.chat.id, "مفتاح API غير صحيح، يرجى المحاولة مرة أخرى.", reply_markup=create_back_button())

# دالة لعرض حسابات المستخدم
def list_accounts(call):
    user_id = call.from_user.id
    if user_id in user_accounts and user_accounts[user_id]:
        accounts_list = "\n".join([f"{i+1}. {account['email']}" for i, account in enumerate(user_accounts[user_id])])
        bot.edit_message_text(f"حساباتك:\n{accounts_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_buttons(user_id))
    else:
        bot.edit_message_text("لا توجد حسابات مضافة.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

def create_account_buttons(user_id):
    markup = telebot.types.InlineKeyboardMarkup()
    for i, account in enumerate(user_accounts[user_id]):
        button = telebot.types.InlineKeyboardButton(account['email'], callback_data=f"select_account_{i}")
        markup.add(button)
    back_button = telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back")
    markup.add(back_button)
    return markup

def select_account(call):
    user_id = call.from_user.id
    account_index = int(call.data.split('_')[-1])
    account = user_accounts[user_id][account_index]
    HEROKU_HEADERS['Authorization'] = f'Bearer {account["api_key"]}'
    bot.edit_message_text(f"تم اختيار الحساب: {account['email']}\nاختر الإجراء المطلوب:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_action_buttons())

# دالة لجلب تطبيقات هيروكو
def list_heroku_apps(call):
    bot.edit_message_text("جلب التطبيقات... ⬛⬜ 0%", chat_id=call.message.chat.id, message_id=call.message.message_id)
    time.sleep(2)
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
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
    elif call.data.startswith("select_account_"):
        select_account(call)
    elif call.data == "list_heroku_apps":
        list_heroku_apps(call)
    elif call.data == "delete_app":
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, handle_app_name_for_deletion)
    elif call.data == "self_delete_app":
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق للحذف الذاتي:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, handle_app_name_for_self_deletion)
    elif call.data == "remaining_time":
        show_remaining_time(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# الحذف
def handle_app_name_for_deletion(message):
    app_name = message.text.strip()
    if validate_heroku_app(app_name):
        delete_heroku_app(app_name, message)
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# تحقق من صحة اسم التطبيق
def validate_heroku_app(app_name):
    response = requests.get(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    return response.status_code == 200

# الحذف الذاتي
def handle_app_name_for_self_deletion(message):
    app_name = message.text.strip()
    if validate_heroku_app(app_name):
        if app_name in self_deleting_apps:
            bot.send_message(message.chat.id, f"تم وضع التطبيق `{app_name}` مسبقًا في قائمة الحذف الذاتي.", parse_mode='Markdown')
        else:
            msg = bot.send_message(message.chat.id, "يرجى إدخال الوقت المطلوب بالدقائق لحذف التطبيق:")
            bot.register_next_step_handler(msg, lambda m: handle_self_deletion_time(m, app_name))
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# الحذف الذاتي
def handle_self_deletion_time(message, app_name):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
        self_deleting_apps[app_name] = minutes
        bot.send_message(message.chat.id, f"سيتم حذف التطبيق `{app_name}` بعد {minutes} دقيقة.\n", reply_markup=create_remaining_time_button())
        # بدء عملية الحذف الذاتي
        threading.Timer(minutes * 60, lambda: delete_and_remove_app(app_name, message)).start()
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إدخال عدد صحيح إيجابي للدقائق.")

# زر عرض الوقت المتبقي
def create_remaining_time_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("الوقت المتبقي ⏳", callback_data="remaining_time")
    markup.add(button)
    return markup

# حذف التطبيق وإزالته من القائمة
def delete_and_remove_app(app_name, message):
    delete_heroku_app(app_name, message)
    if app_name in self_deleting_apps:
        del self_deleting_apps[app_name]

# حذف التطبيق
def delete_heroku_app(app_name, message):
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء محاولة حذف التطبيق.")

# عرض الوقت المتبقي للحذف الذاتي
def show_remaining_time(call):
    remaining_time_message = "التطبيقات المجدولة للحذف الذاتي:\n"
    for app_name, minutes in list(self_deleting_apps.items()):
        if app_name in self_deleting_apps:
            remaining_time_message += f"- {app_name}:\n  الوقت المتبقي: {format_remaining_time(minutes)}\n  تاريخ الحذف: {calculate_deletion_time(minutes)}\n"
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

# التشغيل
if __name__ == "__main__":
    bot.polling() 
