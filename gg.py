import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import subprocess
import os
import threading
import time
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

    welcome_message = (
        "مرحباً بك في بوت استضافة بايثون! \n"
        "قم بإرسال ملف بايثون (.py) وسيتم تشغيله. إذا كان هناك أي أخطاء، سأخبرك بها. ✅\n"
        "يمكنك عرض ملفاتك بالنقر على الزر أدناه."
    )

    keyboard = [[InlineKeyboardButton("عرض الملفات", callback_data='show_files')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(welcome_message, reply_markup=reply_markup)

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

    user_files[user_id]['files'].append({'path': file_path, 'start_time': 0, 'expiry_time': time.time() + float('inf'), 'last_result': '', 'process': None})

    update.message.reply_text("تم تشغيل الملف بنجاح ساخبرك بحال وجود اخطاء ✅")

    thread = threading.Thread(target=run_python_file, args=(update, user_id, len(user_files[user_id]['files']) - 1))
    thread.start()

def run_python_file(update: Update, user_id: int, file_index: int) -> None:
    try:
        lock.acquire()
        file_info = user_files[user_id]['files'][file_index]
        file_path = file_info['path']
        user_files[user_id]['files'][file_index]['start_time'] = time.time()

        process = subprocess.Popen([sys.executable, '-O', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        user_files[user_id]['files'][file_index]['process'] = process
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            message = f"تم تشغيل الملف ({file_index + 1}) بنجاح ✅:\n\n{stdout}"
        else:
            message = f"فشل تشغيل الملف ({file_index + 1}) ❌:\n\n{stderr}"

        user_files[user_id]['files'][file_index]['last_result'] = message
        update.message.reply_text(message)

    except Exception as e:
        user_files[user_id]['files'][file_index]['last_result'] = f"حدث خطأ أثناء التشغيل:\n\n{str(e)}"
        update.message.reply_text(f"حدث خطأ أثناء التشغيل:\n\n{str(e)}")

    finally:
        lock.release()

def show_files(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in user_files or not user_files[user_id]['files']:
        query.message.reply_text("لا توجد ملفات متاحة.")
        return

    keyboard = []
    for i, file_info in enumerate(user_files[user_id]['files']):
        keyboard.append([InlineKeyboardButton(f"ملف {i + 1}", callback_data=f'show_file_{i}')])

    keyboard.append([InlineKeyboardButton("رجوع", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("اختر ملفاً لعرض تفاصيله:", reply_markup=reply_markup)

def show_file_details(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    file_index = int(query.data.split('_')[2])

    if user_id not in user_files or file_index >= len(user_files[user_id]['files']):
        query.message.reply_text("ملف غير موجود.")
        return

    file_info = user_files[user_id]['files'][file_index]
    last_result = file_info['last_result']

    keyboard = [
        [InlineKeyboardButton("عرض سجل التشغيل", callback_data=f'show_log_{file_index}')],
        [InlineKeyboardButton("حذف", callback_data=f'delete_file_{file_index}')],
        [InlineKeyboardButton("إيقاف التشغيل", callback_data=f'stop_file_{file_index}')],
        [InlineKeyboardButton("رجوع", callback_data='show_files')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(f"تفاصيل ملف {file_index + 1}:\n\n{last_result}", reply_markup=reply_markup)

def show_file_log(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    file_index = int(query.data.split('_')[2])

    if user_id not in user_files or file_index >= len(user_files[user_id]['files']):
        query.message.reply_text("ملف غير موجود.")
        return

    file_info = user_files[user_id]['files'][file_index]
    last_result = file_info['last_result']

    keyboard = [
        [InlineKeyboardButton("رجوع", callback_data=f'show_file_{file_index}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(f"سجل تشغيل ملف {file_index + 1}:\n\n{last_result}", reply_markup=reply_markup)

def delete_file(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    file_index = int(query.data.split('_')[2])

    if user_id not in user_files or file_index >= len(user_files[user_id]['files']):
        query.message.reply_text("ملف غير موجود.")
        return

    file_info = user_files[user_id]['files'].pop(file_index)
    process = file_info['process']

    if process and process.poll() is None:
        process.terminate()

    os.remove(file_info['path'])
    query.message.reply_text("تم حذف الملف بنجاح.")
    show_files(update, context)

def stop_file(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    file_index = int(query.data.split('_')[2])

    if user_id not in user_files or file_index >= len(user_files[user_id]['files']):
        query.message.reply_text("ملف غير موجود.")
        return

    file_info = user_files[user_id]['files'][file_index]
    process = file_info['process']

    if process and process.poll() is None:
        process.terminate()
        query.message.reply_text("تم إيقاف تشغيل الملف بنجاح.")
    else:
        query.message.reply_text("الملف لا يعمل حالياً.")

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    if query.data == 'show_files':
        show_files(update, context)
    elif query.data.startswith('show_file_'):
        show_file_details(update, context)
    elif query.data.startswith('show_log_'):
        show_file_log(update, context)
    elif query.data.startswith('delete_file_'):
        delete_file(update, context)
    elif query.data.startswith('stop_file_'):
        stop_file(update, context)
    elif query.data == 'back':
        start(update, context)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document & Filters.private, handle_file))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
