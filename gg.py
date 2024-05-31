import os
import json
import time
import zipfile
import threading
from datetime import datetime, timedelta

import requests
import telebot
from telebot import types

API_TOKEN = '7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20'
HEROKU_API_KEY = 'HRKU-bffcce5a-db84-4c17-97ed-160f04745271'
GITHUB_API_KEY = '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'
ADMIN_USER_ID = '7013440973'
ALLOWED_USERS = [ADMIN_USER_ID]

bot = telebot.TeleBot(API_TOKEN)

def send_heroku_request(endpoint, method='GET', data=None):
url = f"https://api.heroku.com{endpoint}"
headers = {
"Authorization": f"Bearer {HEROKU_API_KEY}",
"Accept": "application/vnd.heroku+json; version=3",
}
if method == 'GET':
response = requests.get(url, headers=headers)
elif method == 'POST':
headers["Content-Type"] = "application/json"
response = requests.post(url, headers=headers, data=json.dumps(data))
elif method == 'PATCH':
headers["Content-Type"] = "application/json"
response = requests.patch(url, headers=headers, data=json.dumps(data))
elif method == 'DELETE':
response = requests.delete(url, headers=headers)
return response.json()

def send_github_request(endpoint, method='GET', data=None):
url = f"https://api.github.com{endpoint}"
headers = {
"Authorization": f"Bearer {GITHUB_API_KEY}",
"Accept": "application/vnd.github.v3+json",
}
if method == 'GET':
response = requests.get(url, headers=headers)
elif method == 'POST':
headers["Content-Type"] = "application/json"
response = requests.post(url, headers=headers, data=json.dumps(data))
elif method == 'PUT':
headers["Content-Type"] = "application/json"
response = requests.put(url, headers=headers, data=json.dumps(data))
elif method == 'DELETE':
response = requests.delete(url, headers=headers)
return response.json()

def check_permissions(user_id):
if str(user_id) not in ALLOWED_USERS:
return False
return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
if not check_permissions(message.from_user.id):
bot.send_message(message.chat.id, "You are not authorized to use this bot.")
return

markup = types.InlineKeyboardMarkup(row_width=1)

heroku_github_buttons = [
types.InlineKeyboardButton("🚀 قسم هيروكو", callback_data='heroku_section'),
types.InlineKeyboardButton("📁 قسم جيتهاب", callback_data='github_section'),
]

for btn in heroku_github_buttons:
markup.add(btn)

developer_btn = types.InlineKeyboardButton("🔧 Developer: 𓆩𝙎َِ𝘢َِ𝘿 َِ𝙍َِ𝘼َِ𝙀َِ𝘿𓆪", url='https://t.me/q_w_c')
markup.add(developer_btn)

bot.send_message(message.chat.id, "مرحبًا بك في بوت إدارة Heroku و GitHub. اختر قسمًا:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
if not check_permissions(call.from_user.id):
bot.send_message(call.message.chat.id, "You are not authorized to use this bot.")
return

if call.data == 'heroku_section':
handle_heroku_section(call.message)
elif call.data == 'github_section':
handle_github_section(call.message)
elif call.data.startswith('heroku_'):
handle_heroku_actions(call)
elif call.data.startswith('github_'):
handle_github_actions(call)
elif call.data == 'list_allowed_users':
handle_list_allowed_users(call.message)
elif call.data == 'add_allowed_user':
handle_add_allowed_user(call.message)
elif call.data == 'remove_allowed_user':
handle_remove_allowed_user(call.message)

def handle_heroku_section(message):
markup = types.InlineKeyboardMarkup(row_width=1)

heroku_btns = [
types.InlineKeyboardButton("🚀 إنشاء تطبيق", callback_data='heroku_create_app'),
types.InlineKeyboardButton("📄 قائمة التطبيقات", callback_data='heroku_list_apps'),
types.InlineKeyboardButton("🔗 ربط مستودع", callback_data='heroku_link_repo_to_app'),
types.InlineKeyboardButton("🗑️ حذف تطبيق", callback_data='heroku_delete_app'),
types.InlineKeyboardButton("🔄 إعادة تشغيل تطبيق", callback_data='heroku_restart_app'),
types.InlineKeyboardButton("⚙️ ضبط Dyno", callback_data='heroku_set_dyno'),
types.InlineKeyboardButton("⏰ ضبط مؤقت الحذف", callback_data='heroku_set_delete_timer'),
types.InlineKeyboardButton("🚫 إيقاف تطبيق", callback_data='heroku_stop_app'),
types.InlineKeyboardButton("📂 نشر تطبيق", callback_data='heroku_deploy_app'),
types.InlineKeyboardButton("✏️ إعادة تسمية تطبيق", callback_data='heroku_rename_app'),
types.InlineKeyboardButton("🔙 العودة", callback_data='back_to_main')
]

for btn in heroku_btns:
markup.add(btn)

bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="🟦 قسم هيروكو 🟦", reply_markup=markup)

