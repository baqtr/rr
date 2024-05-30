import telebot
import requests
import json
import zipfile
import os
from datetime import datetime, timedelta
import threading
from telebot import types

bot_token = '7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20'  # استبدل بـ توكن البوت الخاص بك
heroku_api_key = 'HRKU-9c7ef067-cae2-4294-876e-4d91accff033'  # استبدل بـ API key الخاص بـ Heroku
github_api_key = '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'  # استبدل بـ API key الخاص بـ GitHub
admin_id = '7013440973'  # استبدل بـ Telegram ID الخاص بك

allowed_users = {admin_id}

bot = telebot.TeleBot(bot_token)
heroku_url = "https://api.heroku.com"
github_url = "https://api.github.com"
heroku_headers = {
    "Authorization": f"Bearer {heroku_api_key}",
    "Accept": "application/vnd.heroku+json; version=3"
}
github_headers = {
    "Authorization": f"token {github_api_key}",
    "Accept": "application/vnd.github.v3+json"
}

# دالة لإرسال طلبات إلى API الخاصة بـ Heroku
def send_heroku_request(endpoint, method='GET', data=None):
    url = f"{heroku_url}{endpoint}"
    response = requests.request(method, url, headers=heroku_headers, json=data)
    return response.json()

# دالة لإرسال طلبات إلى API الخاصة بـ GitHub
def send_github_request(endpoint, method='GET', data=None):
    url = f"{github_url}{endpoint}"
    response = requests.request(method, url, headers=github_headers, json=data)
    return response.json()

# رسالة ترحيبية وأزرار التحكم
@bot.message_handler(commands=['start'])
def start_message(message):
    if str(message.chat.id) not in allowed_users:
        bot.send_message(message.chat.id, "عذراً، ليس لديك إذن لاستخدام هذا البوت.")
        return

    keyboard = types.InlineKeyboardMarkup()

    heroku_section = types.InlineKeyboardButton(text="Heroku Section", callback_data="heroku_section")
    github_section = types.InlineKeyboardButton(text="GitHub Section", callback_data="github_section")
    request_button = types.InlineKeyboardButton(text="المطور 👨‍💻 ", url="https://t.me/q_w_c")
    allowed_users_button = types.InlineKeyboardButton(text="ايدي الادمن 🙂 ", callback_data="allowed_users")

    keyboard.add(heroku_section)
    keyboard.add(github_section)
    keyboard.add(request_button)
    keyboard.add(allowed_users_button)

    bot.send_message(message.chat.id, "مرحبًا بك في بوت التحكم في Heroku و GitHub! اختر القسم الذي تريد العمل عليه:", reply_markup=keyboard)

# عرض المستخدمين المسموح لهم
def show_allowed_users(chat_id):
    users = "\n".join(allowed_users)
    bot.send_message(chat_id, f"المستخدمين المسموح لهم:\n{users}")

# عرض خيارات Heroku
def show_heroku_options(chat_id):
    keyboard = types.InlineKeyboardMarkup()

    create_app_button = types.InlineKeyboardButton(text="➕ إنشاء تطبيق جديد", callback_data="create_app")
    list_apps_button = types.InlineKeyboardButton(text="📜 عرض التطبيقات", callback_data="list_apps")
    delete_app_button = types.InlineKeyboardButton(text="🗑️ حذف التطبيقات", callback_data="delete_app")
    scale_dyno_button = types.InlineKeyboardButton(text="⚙️ تغيير عدد Dyno", callback_data="scale_dyno")
    restart_app_button = types.InlineKeyboardButton(text="🔄 إعادة تشغيل التطبيق", callback_data="restart_app")
    set_timer_button = types.InlineKeyboardButton(text="⏰ تعيين وقت وحذف التطبيق", callback_data="set_timer")
    change_heroku_key_button = types.InlineKeyboardButton(text="🔑 تغيير API Key لـ Heroku", callback_data="change_heroku_key")
    deploy_app_button = types.InlineKeyboardButton(text="🚀 نشر التطبيق", callback_data="deploy_app")

    keyboard.add(create_app_button)
    keyboard.add(list_apps_button)
    keyboard.add(delete_app_button)
    keyboard.add(scale_dyno_button)
    keyboard.add(restart_app_button)
    keyboard.add(set_timer_button)
    keyboard.add(change_heroku_key_button)
    keyboard.add(deploy_app_button)

    bot.send_message(chat_id, "اختر العملية التي تريد تنفيذها في قسم Heroku:", reply_markup=keyboard)

