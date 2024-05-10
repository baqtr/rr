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

def create_apps(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("جارٍ إنشاء 50 تطبيق...")

    # قم بإضافة رمز لإنشاء 50 تطبيقًا هنا

def show_all_apps(update: Update, context: CallbackContext) -> None:
    api_key = context.user_data['api_key']
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        apps = response.json()
        app_list = "\n".join([f"{app['name']}: {app['web_url']}" for app in apps])
        update.message.reply_text(f"جميع التطبيقات الموجودة:\n{app_list}")
    else:
        update.message.reply_text("Error fetching apps")

def message_handler(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    api_key = message_text.strip()

    if api_key.startswith("HRKU-"):  # التحقق من صحة مفتاح API
        context.user_data['api_key'] = api_key
        keyboard = [
            [InlineKeyboardButton("حذف جميع التطبيقات", callback_data='delete_all')],
            [InlineKeyboardButton("إنشاء 50 تطبيق", callback_data='create_apps')],
            [InlineKeyboardButton("إظهار جميع التطبيقات", callback_data='show_all')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('يرجى اختيار الإجراء المطلوب:', reply_markup=reply_markup)
    else:
        update.message.reply_text("مفتاح API غير صالح. الرجاء المحاولة مرة أخرى. ❌")

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'delete_all':
        api_key = context.user_data['api_key']
        result = delete_all_apps(api_key)
        query.edit_message_text(result)
    elif query.data == 'create_apps':
        create_apps(update, context)
    elif query.data == 'show_all':
        show_all_apps(update, context)

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
