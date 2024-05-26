import logging
import phonenumbers
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneNumberBannedError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = 'YOUR_TELEGRAM_API_ID'
API_HASH = 'YOUR_TELEGRAM_API_HASH'
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
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        
        try:
            client.connect()
            if not client.is_user_authorized():
                client.send_code_request(phone_number)
                client.sign_in(phone_number, user_code)

            session_string = client.session.save()
            update.message.reply_text(f"✅ تم تسجيل الدخول بنجاح. الجلسة:\n\n`{session_string}`\n\nقم بنسخها واستخدامها في تطبيقك.", parse_mode='Markdown')
            client.disconnect()
        except PhoneNumberBannedError:
            update.message.reply_text("🚫 الرقم محظور. الرجاء استخدام رقم آخر.")
        except SessionPasswordNeededError:
            update.message.reply_text("🔒 يتطلب التحقق بخطوتين. الرجاء إدخال كلمة المرور:")
        except Exception as e:
            update.message.reply_text(f"❌ حدث خطأ أثناء تسجيل الدخول: {str(e)}")
    else:
        update.message.reply_text("❌ لم يتم استقبال رقم الهاتف. الرجاء إرسال رقم الهاتف أولاً.")

def handle_password(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    password = update.message.text

    if user_id in users_data and 'phone_number' in users_data[user_id] and 'verification_code' in users_data[user_id]:
        phone_number = users_data[user_id]['phone_number']
        verification_code = users_data[user_id]['verification_code']

        client = TelegramClient(StringSession(), API_ID, API_HASH)

        try:
            client.connect()
            if not client.is_user_authorized():
                client.send_code_request(phone_number)
                client.sign_in(phone_number, verification_code)
                client.sign_in(password=password)

            session_string = client.session.save()
            update.message.reply_text(f"✅ تم تسجيل الدخول بنجاح. الجلسة:\n\n`{session_string}`\n\nقم بنسخها واستخدامها في تطبيقك.", parse_mode='Markdown')
            client.disconnect()
        except Exception as e:
            update.message.reply_text(f"❌ حدث خطأ أثناء تسجيل الدخول: {str(e)}")
    else:
        update.message.reply_text("❌ لم يتم استقبال كافة البيانات المطلوبة. الرجاء إعادة العملية من البداية.")

def retry(update: Update, context: CallbackContext) -> None:
    start(update, context)

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_number))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_code))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_password))
    dp.add_handler(CommandHandler("retry", retry))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
