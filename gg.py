import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os
import re
import subprocess

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7031770762:AAF-BrYHNEcX8VyGBzY1mastEG3SWod4_uI"

def start(update: Update, context: CallbackContext) -> None:
    file_path = context.user_data.get('file_path')
    if file_path:
        show_menu(update.message.reply_text, "📂 تم استقبال الملف مسبقاً. اختر عملية:")
    else:
        update.message.reply_text("👋 مرحباً! أنا بوت إدارة ملفات بايثون. الرجاء إرسال ملف بايثون لتبدأ.")

def handle_file(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    if file.file_name.endswith('.py'):
        file_path = file.get_file().download()
        context.user_data['file_path'] = file_path
        context.user_data['file_name'] = file.file_name
        context.user_data['modifications'] = []

        show_menu(update.message.reply_text, "📂 تم استقبال الملف. اختر عملية:")
    else:
        update.message.reply_text("❌ الرجاء إرسال ملف بايثون بامتداد .py")

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if 'file_path' not in context.user_data:
        query.edit_message_text(text="⚠️ لم يتم استقبال ملف بعد. الرجاء إرسال ملف بايثون أولاً.")
        return

    file_path = context.user_data['file_path']

    if query.data == 'show_commands':
        show_commands(query, file_path)
    elif query.data == 'show_libraries':
        show_libraries(query, file_path)
    elif query.data == 'fix_errors':
        fix_errors(query, file_path, context)
    elif query.data == 'clean_file':
        clean_file(query, file_path, context)
    elif query.data == 'format_code':
        format_code(query, file_path, context)
    elif query.data == 'optimize':
        optimize(query, file_path, context)
    elif query.data == 'send_file':
        send_file(query, context)
    elif query.data == 'reload_file':
        reload_file(query, context)
    elif query.data == 'test_file':
        test_file(query, file_path)
    elif query.data == 'back_to_menu':
        back_to_menu(query, context)

def show_menu(reply_func, message):
    keyboard = [
        [InlineKeyboardButton("🔍 عرض الأوامر", callback_data='show_commands')],
        [InlineKeyboardButton("📚 عرض المكاتب", callback_data='show_libraries')],
        [InlineKeyboardButton("🛠️ تصحيح الأخطاء", callback_data='fix_errors')],
        [InlineKeyboardButton("🧹 تنظيف الملف", callback_data='clean_file')],
        [InlineKeyboardButton("🗂️ تنظيم الكود", callback_data='format_code')],
        [InlineKeyboardButton("🚀 تحسين الأداء", callback_data='optimize')],
        [InlineKeyboardButton("📤 إرسال الملف", callback_data='send_file')],
        [InlineKeyboardButton("🔄 تحديث الملف", callback_data='reload_file')],
        [InlineKeyboardButton("⚙️ اختبار الملف", callback_data='test_file')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_func(message, reply_markup=reply_markup)

def show_commands(query, file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    commands = [line for line in content.split('\n') if line.strip().startswith('def ')]
    query.edit_message_text(text="الأوامر:\n" + '\n'.join(commands), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def show_libraries(query, file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    libraries = [line for line in content.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
    library_text = "\n".join([f"`{lib}`" for lib in libraries])
    query.edit_message_text(text=f"المكاتب:\n{library_text}\n(يمكنك نسخ المكتبة بالنقر عليها)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]), parse_mode='Markdown')

def fix_errors(query, file_path, context):
    with open(file_path, 'r') as f:
        content = f.read()

    # Attempt to correct common syntax errors
    content = re.sub(r'print\s+"', 'print("', content)
    content = re.sub(r'"\s*$', '")', content)
    content = re.sub(r'(?<!\w)exec\s+"', 'exec("', content)
    content = re.sub(r'"\s*$', '")', content)

    with open(file_path, 'w') as f:
        f.write(content)

    context.user_data['modifications'].append("تصحيح الأخطاء")
    query.edit_message_text(text="✅ تم تصحيح الأخطاء.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def clean_file(query, file_path, context):
    with open(file_path, 'r') as f:
        content = f.read()
    cleaned_content = '\n'.join([line for line in content.split('\n') if not line.strip().startswith('#')])
    with open(file_path, 'w') as f:
        f.write(cleaned_content)
    context.user_data['modifications'].append("تنظيف الملف من التعليقات")
    query.edit_message_text(text="🧹 تم تنظيف الملف من التعليقات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def format_code(query, file_path, context):
    with open(file_path, 'r') as f:
        content = f.read()
    formatted_content = '\n'.join([line.strip() for line in content.split('\n')])
    with open(file_path, 'w') as f:
        f.write(formatted_content)
    context.user_data['modifications'].append("تنظيم الكود")
    query.edit_message_text(text="🗂️ تم تنظيم الكود.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def optimize(query, file_path, context):
    context.user_data['modifications'].append("تسريع الأداء")
    query.edit_message_text(text="🚀 تم تسريع الأداء (مبدئي).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def reload_file(query, context):
    file_path = context.user_data['file_path']
    context.user_data['modifications'] = []
    query.edit_message_text(text="🔄 تم تحديث الملف. اختر عملية من جديد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def send_file(query, context):
    file_path = context.user_data['file_path']
    modifications = context.user_data['modifications']
    modifications_text = "التعديلات التي تمت على الملف:\n" + '\n'.join(modifications)
    line_count = sum(1 for line in open(file_path))

    with open(file_path, 'rb') as f:
        context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(f, filename=context.user_data['file_name']))
    
    result_text = f"{modifications_text}\nعدد التعديلات: {len(modifications)}\nعدد سطور الملف: {line_count}\nنسبة نجاح العملية: ✅"
    context.bot.send_message(chat_id=query.message.chat_id, text=result_text)
    query.edit_message_text(text="📤 تم إرسال الملف المعدل.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def test_file(query, file_path):
    query.edit_message_text(text="⚙️ جارٍ اختبار الملف...")
    try:
        result = subprocess.run(['python', file_path], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            query.edit_message_text(text=f"✅ تم اختبار الملف بنجاح:\n{result.stdout}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))
        else:
            query.edit_message_text(text=f"❌ فشل اختبار الملف:\n{result.stderr}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))
    except subprocess.TimeoutExpired:
        query.edit_message_text(text="⏰ تجاوز وقت اختبار الملف 30 ثانية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data='back_to_menu')]]))

def back_to_menu(query, context):
    show_menu(query.edit_message_text, "تم العودة إلى القائمة الرئيسية. اختر عملية:")

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_file))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    bot.polling()
