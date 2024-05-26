import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelمه)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE"

language = "en"

messages = {
    "en": {
        "start": "👋 Hello! I am a bot that converts PHP files to Python. Please send a PHP file to start.",
        "invalid_file": "❌ Please send a PHP file with .php extension.",
        "file_received": "📂 File received. Choose an option:",
        "convert_success": "✅ Conversion successful. Here is your Python file.",
        "choose_language": "Please choose a language:",
        "back_to_menu": "🔙 Back to Menu",
        "send_file": "📤 Send File",
        "change_language": "🌐 Change Language",
        "show_stats": "📊 Show File Statistics",
        "convert_file": "🔄 Convert File",
        "conversion_result": "🔄 Conversion Result",
    },
    "ar": {
        "start": "👋 مرحباً! أنا بوت لتحويل ملفات PHP إلى بايثون. الرجاء إرسال ملف PHP للبدء.",
        "invalid_file": "❌ الرجاء إرسال ملف PHP بامتداد .php",
        "file_received": "📂 تم استقبال الملف. اختر خيارًا:",
        "convert_success": "✅ تم التحويل بنجاح. إليك ملف بايثون.",
        "choose_language": "الرجاء اختيار اللغة:",
        "back_to_menu": "🔙 العودة إلى القائمة",
        "send_file": "📤 إرسال الملف",
        "change_language": "🌐 تغيير اللغة",
        "show_stats": "📊 عرض إحصائيات الملف",
        "convert_file": "🔄 تحويل الملف",
        "conversion_result": "🔄 نتيجة التحويل",
    }
}

def start(update: Update, context: CallbackContext) -> None:
    show_menu(update.message.reply_text, messages[language]["start"])

def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    if file.file_name.endswith('.php'):
        file_path = file.get_file().download()
        context.user_data['file_path'] = file_path
        context.user_data['file_name'] = file.file_name

        show_menu(update.message.reply_text, messages[language]["file_received"])
    else:
        update.message.reply_text(messages[language]["invalid_file"])

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    file_path = context.user_data.get('file_path')
    if not file_path and query.data not in ['change_language', 'back_to_menu']:
        query.edit_message_text(text=messages[language]["invalid_file"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')]]))
        return

    if query.data == 'convert_file':
        convert_file(query, file_path, context)
    elif query.data == 'send_file':
        send_file(query, context)
    elif query.data == 'change_language':
        change_language(query)
    elif query.data == 'show_stats':
        show_stats(query, file_path)
    elif query.data == 'conversion_result':
        show_conversion_result(query, context)
    elif query.data == 'back_to_menu':
        back_to_menu(query, context)

def convert_file(query, file_path, context):
    with open(file_path, 'r') as f:
        php_code = f.read()
    python_code = php_code.replace("<?php", "").replace("?>", "").replace(";", "\n")  # Simple example conversion

    python_file_path = file_path.replace('.php', '.py')
    with open(python_file_path, 'w') as f:
        f.write(python_code)

    context.user_data['converted_file_path'] = python_file_path
    context.user_data['modifications'] = ["تحويل الملف من PHP إلى بايثون"]
    query.edit_message_text(text=messages[language]["convert_success"], reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')],
        [InlineKeyboardButton(messages[language]["send_file"], callback_data='send_file')],
        [InlineKeyboardButton(messages[language]["conversion_result"], callback_data='conversion_result')]
    ]))

def send_file(query, context):
    converted_file_path = context.user_data.get('converted_file_path')
    if converted_file_path:
        with open(converted_file_path, 'rb') as f:
            context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(f, filename=os.path.basename(converted_file_path)))

        query.edit_message_text(text=messages[language]["send_file"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')]]))
    else:
        query.edit_message_text(text="⚠️ لم يتم تحويل الملف بعد. الرجاء تحويل الملف أولاً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')]]))

def change_language(query):
    global language
    language = "ar" if language == "en" else "en"
    show_menu(query.edit_message_text, messages[language]["choose_language"])

def show_stats(query, file_path):
    line_count = sum(1 for line in open(file_path))
    query.edit_message_text(text=f"📊 عدد سطور الملف: {line_count}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')]]))

def show_conversion_result(query, context):
    modifications = context.user_data.get('modifications', [])
    file_path = context.user_data['file_path']
    converted_file_path = context.user_data.get('converted_file_path')

    original_line_count = sum(1 for line in open(file_path))
    converted_line_count = sum(1 for line in open(converted_file_path)) if converted_file_path else 0

    result_text = f"عدد التعديلات: {len(modifications)}\nعدد سطور الملف الأصلي: {original_line_count}\nعدد سطور الملف المحول: {converted_line_count}\nنسبة نجاح العملية: ✅"
    query.edit_message_text(text=result_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')]]))

def back_to_menu(query, context):
    show_menu(query.edit_message_text, messages[language]["start"])

def show_menu(reply_func, message):
    keyboard = [
        [InlineKeyboardButton(messages[language]["convert_file"], callback_data='convert_file')],
        [InlineKeyboardButton(messages[language]["send_file"], callback_data='send_file')],
        [InlineKeyboardButton(messages[language]["show_stats"], callback_data='show_stats')],
        [InlineKeyboardButton(messages[language]["change_language"], callback_data='change_language')],
        [InlineKeyboardButton(messages[language]["back_to_menu"], callback_data='back_to_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_func(message, reply_markup=reply_markup)

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
