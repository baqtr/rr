import os
import telebot
import requests

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
heroku_api_key = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"  # مفتاح API الخاص بـ Heroku

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)

# الهيروكو API
HEROKU_BASE_URL = 'https://api.heroku.com'
HEROKU_HEADERS = {
    'Authorization': f'Bearer {heroku_api_key}',
    'Accept': 'application/vnd.heroku+json; version=3'
}

# دالة لإنشاء الأزرار وتخصيصها
def create_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("اضغط هنا", callback_data="show_id1")
    button2 = telebot.types.InlineKeyboardButton("جلب تطبيقات هيروكو", callback_data="list_heroku_apps")
    button3 = telebot.types.InlineKeyboardButton("وضع الصيانة", callback_data="maintenance_mode")
    button4 = telebot.types.InlineKeyboardButton("حذف تطبيق", callback_data="delete_app")
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(button4)
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
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=HEROKU_HEADERS)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.edit_message_text(f"التطبيقات المتاحة في هيروكو:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("حدث خطأ في جلب التطبيقات من هيروكو.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "show_id1":
        user_id = call.message.chat.id
        bot.edit_message_text(f"معرف المستخدم هو: `{user_id}`", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    elif call.data == "list_heroku_apps":
        list_heroku_apps(call)
    elif call.data == "maintenance_mode":
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لوضعه في وضع الصيانة:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, handle_app_name_for_maintenance)
    elif call.data == "delete_app":
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, handle_app_name_for_deletion)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_button())

# دالة لمعالجة اسم التطبيق المستلم لوضع الصيانة
def handle_app_name_for_maintenance(message):
    app_name = message.text.strip()
    if validate_heroku_app(app_name):
        set_maintenance_mode(app_name, message)
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة لمعالجة اسم التطبيق المستلم للحذف
def handle_app_name_for_deletion(message):
    app_name = message.text.strip()
    if validate_heroku_app(app_name):
        delete_heroku_app(app_name, message)
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة للتحقق من صحة اسم التطبيق
def validate_heroku_app(app_name):
    response = requests.get(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    return response.status_code == 200

# دالة لوضع التطبيق في وضع الصيانة
def set_maintenance_mode(app_name, message):
    response = requests.patch(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS, json={'maintenance': True})
    if response.status_code == 200:
        bot.send_message(message.chat.id, f"تم وضع التطبيق `{app_name}` في وضع الصيانة.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء وضع التطبيق في وضع الصيانة.")

# دالة لحذف التطبيق
def delete_heroku_app(app_name, message):
    response = requests.delete(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=HEROKU_HEADERS)
    if response.status_code == 202:
        bot.send_message(message.chat.id, f"تم حذف التطبيق `{app_name}` بنجاح.", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "حدث خطأ أثناء محاولة حذف التطبيق.")

# التشغيل
if __name__ == "__main__":
    bot.polling()
