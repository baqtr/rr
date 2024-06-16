from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

# احصل على رمز التوكن من متغير البيئة
BOT_TOKEN = '6444148337:AAFANHnwUPQXnq_SLHnqhsuH9WnSxALtUvo'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحبًا! كيف يمكنني مساعدتك؟')

def main():
    updater = Updater(BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