def handle_github_section(message):
markup = types.InlineKeyboardMarkup(row_width=1)

github_btns = [
types.InlineKeyboardButton("📁 إنشاء مستودع", callback_data='github_create_repo'),
types.InlineKeyboardButton("📄 قائمة المستودعات", callback_data='github_list_repos'),
types.InlineKeyboardButton("🗑️ حذف مستودع", callback_data='github_delete_repo'),
types.InlineKeyboardButton("📤 رفع ملفات", callback_data='github_upload_files'),
types.InlineKeyboardButton("🔑 تغيير مفتاح API", callback_data='github_change_api_key'),
types.InlineKeyboardButton("🔙 العودة", callback_data='back_to_main')
]

for btn in github_btns:
markup.add(btn)

bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="🟦 قسم جيتهاب 🟦", reply_markup=markup)

def handle_heroku_actions(call):
if call.data == 'heroku_create_app':
handle_create_app(call.message)
elif call.data == 'heroku_list_apps':
handle_list_apps(call.message)
elif call.data == 'heroku_link_repo_to_app':
handle_link_repo_to_app(call.message)
elif call.data == 'heroku_delete_app':
handle_list_apps_for_deletion(call.message)
elif call.data == 'heroku_restart_app':
handle_restart_app(call.message)
elif call.data == 'heroku_set_dyno':
handle_set_dyno(call.message)
elif call.data == 'heroku_set_delete_timer':
handle_set_delete_timer(call.message)
elif call.data == 'heroku_stop_app':
handle_stop_app(call.message)
elif call.data == 'heroku_deploy_app':
handle_deploy_app(call.message)
elif call.data == 'heroku_rename_app':
handle_rename_app(call.message)
elif call.data == 'back_to_main':
send_welcome(call.message)

def handle_github_actions(call):
if call.data == 'github_create_repo':
handle_create_repo(call.message)
elif call.data == 'github_list_repos':
handle_list_repos(call.message)
elif call.data == 'github_delete_repo':
handle_list_repos_for_deletion(call.message)
elif call.data == 'github_upload_files':
handle_upload_files(call.message)
elif call.data == 'github_change_api_key':
handle_change_github_api_key(call.message)
elif call.data == 'back_to_main':
send_welcome(call.message)

