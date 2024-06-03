import os
import telebot
import requests
import time
from github import Github
from heroku3 import from_key
from telebot import types
import tempfile
import zipfile

# استيراد التوكنات من المتغيرات البيئية
BOT_TOKEN = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
GITHUB_TOKEN = "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"
HEROKU_API_KEY = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"

# إنشاء كائنات البوت
bot = telebot.TeleBot(BOT_TOKEN)
github = Github(GITHUB_TOKEN)
heroku_conn = from_key(HEROKU_API_KEY)

# قائمة لمتابعة التقدم
progress_tracking = {}

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("نشر مستودع على Heroku 🚀", callback_data="deploy_repo")
    button2 = types.InlineKeyboardButton("عرض مستودعات GitHub 📂", callback_data="list_github_repos")
    markup.add(button1)
    markup.add(button2)
    return markup

# دالة للبدء
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_main_buttons())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "deploy_repo":
        msg = bot.send_message(call.message.chat.id, "يرجى إرسال اسم مستودع GitHub للنشر.")
        bot.register_next_step_handler(msg, ask_for_heroku_app_name)
    elif call.data == "list_github_repos":
        list_github_repos(call)

# دالة لطلب اسم تطبيق Heroku
def ask_for_heroku_app_name(message):
    repo_name = message.text.strip()
    progress_tracking[message.chat.id] = {'repo_name': repo_name}
    msg = bot.send_message(message.chat.id, "يرجى إرسال اسم تطبيق Heroku.")
    bot.register_next_step_handler(msg, handle_repo_deployment)

# دالة لعرض مستودعات GitHub
def list_github_repos(call):
    user = github.get_user()
    repos = user.get_repos()
    repo_list = ""
    loading_message = bot.send_message(call.message.chat.id, "جارٍ جلب المستودعات، يرجى الانتظار...")

    for repo in repos:
        repo_list += f"📂 *اسم المستودع*: `{repo.name}`\n\n"

    if repo_list:
        bot.edit_message_text(f"مستودعات GitHub:\n{repo_list}", chat_id=call.message.chat.id, message_id=loading_message.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text("لا توجد مستودعات لعرضها.", chat_id=call.message.chat.id, message_id=loading_message.message_id, parse_mode='Markdown')

# دالة لمعالجة اسم المستودع والنشر على Heroku
def handle_repo_deployment(message):
    chat_id = message.chat.id
    app_name = message.text.strip()
    repo_name = progress_tracking[chat_id]['repo_name']

    user = github.get_user()
    repo = None
    try:
        repo = user.get_repo(repo_name)
    except:
        bot.send_message(chat_id, f"المستودع `{repo_name}` غير موجود. يرجى المحاولة مرة أخرى.")
        return

    bot.send_message(chat_id, f"جارٍ تنزيل مستودع `{repo_name}` للنشر...")

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, f"{repo_name}.zip")
        with open(zip_path, 'wb') as zip_file:
            zip_file.write(repo.get_archive_link('zipball'))

        bot.send_message(chat_id, "تم تنزيل المستودع. جارٍ التحضير للنشر...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

            try:
                app = heroku_conn.create_app(name=app_name, stack_id='heroku-22')
            except Exception as e:
                bot.send_message(chat_id, f"حدث خطأ أثناء إنشاء تطبيق Heroku: {e}")
                return

            bot.send_message(chat_id, f"تم إنشاء تطبيق Heroku باسم `{app_name}`. جارٍ رفع الملفات...")

            for root, dirs, files in os.walk(temp_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, temp_dir)
                    with open(file_path, 'rb') as file_data:
                        app.create_file(relative_path, file_data.read())

            bot.send_message(chat_id, f"تم نشر المستودع `{repo_name}` بنجاح على Heroku.\nرابط التطبيق: https://{app_name}.herokuapp.com", parse_mode='Markdown')

# تشغيل البوت
if __name__ == "__main__":
    bot.polling()
