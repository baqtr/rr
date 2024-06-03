import os
import telebot
import requests
import time
from github import Github
from heroku3 import from_key
from telebot import types
import tempfile
import zipfile
import random
import string

# استيراد التوكنات من المتغيرات البيئية
BOT_TOKEN = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
GITHUB_TOKEN = "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"
HEROKU_API_KEY = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"

# إنشاء كائنات البوت
bot = telebot.TeleBot(BOT_TOKEN)
github = Github(GITHUB_TOKEN)
heroku_conn = from_key(HEROKU_API_KEY)

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("نشر مستودع على Heroku 🚀", callback_data="deploy_repo")
    button2 = types.InlineKeyboardButton("عرض مستودعات GitHub 📂", callback_data="list_github_repos")
    markup.add(button1, button2)
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
        bot.register_next_step_handler(msg, handle_repo_deployment)
    elif call.data == "list_github_repos":
        list_github_repos(call)

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
    repo_name = message.text.strip()
    user = github.get_user()
    repo = None
    try:
        repo = user.get_repo(repo_name)
    except Exception as e:
        bot.send_message(message.chat.id, f"المستودع `{repo_name}` غير موجود أو حدث خطأ: {e}. يرجى المحاولة مرة أخرى.")
        return

    bot.send_message(message.chat.id, f"جارٍ تنزيل مستودع `{repo_name}` للنشر...")
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, f"{repo_name}.zip")
        try:
            with requests.get(repo.get_archive_link('zipball'), stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as zip_file:
                    for chunk in r.iter_content(chunk_size=8192):
                        zip_file.write(chunk)
        except Exception as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء تنزيل المستودع: {e}")
            return

        bot.send_message(message.chat.id, "تم تنزيل المستودع. جارٍ التحضير للنشر...")

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء استخراج المستودع: {e}")
            return

        app_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        try:
            app = heroku_conn.create_app(app_name)
            app.stack = heroku_conn.stack('heroku-22')
            app.update()
        except Exception as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء إنشاء تطبيق Heroku: {e}")
            return

        bot.send_message(message.chat.id, f"تم إنشاء تطبيق Heroku باسم `{app_name}`. جارٍ رفع الملفات...")

        progress_message = bot.send_message(message.chat.id, "0% - جاري رفع الملفات إلى Heroku...")

        file_count = sum([len(files) for r, d, files in os.walk(temp_dir)])
        current_count = 0

        for root, dirs, files in os.walk(temp_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, temp_dir)
                try:
                    with open(file_path, 'rb') as file_data:
                        app.create_file(relative_path, file_data.read())
                except Exception as e:
                    bot.send_message(message.chat.id, f"حدث خطأ أثناء رفع الملف {file_name}: {e}")
                    return
                current_count += 1
                progress = int((current_count / file_count) * 100)
                bot.edit_message_text(f"{progress}% - جاري رفع الملفات إلى Heroku...", chat_id=progress_message.chat.id, message_id=progress_message.message_id)

        try:
            source_blob = {
                "url": f"https://github.com/{user.login}/{repo_name}/archive/master.zip",
                "version": "master"
            }
            build = app.builds().create(source_blob=source_blob)
            while build.status in ['pending', 'building']:
                time.sleep(5)
                build = app.builds().get(build.id)
                bot.edit_message_text(f"{build.status.capitalize()} - جاري بناء التطبيق...", chat_id=progress_message.chat.id, message_id=progress_message.message_id)

            if build.status == 'succeeded':
                bot.edit_message_text(f"تم نشر المستودع `{repo_name}` بنجاح على Heroku.\nاسم التطبيق: `{app_name}`\nرابط التطبيق: [https://{app_name}.herokuapp.com](https://{app_name}.herokuapp.com)", chat_id=progress_message.chat.id, message_id=progress_message.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text(f"فشل في بناء التطبيق على Heroku: {build.status}", chat_id=progress_message.chat.id, message_id=progress_message.message_id)
        except Exception as e:
            bot.send_message(message.chat.id, f"حدث خطأ أثناء بناء التطبيق على Heroku: {e}")

# تشغيل البوت
if __name__ == "__main__":
    bot.polling()