def handle_create_app(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الجديد في هيروكو:")
bot.register_next_step_handler(message, create_app)

def create_app(message):
app_name = message.text.strip()
data = {"name": app_name, "region": "eu"}
response = send_heroku_request("/apps", method="POST", data=data)
if "id" in response:
bot.send_message(message.chat.id, f"✅ التطبيق {app_name} تم إنشاؤه بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في إنشاء التطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_list_apps(message):
apps = send_heroku_request("/apps")
if apps:
app_names = "\n".join([f"`{app['name']}`" for app in apps])
bot.send_message(message.chat.id, f"📄 التطبيقات المتاحة:\n{app_names}", parse_mode='Markdown')
else:
bot.send_message(message.chat.id, "❌ لم يتم العثور على أي تطبيقات.")

def handle_link_repo_to_app(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في ربطه بمستودع جيتهاب:")
bot.register_next_step_handler(message, get_app_name_for_linking)

def get_app_name_for_linking(message):
app_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال عنوان المستودع (repository URL):")
bot.register_next_step_handler(message, link_repo_to_app, app_name)

def link_repo_to_app(message, app_name):
repo_url = message.text.strip()
data = {
"source_blob": {
"url": repo_url,
}
}
response = send_heroku_request(f"/apps/{app_name}/builds", method="POST", data=data)
if "id" in response:
bot.send_message(message.chat.id, f"✅ تم ربط المستودع {repo_url} بالتطبيق {app_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في ربط المستودع بالتطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_list_apps_for_deletion(message):
apps = send_heroku_request("/apps")
if apps:
markup = types.InlineKeyboardMarkup(row_width=1)
for app in apps:
markup.add(types.InlineKeyboardButton(app['name'], callback_data=f"delete_app_{app['id']}"))
bot.send_message(message.chat.id, "🔵 اختر التطبيق الذي ترغب في حذفه:", reply_markup=markup)
else:
bot.send_message(message.chat.id, "❌ لم يتم العثور على أي تطبيقات.")

def handle_restart_app(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في إعادة تشغيله:")
bot.register_next_step_handler(message, restart_app)

def restart_app(message):
app_name = message.text.strip()
response = send_heroku_request(f"/apps/{app_name}/dynos", method="DELETE")
if not response:
bot.send_message(message.chat.id, f"✅ التطبيق {app_name} تم إعادة تشغيله بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في إعادة تشغيل التطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_set_dyno(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في ضبط dyno له:")
bot.register_next_step_handler(message, get_app_name_for_dyno)

def get_app_name_for_dyno(message):
app_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال اسم dyno الجديد:")
bot.register_next_step_handler(message, set_dyno, app_name)

def set_dyno(message, app_name):
dyno_name = message.text.strip()
data = {"type": dyno_name, "quantity": 1, "size": "free"}
response = send_heroku_request(f"/apps/{app_name}/formation", method="PATCH", data=data)
if "id" in response:
bot.send_message(message.chat.id, f"✅ تم ضبط dyno {dyno_name} للتطبيق {app_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في ضبط dyno: {response.get('message', 'خطأ غير معروف')}")

def handle_set_delete_timer(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في ضبط مؤقت الحذف له:")
bot.register_next_step_handler(message, get_app_name_for_delete_timer)

def get_app_name_for_delete_timer(message):
app_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال الوقت المتبقي (بالدقائق) قبل الحذف:")
bot.register_next_step_handler(message, set_delete_timer, app_name)

def set_delete_timer(message, app_name):
try:
minutes = int(message.text.strip())
delete_time = datetime.now() + timedelta(minutes=minutes)
threading.Timer(minutes * 60, delete_app_by_name, args=[app_name]).start()
bot.send_message(message.chat.id, f"✅ سيتم حذف التطبيق {app_name} بعد {minutes} دقيقة.")
except ValueError:
bot.send_message(message.chat.id, "❌ الوقت المدخل غير صحيح. يرجى إدخال عدد الدقائق بشكل صحيح.")

def delete_app_by_name(app_name):
response = send_heroku_request(f"/apps/{app_name}", method="DELETE")
if response == {}:
print(f"✅ التطبيق {app_name} تم حذفه بنجاح.")
else:
print(f"❌ فشل في حذف التطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_stop_app(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في إيقافه:")
bot.register_next_step_handler(message, stop_app)

def stop_app(message):
app_name = message.text.strip()
response = send_heroku_request(f"/apps/{app_name}/formation", method="PATCH", data={"quantity": 0})
if "id" in response:
bot.send_message(message.chat.id, f"✅ تم إيقاف التطبيق {app_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في إيقاف التطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_deploy_app(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في نشره:")
bot.register_next_step_handler(message, get_app_name_for_deploy)

def get_app_name_for_deploy(message):
app_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال عنوان المستودع (repository URL) الذي ترغب في نشره:")
bot.register_next_step_handler(message, deploy_app, app_name)

def deploy_app(message, app_name):
repo_url = message.text.strip()
data = {
"source_blob": {
"url": repo_url,
}
}
response = send_heroku_request(f"/apps/{app_name}/builds", method="POST", data=data)
if "id" in response:
bot.send_message(message.chat.id, f"✅ تم نشر المستودع {repo_url} للتطبيق {app_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في نشر التطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_rename_app(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم التطبيق الذي ترغب في إعادة تسميته:")
bot.register_next_step_handler(message, get_app_name_for_rename)

def get_app_name_for_rename(message):
app_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال الاسم الجديد للتطبيق:")
bot.register_next_step_handler(message, rename_app, app_name)

def rename_app(message, app_name):
new_app_name = message.text.strip()
data = {"name": new_app_name}
response = send_heroku_request(f"/apps/{app_name}", method="PATCH", data=data)
if "id" in response:
bot.send_message(message.chat.id, f"✅ تم إعادة تسمية التطبيق {app_name} إلى {new_app_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في إعادة تسمية التطبيق: {response.get('message', 'خطأ غير معروف')}")

def handle_create_repo(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم المستودع الجديد في جيتهاب:")
bot.register_next_step_handler(message, create_repo)

def create_repo(message):
repo_name = message.text.strip()
data = {"name": repo_name, "private": False}
response = send_github_request("/user/repos", method="POST", data=data)
if "id" in response:
bot.send_message(message.chat.id, f"✅ تم إنشاء المستودع {repo_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في إنشاء المستودع: {response.get('message', 'خطأ غير معروف')}")

def handle_list_repos(message):
repos = send_github_request("/user/repos")
if repos:
repo_names = "\n".join([f"`{repo['name']}`" for repo in repos])
bot.send_message(message.chat.id, f"📄 المستودعات المتاحة:\n{repo_names}", parse_mode='Markdown')
else:
bot.send_message(message.chat.id, "❌ لم يتم العثور على أي مستودعات.")

def handle_list_repos_for_deletion(message):
repos = send_github_request("/user/repos")
if repos:
markup = types.InlineKeyboardMarkup(row_width=1)
for repo in repos:
markup.add(types.InlineKeyboardButton(repo['name'], callback_data=f"delete_repo_{repo['id']}"))
bot.send_message(message.chat.id, "🔵 اختر المستودع الذي ترغب في حذفه:", reply_markup=markup)
else:
bot.send_message(message.chat.id, "❌ لم يتم العثور على أي مستودعات.")

def handle_upload_files(message):
bot.send_message(message.chat.id, "🔵 إرسال اسم المستودع الذي ترغب في رفع الملفات إليه:")
bot.register_next_step_handler(message, get_repo_name_for_upload)

def get_repo_name_for_upload(message):
repo_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال اسم الملف الذي ترغب في رفعه:")
bot.register_next_step_handler(message, get_file_name_for_upload, repo_name)

def get_file_name_for_upload(message, repo_name):
file_name = message.text.strip()
bot.send_message(message.chat.id, "🔵 إرسال محتوى الملف:")
bot.register_next_step_handler(message, upload_file_to_repo, repo_name, file_name)

def upload_file_to_repo(message, repo_name, file_name):
file_content = message.text.strip()
data = {
"message": f"Upload {file_name}",
"content": file_content.encode("utf-8").decode("ascii"),
"branch": "main"
}
response = send_github_request(f"/repos/{repo_name}/contents/{file_name}", method="PUT", data=data)
if "content" in response:
bot.send_message(message.chat.id, f"✅ تم رفع الملف {file_name} إلى المستودع {repo_name} بنجاح.")
else:
bot.send_message(message.chat.id, f"❌ فشل في رفع الملف: {response.get('message', 'خطأ غير معروف')}")

def send_heroku_request(endpoint, method="GET", data=None):
url = f"https://api.heroku.com{endpoint}"
headers = {
"Authorization": f"Bearer {HEROKU_API_KEY}",
"Accept": "application/vnd.heroku+json; version=3",
"Content-Type": "application/json"
}
response = requests.request(method, url, headers=headers, json=data)
return response.json() if response.status_code in range(200, 299) else response.json()

def send_github_request(endpoint, method="GET", data=None):
url = f"https://api.github.com{endpoint}"
headers = {
"Authorization": f"Bearer {GITHUB_API_KEY}",
"Accept": "application/vnd.github.v3+json",
"Content-Type": "application/json"
}
response = requests.request(method, url, headers=headers, json=data)
return response.json() if response.status_code in range(200, 299) else response.json()

bot.polling(none_stop=True)