# عرض خيارات GitHub
def show_github_options(chat_id):
    keyboard = types.InlineKeyboardMarkup()

    create_repo_button = types.InlineKeyboardButton(text="➕ إنشاء مستودع خاص", callback_data="create_repo")
    delete_repo_button = types.InlineKeyboardButton(text="🗑️ حذف مستودع", callback_data="delete_repo")
    upload_files_button = types.InlineKeyboardButton(text="📤 رفع ملفات إلى GitHub", callback_data="upload_files")
    change_github_key_button = types.InlineKeyboardButton(text="🔑 تغيير API Key لـ GitHub", callback_data="change_github_key")
    link_github_button = types.InlineKeyboardButton(text="🔗 ربط GitHub بتطبيق", callback_data="link_github")

    keyboard.add(create_repo_button)
    keyboard.add(delete_repo_button)
    keyboard.add(upload_files_button)
    keyboard.add(change_github_key_button)
    keyboard.add(link_github_button)

    bot.send_message(chat_id, "اختر العملية التي تريد تنفيذها في قسم GitHub:", reply_markup=keyboard)

# معالجة ضغطات الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if str(call.message.chat.id) not in allowed_users:
        bot.send_message(call.message.chat.id, "عذراً، ليس لديك إذن لاستخدام هذا البوت.")
        return

    if call.data == "heroku_section":
        show_heroku_options(call.message.chat.id)
    elif call.data == "github_section":
        show_github_options(call.message.chat.id)
    elif call.data == "create_app":
        bot.send_message(call.message.chat.id, "أرسل اسم التطبيق الجديد.")
        bot.register_next_step_handler(call.message, create_app)
    elif call.data == "list_apps":
        list_apps(call.message)
    elif call.data == "delete_app":
        list_apps_for_deletion(call.message)
    elif call.data == "scale_dyno":
        bot.send_message(call.message.chat.id, "أرسل اسم التطبيق وعدد الدينو بالشكل التالي:\napp_name dyno_count")
        bot.register_next_step_handler(call.message, scale_dyno)
    elif call.data == "restart_app":
        bot.send_message(call.message.chat.id, "أرسل اسم التطبيق الذي تريد إعادة تشغيله.")
        bot.register_next_step_handler(call.message, restart_app)
    elif call.data == "set_timer":
        bot.send_message(call.message.chat.id, "أرسل اسم التطبيق ومدة الوقت بالدقائق بالشكل التالي:\napp_name minutes")
        bot.register_next_step_handler(call.message, set_timer)
    elif call.data == "change_heroku_key":
        bot.send_message(call.message.chat.id, "أرسل API Key الجديد لـ Heroku.")
        bot.register_next_step_handler(call.message, change_heroku_key)
    elif call.data == "deploy_app":
        bot.send_message(call.message.chat.id, "أرسل اسم التطبيق الذي تريد نشره.")
        bot.register_next_step_handler(call.message, deploy_app)
    elif call.data == "create_repo":
        bot.send_message(call.message.chat.id, "أرسل اسم المستودع الجديد.")
        bot.register_next_step_handler(call.message, create_repo)
    elif call.data == "delete_repo":
        list_repos_for_deletion(call.message)
    elif call.data == "upload_files":
        bot.send_message(call.message.chat.id, "أرسل اسم المستودع الذي تريد رفع الملفات إليه.")
        bot.register_next_step_handler(call.message, get_repo_name_for_upload)
    elif call.data == "change_github_key":
        bot.send_message(call.message.chat.id, "أرسل API Key الجديد لـ GitHub.")
        bot.register_next_step_handler(call.message, change_github_key)
    elif call.data == "link_github":
        bot.send_message(call.message.chat.id, "أرسل اسم التطبيق واسم مستودع GitHub بالشكل التالي:\napp_name repo_name")
        bot.register_next_step_handler(call.message, link_github)
    elif call.data == "allowed_users":
        show_allowed_users(call.message.chat.id)

