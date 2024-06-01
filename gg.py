import os
import telebot
import requests
import threading
import time

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6qGm6qZA2JRJGOUQ20"
heroku_api_key = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"  # مفتاح API الخاص بـ Heroku

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'
HEROKU_HEADERS = {
    'Authorization': f'Bearer {heroku_api_key}',
    'Accept': 'application/vnd.heroku+json; version=3'
}

# قائمة التطبيقات المجدولة للحذف الذاتي
self_deleting_apps = {}

# دالة لإنشاء الأزرار وتخصيصها
def create_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("اضغط هنا", callback_data="show_id1")
    button2 = telebot.types.InlineKeyboardButton("جلب تطبيقات هيروكو", callback_data="list_heroku_apps")
    button3 = telebot.types.InlineKeyboardButton("حذف تطبيق", callback_data="delete_app")
    button4 = telebot.types.InlineKeyboardButton("الحذف الذاتي", callback_data="self_delete_app")
    button5 = telebot.types.InlineKeyboardButton("الوقت المتبقي للحذف الذاتي", callback_data="remaining_time")
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(button4)
    markup.add(button5)
    return markup

# دالة لإنشاء زر العودة
def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton("العودة", callback_data="go_back")
    markup.add(back_button)
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_button())

# دالة لجلب تطبيقات هيروكو
def list_heroku_apps(call):
    bot.edit_message_text("جلب التطبيقات... ⬛⬜ 0%", chat_id=call.message.chat.id, message_id=call.message.message_id)
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.edit_message_text("جلب التطبيقات... ⬛⬛ 50%", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.edit_message_text(f"التطبيقات المتاحة في هيروكو:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("حدث خطأ في جلب التطبيقات من هيروكو.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "show_id1":
        user_id = call.message.chat.id
        bot.edit_message_text("جلب معرف المستخدم... ⬛⬜ 0%", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.edit_message_text("جلب معرف المستخدم... ⬛⬛ 50%", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.edit_message_text(f"معرف المستخدم هو: `{user_id}`", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
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
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_button())

# دالة لمعالجة اسم التطبيق المستلم للحذف
def handle_app_name_for_deletion(message):
    app_name = message.text.strip()
    if validate_heroku_app(app_name):
        delete_heroku_app(app_name, message)
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة لمعالجة اسم التطبيق المستلم للحذف الذاتي
def handle_app_name_for_self_deletion(message):
    app_name = message.text.strip()
    if validate_heroku_app(app_name):
        msg = bot.send_message(message.chat.id, f"تم تأكيد اسم التطبيق `{app_name}`. يرجى إرسال الوقت (بالدقائق) حتى يتم الحذف الذاتي:")
        bot.register_next_step_handler(msg, lambda m: schedule_self_deletion(app_name, m))
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة للتحقق من صحة اسم التطبيق
def validate_heroku_app(app_name):
    response = requests.get(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    return response.status_code == 200

# دالة لحذف التطبيق
def delete_heroku_app(app_name, message):
    bot.send_message(message.chat.id, "حذف التطبيق... ⬛⬜ 0%")
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 202:
        bot.send_message(message.chat.id, "حذف التطبيق... ⬛⬛ 50%")
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء محاولة حذف التطبيق.")

# دالة لجدولة الحذف الذاتي
def schedule_self_deletion(app_name, message):
    try:
        minutes = int(message.text.strip())
        if minutes > 0:
            delete_time = time.time() + minutes * 60
            self_deleting_apps[app_name] = delete_time
            bot.send_message(message.chat.id, f"تم جدولة حذف التطبيق `{app_name}` بعد {minutes} دقيقة.")
            threading.Thread(target=wait_and_delete_app, args=(app_name, message.chat.id, delete_time)).start()
        else:
            bot.send_message(message.chat.id, "يرجى إرسال وقت صحيح (عدد الدقائق يجب أن يكون أكبر من 0).")
    except ValueError:
        bot.send_message(message.chat.id, "يرجى إرسال وقت صحيح (عدد الدقائق).")

# دالة للانتظار وحذف التطبيق بعد انتهاء الوقت المحدد
def wait_and_delete_app(app_name, chat_id, delete_time):
    while time.time() < delete_time:
        time.sleep(10)
    delete_heroku_app(app_name, None)
    bot.send_message(chat_id, f"تم حذف التطبيق `{app_name}` بعد انتهاء الوقت المحدد.")

# دالة لعرض الوقت المتبقي للحذف الذاتي
def show_remaining_time(call):
    messages = []
    current_time = time.time()
    for app_name, delete_time in self_deleting_apps.items():
        remaining_time = int((delete_time - current_time) / 60)
        if remaining_time > 0:
            messages.append(f"التطبيق `{app_name}` سيتم حذفه بعد {remaining_time} دقيقة.")
        else:
            messages.append(f"التطبيق `{app_name}` سيتم حذفه قريبا.")
    if messages:
        bot.edit_message_text("\n".join(messages), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("لا توجد تطبيقات مجدولة للحذف الذاتي.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# التشغيل
if __name__ == "__main__":
    bot.polling()
