import os
import telebot
import requests
import time
from github import Github

# استيراد التوكنات من المتغيرات البيئية
bot_token = "7031770762:AAF-BrYHNEcX8VyGBzY1mastEG3SWod4_uI"
github_token = "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"
koyeb_token = "cbaa3j79e6se7juh0qkte6a7geck1z51ff6p3t38dl11u26idyllrbkq7cg40hnc"

# إنشاء كائن البوت
bot = telebot.TeleBot(bot_token)
g = Github(github_token)

# الدالة لإنشاء الأزرار وتخصيصها
def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton("🚀 نشر تطبيق", callback_data="deploy_app")
    button2 = telebot.types.InlineKeyboardButton("📊 عرض التطبيقات", callback_data="list_apps")
    button3 = telebot.types.InlineKeyboardButton("🗂️ عرض المستودعات", callback_data="list_repos")
    button4 = telebot.types.InlineKeyboardButton("🗑️ حذف تطبيق", callback_data="delete_app")
    markup.add(button1, button2)
    markup.add(button3, button4)
    return markup

# دالة للرد على /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "أهلاً بك! اختر من الأزرار أدناه:", reply_markup=create_main_buttons())

# دالة لنشر التطبيق
def deploy_app(call):
    bot.send_message(call.message.chat.id, "اختر مستودع GitHub لنشر التطبيق:", reply_markup=create_repos_buttons())

# دالة لإنشاء أزرار المستودعات
def create_repos_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    repos = g.get_user().get_repos()
    for repo in repos:
        button = telebot.types.InlineKeyboardButton(repo.name, callback_data=f"deploy_repo:{repo.full_name}")
        markup.add(button)
    return markup

# دالة لمعالجة نشر التطبيق
def handle_deploy_repo(call, repo_full_name):
    bot.send_message(call.message.chat.id, f"جاري نشر المستودع: {repo_full_name}. يرجى الانتظار...")

    headers = {
        'Authorization': f'Bearer {koyeb_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "name": repo_full_name.split('/')[-1],
        "repository": f"https://github.com/{repo_full_name}.git",
        "branch": "main"
    }
    response = requests.post('https://app.koyeb.com/v1/apps', headers=headers, json=payload)
    
    if response.status_code == 201:
        deployment_id = response.json()['id']
        bot.send_message(call.message.chat.id, f"تم بدء عملية النشر بنجاح! معرف النشر: {deployment_id}")
        track_deployment_status(call.message.chat.id, deployment_id)
    else:
        bot.send_message(call.message.chat.id, f"حدث خطأ أثناء عملية النشر. الرمز: {response.status_code} - الرسالة: {response.text}")

# دالة لمتابعة حالة النشر
def track_deployment_status(chat_id, deployment_id):
    headers = {
        'Authorization': f'Bearer {koyeb_token}',
        'Content-Type': 'application/json'
    }
    while True:
        response = requests.get(f'https://app.koyeb.com/v1/deployments/{deployment_id}', headers=headers)
        status = response.json().get('status')
        bot.send_message(chat_id, f"حالة النشر الحالية: {status}")
        
        if status in ['success', 'failed']:
            break
        
        time.sleep(10)

# دالة لعرض التطبيقات
def list_apps(call):
    headers = {
        'Authorization': f'Bearer {koyeb_token}',
        'Content-Type': 'application/json'
    }
    response = requests.get('https://app.koyeb.com/v1/apps', headers=headers)
    if response.status_code == 200:
        apps = response.json()['apps']
        if apps:
            apps_list = "\n".join([f"معرف: {app['id']} - اسم: {app['name']}" for app in apps])
            bot.send_message(call.message.chat.id, f"التطبيقات المتاحة:\n{apps_list}")
        else:
            bot.send_message(call.message.chat.id, "لا يوجد تطبيقات متاحة حالياً.")
    else:
        bot.send_message(call.message.chat.id, f"حدث خطأ أثناء جلب التطبيقات. الرمز: {response.status_code} - الرسالة: {response.text}")

# دالة لعرض المستودعات
def list_repos(call):
    bot.send_message(call.message.chat.id, "اختر مستودع من القائمة أدناه:", reply_markup=create_repos_buttons())

# دالة لحذف تطبيق
def delete_app(call):
    msg = bot.send_message(call.message.chat.id, "أرسل معرف التطبيق الذي تريد حذفه:")
    bot.register_next_step_handler(msg, handle_delete_app)

def handle_delete_app(message):
    app_id = message.text.strip()
    headers = {
        'Authorization': f'Bearer {koyeb_token}',
        'Content-Type': 'application/json'
    }
    response = requests.delete(f'https://app.koyeb.com/v1/apps/{app_id}', headers=headers)
    if response.status_code == 204:
        bot.send_message(message.chat.id, f"تم حذف التطبيق بنجاح! معرف التطبيق: {app_id}")
    else:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء حذف التطبيق. الرمز: {response.status_code} - الرسالة: {response.text}")

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "deploy_app":
        deploy_app(call)
    elif call.data == "list_apps":
        list_apps(call)
    elif call.data == "list_repos":
        list_repos(call)
    elif call.data == "delete_app":
        delete_app(call)
    elif call.data.startswith("deploy_repo:"):
        repo_full_name = call.data.split(":")[1]
        handle_deploy_repo(call, repo_full_name)

# تشغيل البوت
bot.polling()
