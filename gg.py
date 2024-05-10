import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"

def welcome(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "مرحباً بك! أنا بوت Heroku Manager. إذا كنت مستعدًا لحذف جميع التطبيقات المرتبطة بحساب Heroku الخاص بك، يرجى إرسال لي مفتاح API الخاص بك. 😊"
    )

def delete_all_apps(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        apps = response.json()
        for app in apps:
            app_id = app['id']
            delete_response = requests.delete(f"https://api.heroku.com/apps/{app_id}", headers=headers)
            if delete_response.status_code != 200:
                return f"Error deleting app: {app_id}"
        return f"تم حذف جميع التطبيقات بنجاح. عدد التطبيقات التي تم حذفها: {len(apps)} ✅"
    else:
        return "Error fetching apps"

def create_apps(api_key, num_apps):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    app_names = []
    for _ in range(num_apps):
        app_name = f"app-{os.urandom(6).hex()}"
        create_response = requests.post("https://api.heroku.com/apps", headers=headers, json={"name": app_name})
        if create_response.status_code == 201:
            app_names.append(app_name)
    if app_names:
        return f"تم إنشاء {num_apps} تطبيق بنجاح: {', '.join(app_names)} ✅"
    else:
        return "فشل في إنشاء التطبيقات."

def list_all_apps(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        apps = response.json()
        app_names = [app['name'] for app in apps]
        return f"التطبيقات الموجودة: {', '.join(app_names)}"
    else:
        return "فشل في جلب قائمة التطبيقات."

def message_handler(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    api_key = message_text.strip()

    if api_key.startswith("HRKU-"):  # التحقق من صحة مفتاح API
        buttons = [
            [InlineKeyboardButton("حذف جميع التطبيقات", callback_data="delete_all")],
            [InlineKeyboardButton("إنشاء 50 تطبيق", callback_data="create_apps_50")],
            [InlineKeyboardButton("عرض جميع التطبيقات", callback_data="list_apps")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text("تم استلام مفتاح API بنجاح. اختر الإجراء الذي ترغب في تنفيذه:", reply_markup=keyboard)
    else:
        update.message.reply_text("مفتاح API غير صالح. الرجاء المحاولة مرة أخرى. ❌")

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    api_key = query.message.text.split('\n')[0]  # استخراج مفتاح API من الرسالة
    action = query.data

    if action == "delete_all":
        result = delete_all_apps(api_key)
        query.edit_message_text(text=result)
    elif action == "create_apps_50":
        result = create_apps(api_key, 50)
        query.edit_message_text(text=result)
    elif action == "list_apps":
        result = list_all_apps(api_key)
        query.edit_message_text(text=result)

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", welcome))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