# تغيير مفتاح API لـ Heroku
def change_heroku_key(message):
    global heroku_api_key, heroku_headers
    heroku_api_key = message.text.strip()
    heroku_headers = {
        "Authorization": f"Bearer {heroku_api_key}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    bot.send_message(message.chat.id, "تم تغيير API Key لـ Heroku بنجاح.")

# تغيير مفتاح API لـ GitHub
def change_github_key(message):
    global github_api_key, github_headers
    github_api_key = message.text.strip()
    github_headers = {
        "Authorization": f"token {github_api_key}",
        "Accept": "application/vnd.github.v3+json"
    }
    bot.send_message(message.chat.id, "تم تغيير API Key لـ GitHub بنجاح.")

# إنشاء تطبيق جديد
def create_app(message):
    app_name = message.text.strip()
    data = {
        "name": app_name,
        "region": "us"
    }
    response = send_heroku_request("/apps", method="POST", data=data)
    if "id" in response:
        bot.send_message(message.chat.id, f"تم إنشاء التطبيق بنجاح: {app_name}")
    else:
        bot.send_message(message.chat.id, f"فشل في إنشاء التطبيق: {response.get('message', 'Unknown error')}")

# عرض قائمة التطبيقات
def list_apps(message):
    apps = send_heroku_request("/apps")
    if apps:
        app_names = "\n".join([app['name'] for app in apps])
        bot.send_message(message.chat.id, f"التطبيقات المتاحة:\n{app_names}")
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على تطبيقات.")

# عرض قائمة التطبيقات للحذف
def list_apps_for_deletion(message):
    apps = send_heroku_request("/apps")
    if apps:
        app_names = "\n".join([app['name'] for app in apps])
        bot.send_message(message.chat.id, f"التطبيقات المتاحة:\n{app_names}\n\nأرسل اسم التطبيق الذي تريد حذفه.")
        bot.register_next_step_handler(message, delete_app)
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على تطبيقات.")

# حذف تطبيق
def delete_app(message):
    app_name = message.text.strip()
    response = send_heroku_request(f"/apps/{app_name}", method="DELETE")
    if response == {}:
        bot.send_message(message.chat.id, f"تم حذف التطبيق: {app_name}")
    else:
        bot.send_message(message.chat.id, f"فشل في حذف التطبيق: {response.get('message', 'Unknown error')}")

# تغيير عدد Dyno
def scale_dyno(message):
    try:
        app_name, dyno_count = message.text.split()
        dyno_count = int(dyno_count)
        data = {
            "quantity": dyno_count,
            "size": "standard-2x"
        }
        response = send_heroku_request(f"/apps/{app_name}/formation/web", method="PATCH", data=data)
        if "id" in response:
            bot.send_message(message.chat.id, f"تم تغيير عدد Dyno للتطبيق {app_name} إلى {dyno_count}.")
        else:
            bot.send_message(message.chat.id, f"فشل في تغيير عدد Dyno: {response.get('message', 'Unknown error')}")
    except ValueError:
        bot.send_message(message.chat.id, "يرجى إرسال اسم التطبيق وعدد الدينو بالشكل الصحيح.")

# إعادة تشغيل التطبيق
def restart_app(message):
    app_name = message.text.strip()
    response = send_heroku_request(f"/apps/{app_name}/dynos", method="DELETE")
    if "id" in response:
        bot.send_message(message.chat.id, f"تم إعادة تشغيل التطبيق: {app_name}")
    else:
        bot.send_message(message.chat.id, f"فشل في إعادة تشغيل التطبيق: {response.get('message', 'Unknown error')}")

# تعيين وقت وحذف التطبيق
def set_timer(message):
    try:
        app_name, minutes = message.text.split()
        minutes = int(minutes)
        delete_time = datetime.now() + timedelta(minutes=minutes)
        bot.send_message(message.chat.id, f"سيتم حذف التطبيق {app_name} بعد {minutes} دقائق.")

        def delete_app_after_time():
            nonlocal app_name
            response = send_heroku_request(f"/apps/{app_name}", method="DELETE")
            if response == {}:
                bot.send_message(message.chat.id, f"تم حذف التطبيق {app_name} بعد انتهاء الوقت المحدد.")
            else:
                bot.send_message(message.chat.id, f"فشل في حذف التطبيق بعد انتهاء الوقت: {response.get('message', 'Unknown error')}")

        timer_thread = threading.Timer(minutes * 60, delete_app_after_time)
        timer_thread.start()
    except ValueError:
        bot.send_message(message.chat.id, "يرجى إرسال اسم التطبيق ومدة الوقت بالدقائق بالشكل الصحيح.")

# نشر التطبيق على Heroku
def deploy_app(message):
    app_name = message.text.strip()
    data = {
        "updates": [{
            "app": app_name,
            "process_types": {
                "web": "standard-2x"
            }
        }]
    }
    response = send_heroku_request(f"/apps/{app_name}/formation", method="PATCH", data=data)
    if "id" in response:
        bot.send_message(message.chat.id, f"تم نشر التطبيق بنجاح: {app_name}")
    else:
        bot.send_message(message.chat.id, f"فشل في نشر التطبيق: {response.get('message', 'Unknown error')}")

# إنشاء مستودع جديد
def create_repo(message):
    repo_name = message.text.strip()
    data = {
        "name": repo_name,
        "private": True
    }
    response = send_github_request("/user/repos", method="POST", data=data)
    if "id" in response:
        bot.send_message(message.chat.id, f"تم إنشاء المستودع بنجاح: {repo_name}")
    else:
        bot.send_message(message.chat.id, f"فشل في إنشاء المستودع: {response.get('message', 'Unknown error')}")

# عرض قائمة المستودعات للحذف
def list_repos_for_deletion(message):
    repos = send_github_request("/user/repos")
    if repos:
        repo_names = "\n".join([repo['name'] for repo in repos])
        bot.send_message(message.chat.id, f"المستودعات المتاحة:\n{repo_names}\n\nأرسل اسم المستودع الذي تريد حذفه.")
        bot.register_next_step_handler(message, delete_repo)
    else:
        bot.send_message(message.chat.id, "لم يتم العثور على مستودعات.")

# حذف مستودع
def delete_repo(message):
    repo_name = message.text.strip()
    response = send_github_request(f"/repos/{repo_name}", method="DELETE")
    if response == {}:
        bot.send_message(message.chat.id, f"تم حذف المستودع: {repo_name}")
    else:
        bot.send_message(message.chat.id, f"فشل في حذف المستودع: {response.get('message', 'Unknown error')}")

# رفع الملفات إلى GitHub
def get_repo_name_for_upload(message):
    repo_name = message.text.strip()
    bot.send_message(message.chat.id, "أرسل الملف المضغوط الذي يحتوي على الملفات.")
    bot.register_next_step_handler(message, upload_files, repo_name)

def upload_files(message, repo_name):
    if message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.zip", 'wb') as new_file:
            new_file.write(downloaded_file)
        
        with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_unzipped")
        
        for root, dirs, files in os.walk("temp_unzipped"):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    content = f.read().encode('base64')
                data = {
                    "message": "Upload files via bot",
                    "committer": {
                        "name": "Bot",
                        "email": "bot@example.com"
                    },
                    "content": content
                }
                file_name = os.path.relpath(file_path, "temp_unzipped")
                response = send_github_request(f"/repos/{repo_name}/contents/{file_name}", method="PUT", data=data)
                if "content" not in response:
                    bot.send_message(message.chat.id, f"فشل في رفع الملف: {file_name}\nError: {response.get('message', 'Unknown error')}")
        
        os.remove("temp.zip")
        for root, dirs, files in os.walk("temp_unzipped", topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir("temp_unzipped")
        bot.send_message(message.chat.id, f"تم رفع الملفات إلى المستودع: {repo_name}")
    else:
        bot.send_message(message.chat.id, "يرجى إرسال ملف مضغوط بصيغة ZIP.")

# ربط GitHub بتطبيق Heroku
def link_github(message):
    try:
        app_name, repo_name = message.text.split()
        data = {
            "source_blob": {
                "url": f"https://github.com/{repo_name}/tarball/main"
            }
        }
        response = send_heroku_request(f"/apps/{app_name}/builds", method="POST", data=data)
        if "id" in response:
            bot.send_message(message.chat.id, f"تم ربط المستودع {repo_name} بالتطبيق {app_name} بنجاح.")
        else:
            bot.send_message(message.chat.id, f"فشل في ربط المستودع بالتطبيق: {response.get('message', 'Unknown error')}")
    except ValueError:
        bot.send_message(message.chat.id, "يرجى إرسال اسم التطبيق واسم مستودع GitHub بالشكل الصحيح.")

# تشغيل البوت
bot.polling()
