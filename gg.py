import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import subprocess
import os
import threading
import time
import ast
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "7031770762:AAF-BrYHNEcX8VyGBzY1mastEG3SWod4_uI"

user_files = {}
lock = threading.Lock()
MAX_FILES_PER_USER = 5

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id in user_files:
        for file_info in user_files[user_id]['files']:
            file_path = file_info['path']
            os.remove(file_path)
        del user_files[user_id]

    welcome_message = "🛠️ مرحبًا بك في أفضل بوت استضافة بايثون! يمكنك إرسال ملفات بايثون ليتم تشغيلها والتحقق منها. إذا كان هناك أي خطأ، سأقوم بإعلامك بالتفاصيل. 📂"
    
    keyboard = [
        [InlineKeyboardButton("📁 عرض الملفات", callback_data='show_files')],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data='help')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def handle_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_files.setdefault(user_id, {'files': [], 'expiry_time': 0, 'last_result': ''})

    if len(user_files[user_id]['files']) >= MAX_FILES_PER_USER:
        update.message.reply_text("⚠️ لقد تجاوزت الحد الأقصى لعدد الملفات المسموح بها. الرجاء المحاولة مرة أخرى لاحقًا.")
        return

    user_file = update.message.document
    file_name = user_file.file_name

    if not file_name.endswith('.py'):
        update.message.reply_text("⚠️ الرجاء إرسال ملف بايثون فقط.")
        return

    file_id = user_file.file_id
    file_path = f"{user_id}_{file_name}"
    user_file.get_file().download(file_path)

    user_files[user_id]['files'].append({'path': file_path, 'start_time': 0, 'expiry_time': time.time() + float('inf'), 'last_result': ''})

    update.message.reply_text("📥 تم تشغيل الملف بنجاح! سأخبرك بحال وجود أخطاء ✅")

    thread = threading.Thread(target=run_python_file, args=(update, user_id, len(user_files[user_id]['files']) - 1))
    thread.start()

def run_python_file(update: Update, user_id: int, file_index: int) -> None:
    try:
        lock.acquire()
        file_info = user_files[user_id]['files'][file_index]
        file_path = file_info['path']
        user_files[user_id]['files'][file_index]['start_time'] = time.time()

        with open(file_path, 'r') as f:
            code = f.read()

        try:
            # Check syntax errors
            ast.parse(code)
        except SyntaxError as e:
            message = f"❌ تعذر تشغيل الملف ({file_index + 1}) بسبب خطأ نحوي:\n\n{e}"
        else:
            # No syntax errors, proceed with running the code
            result = subprocess.run([sys.executable, file_path], capture_output=True, text=True)

            if result.returncode == 0:
                message = f"✅ تم تشغيل الملف ({file_index + 1}) بنجاح:\n\n{result.stdout}"
            else:
                message = f"❌ فشل تشغيل الملف ({file_index + 1}):\n\n{result.stderr}"

        user_files[user_id]['files'][file_index]['last_result'] = message
        update.message.reply_text(message)

    except Exception as e:
        user_files[user_id]['files'][file_index]['last_result'] = f"حدث خطأ أثناء التشغيل:\n\n{str(e)}"
        update.message.reply_text(f"حدث خطأ أثناء التشغيل:\n\n{str(e)}")

    finally:
        os.remove(file_path)
        lock.release()

def show_files(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_files or not user_files[user_id]['files']:
        update.message.reply_text("❌ لا توجد ملفات لعرضها.")
        return

    keyboard = []
    for idx, file_info in enumerate(user_files[user_id]['files']):
        keyboard.append([InlineKeyboardButton(f"ملف {idx + 1}: {file_info['path']}", callback_data=f"show_log:{user_id}:{idx}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📂 الملفات الخاصة بك:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split(":")
    action = data[0]
    user_id = int(data[1])
    file_index = int(data[2])

    if action == "show_log":
        query.edit_message_text(text="⏳ جاري جلب السجل...")
        log = user_files[user_id]['files'][file_index]['last_result']
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"back_to_files:{user_id}")]
        ])
        query.edit_message_text(text=log, reply_markup=reply_markup)

    elif action == "back_to_files":
        show_files(update, context)

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "ℹ️ تعليمات البوت:\n"
        "- يمكنك إرسال ملف بايثون ليتم تشغيله.\n"
        "- استخدم /start لإعادة تشغيل البوت وحذف جميع الملفات.\n"
        "- استخدم /show_files لعرض ملفاتك الحالية.\n"
        "- يمكنك عرض السجل لكل ملف بالنقر على الأزرار بعد عرض الملفات."
    )
    update.message.reply_text(help_text)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.document & Filters.private, handle_file))
    dp.add_handler(CommandHandler("show_files", show_files))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
