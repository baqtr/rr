import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import subprocess
import os
import threading
import time
import ast
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE"

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

    welcome_message = ":  @AsiacellI2 اهلا بيك في افضل بوت استضافة بايثون يقوم بتشغيل ملفات متعدده كل ماعليك فعله هوه ارسال ملف بايثون وسيتم تشغيله وذا كان يحتوى على اخطاء سايخبرك البوت المطور"
    update.message.reply_text(welcome_message)

def handle_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_files.setdefault(user_id, {'files': [], 'expiry_time': 0, 'last_result': ''})

    if len(user_files[user_id]['files']) >= MAX_FILES_PER_USER:
        update.message.reply_text("لقد تجاوزت الحد الأقصى لعدد الملفات المسموح بها. الرجاء المحاولة مرة أخرى لاحقًا.")
        return

    user_file = update.message.document
    file_name = user_file.file_name

    if not file_name.endswith('.py'):
        update.message.reply_text("الرجاء إرسال ملف بايثون فقط.")
        return

    file_id = user_file.file_id
    file_path = f"{user_id}_{file_name}"
    user_file.get_file().download(file_path)

    user_files[user_id]['files'].append({'path': file_path, 'start_time': 0, 'expiry_time': time.time() + float('inf'), 'last_result': ''})

    update.message.reply_text("تم تشغيل الملف بنجاح ساخبرك بحال وجود اخطاء ✅")

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
            # Attempt to fix syntax errors automatically
            try:
                fixed_code = ast.fix_syntax_error(code)
                with open(file_path, 'w') as f:
                    f.write(fixed_code)
                # Re-run the corrected code
                result = subprocess.run([sys.executable, '-O', file_path], capture_output=True, text=True)

                if result.returncode == 0:
                    message = f"تم تشغيل الملف ({file_index + 1}) بنجاح ✅:\n\n{result.stdout}"
                else:
                    message = f"فشل تشغيل الملف ({file_index + 1}) ❌:\n\n{result.stderr}"
            except Exception as fix_error:
                message = f"تعذر تصحيح الخطأ وتشغيل الملف ({file_index + 1}) ❌:\n\n{fix_error}"
        else:
            # No syntax errors, proceed with running the code
            result = subprocess.run([sys.executable, '-O', file_path], capture_output=True, text=True)

            if result.returncode == 0:
                message = f"تم تشغيل الملف ({file_index + 1}) بنجاح ✅:\n\n{result.stdout}"
            else:
                message = f"فشل تشغيل الملف ({file_index + 1}) ❌:\n\n{result.stderr}"

        user_files[user_id]['files'][file_index]['last_result'] = message
        update.message.reply_text(message)

    except Exception as e:
        user_files[user_id]['files'][file_index]['last_result'] = f"حدث خطأ أثناء التشغيل:\n\n{str(e)}"
        update.message.reply_text(f"حدث خطأ أثناء التشغيل:\n\n{str(e)}")

    finally:
        os.remove(file_path)
        lock.release()

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document & Filters.private, handle_file))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
