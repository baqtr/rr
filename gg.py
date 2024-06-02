import os
import telebot
import requests
import zipfile
import tempfile
import shutil
import random
import string
from github import Github

# استيراد توكن البوت من المتغيرات البيئية
bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"
github_token = "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"

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)
g = Github(github_token)

# دالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("رفع ملف 📤", callback_data="upload_file")
    button2 = telebot.types.InlineKeyboardButton("عرض مستودعات GitHub 📂", callback_data="list_github_repos")
    button3 = telebot.types.InlineKeyboardButton("حذف مستودع 🗑️", callback_data="delete_repo")
    button4 = telebot.types.InlineKeyboardButton("حذف الكل 🗑️", callback_data="delete_all_repos")
    markup.row(button1)
    markup.row(button2)
    markup.row(button3)
    markup.row(button4)
    return markup

# دالة لإنشاء زر العودة
def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back")
    markup.add(back_button)
    return markup

# دالة لمعالجة الطلبات الواردة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", reply_markup=create_main_buttons())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "upload_file":
        msg = bot.send_message(call.message.chat.id, "يرجى إرسال ملف مضغوط بصيغة ZIP.")
        bot.register_next_step_handler(msg, handle_zip_file)
    elif call.data == "list_github_repos":
        list_github_repos(call)
    elif call.data == "delete_repo":
        msg = bot.send_message(call.message.chat.id, "يرجى إرسال اسم المستودع لحذفه.")
        bot.register_next_step_handler(msg, handle_repo_deletion)
    elif call.data == "delete_all_repos":
        delete_all_repos(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())

# دالة لمعالجة ملف ZIP
def handle_zip_file(message):
    if message.document and message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, message.document.file_name)
            with open(zip_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                repo_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                user = g.get_user()
                repo = user.create_repo(repo_name, private=True)
                
                for root, dirs, files in os.walk(temp_dir):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        relative_path = os.path.relpath(file_path, temp_dir)
                        with open(file_path, 'rb') as file_data:
                            repo.create_file(relative_path, f"Add {relative_path}", file_data.read())
                
                num_files = sum([len(files) for r, d, files in os.walk(temp_dir)])
                bot.send_message(message.chat.id, f"تم إنشاء المستودع بنجاح.\nاسم المستودع: `{repo_name}`\nعدد الملفات: {num_files}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "الملف الذي تم إرساله ليس ملف ZIP. يرجى المحاولة مرة أخرى.")

# دالة لعرض مستودعات GitHub
def list_github_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    repo_list = ""
    for repo in repos:
        try:
            contents = repo.get_contents("")
            num_files = sum(1 for _ in contents)
            repo_list += f"اسم المستودع: `{repo.name}`\nعدد الملفات: {num_files}\n\n"
        except Exception as e:
            bot.send_message(call.message.chat.id, f"خطأ في جلب محتويات المستودع `{repo.name}`: {str(e)}")
    if repo_list:
        bot.edit_message_text(f"مستودعات GitHub:\n{repo_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.edit_message_text("لا توجد مستودعات لعرضها.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=create_back_button())

# دالة لحذف مستودع
def handle_repo_deletion(message):
    repo_name = message.text.strip()
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
        repo.delete()
        bot.send_message(message.chat.id, f"تم حذف المستودع `{repo_name}` بنجاح.", parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id, f"المستودع `{repo_name}` غير موجود أو لا تملك صلاحية حذفه.", parse_mode='Markdown')

# دالة لحذف جميع المستودعات
def delete_all_repos(call):
    user = g.get_user()
    repos = user.get_repos()
    repo_count = repos.totalCount
    for repo in repos:
        repo.delete()
    bot.edit_message_text(f"تم حذف جميع المستودعات بنجاح.\nعدد المستودعات المحذوفة: {repo_count}", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=create_back_button())

# التشغيل
if __name__ == "__main__":
    bot.polling()
