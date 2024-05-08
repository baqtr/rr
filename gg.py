import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from heroku3 import from_key

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"
HEROKU_API_KEYS = [
    "HRKU-5e86e90f-8222-40b2-9b54-302d63a73e32",
    "HRKU-a362bdb3-a2a3-4e48-86e5-3d3f56799621",
    "HRKU-354b0fc4-1af5-4c26-91a5-9c09166d5eee"
]
MAX_APPS_DISPLAYED = 3

def start(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for i, account_key in enumerate(HEROKU_API_KEYS):
        keyboard.append([InlineKeyboardButton(f"حساب {i + 1}", callback_data=f"account_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("يرجى اختيار أحد الحسابات:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    account_index = int(query.data.split('_')[1])

    heroku = from_key(HEROKU_API_KEYS[account_index])
    apps = heroku.apps()

    update.message.reply_text(f"عدد التطبيقات المرتبطة بحساب Heroku الحساب {account_index + 1}: {len(apps)}")

    keyboard = []
    for i, app in enumerate(apps[:MAX_APPS_DISPLAYED]):
        button = InlineKeyboardButton(app.name, callback_data=f"app_{i}_{account_index}")
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text("يرجى اختيار أحد التطبيقات:", reply_markup=reply_markup)

def app_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    app_index, account_index = map(int, query.data.split('_')[1:3])

    heroku = from_key(HEROKU_API_KEYS[account_index])
    apps = heroku.apps()

    app = apps[app_index]
    app_info = f"اسم التطبيق: {app.name}\n"
    app_info += f"رابط التطبيق: {app.web_url}"

    query.edit_message_text(text=app_info)

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button, pattern='^account_'))
    dp.add_handler(CallbackQueryHandler(app_button, pattern='^app_'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
