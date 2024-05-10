import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# تفعيل تسجيل الأحداث
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# تعريف التوكن الخاص بالبوت
TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"

# دالة رحب
def welcome(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "مرحباً بك! أنا بوت Heroku Manager. إذا كنت مستعدًا لحذف جميع التطبيقات المرتبطة بحساب Heroku الخاص بك، يرجى إرسال لي مفتاح API الخاص بك."
    )

# دالة لحذف جميع التطبيقات
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
        return f"تم حذف جميع التطبيقات بنجاح. عدد التطبيقات التي تم حذفها: {len(apps)}"
    else:
        return "Error fetching apps"

# دالة استجابة للرسائل
def message_handler(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    api_key = message_text.strip()

    if api_key.startswith("HRKU-"):  # التحقق من صحة مفتاح API
        result = delete_all_apps(api_key)
        update.message.reply_text(result)
    else:
        update.message.reply_text("مفتاح API غير صالح. الرجاء المحاولة مرة أخرى.")

# دالة رئيسية
def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # إضافة معالج لرسائل البداية
    dp.add_handler(CommandHandler("start", welcome))

    # إضافة معالج لرسائل النص
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if name == 'main':
    main()
