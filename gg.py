import logging
import phonenumbers
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pyrogram import Client, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = '28803961'
API_HASH = '4040917ceee8cf48c0ea217fcdc84250'
TOKEN = '6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE'

users_data = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 مرحباً! الرجاء إدخال رقم التليجرام الخاص بك مع رمز الدولة (مثال: +201234567890):")

def handle_number(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_number = update.message.text

    try:
        phone_number = phonenumbers.parse(user_number)
        if phonenumbers.is_valid_number(phone_number):
            users_data[user_id] = {'phone_number': user_number}
            update.message.reply_text("✅ تم استقبال الرقم. الرجاء إدخال رمز التحقق الذي تلقيته:")

            # Request verification code directly after receiving the number
            handle_code(update, context)
        else:
            update.message.reply_text("❌ الرقم غير صحيح. الرجاء إدخال رقم صحيح:")
    except phonenumbers.phonenumberutil.NumberParseException:
        update.message.reply_text("❌ الرقم غير صحيح. الرجاء إدخال رقم صحيح:")

def handle_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_code = update.message.text

    if user_id in users_data:
        users_data[user_id]['verification_code'] = user_code
        update.message.reply_text("🔄 جاري التحقق من الرمز...")

        phone_number = users_data[user_id]['phone_number']
        with Client("my_account", api_id=API_ID, api_hash=API_HASH) as app:
            try:
                app.start(phone=phone_number, code=user_code)

                session_string = app.export_session_string()
                update.message.reply_text(f"✅ تم تسجيل الدخول بنجاح. الجلسة:\n\n`{session_string}`\n\nقم بنسخها واستخدامها في تطبيقك.", parse_mode='Markdown')
            except Exception as e:
                update.message.reply_text(f"❌ حدث خطأ أثناء تسجيل الدخول: {str(e)}")
    else:
        update.message.reply_text("❌ لم يتم استقبال رقم الهاتف. الرجاء إرسال رقم الهاتف أولاً.")

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_number))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_code))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
