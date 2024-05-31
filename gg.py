import telebot
import requests

bot_token = "7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20"  # توكن البوت في تليجرام
heroku_api_key = "HRKU-bffcce5a-db84-4c17-97ed-160f04745271"  # مفتاح API الخاص بـ Heroku
github_token = "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"  # توكن GitHub

bot = telebot.TeleBot(bot_token)

HEROKU_BASE_URL = 'https://api.heroku.com'
HEROKU_HEADERS = {
    'Authorization': f'Bearer {heroku_api_key}',
    'Accept': 'application/vnd.heroku+json; version=3'
}

GITHUB_BASE_URL = 'https://api.github.com'
GITHUB_HEADERS = {
    'Authorization': f'token {github_token}',
    'Accept': 'application/vnd.github.v3+json'
}

def create_main_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('قسم هيروكو 🏢', callback_data='heroku_section')
    itembtn2 = telebot.types.InlineKeyboardButton('قسم GitHub 🗂️', callback_data='github_section')
    itembtn3 = telebot.types.InlineKeyboardButton('المطور 👨‍💻', url='https://t.me/q_w_c')
    markup.add(itembtn1, itembtn2)
    markup.add(itembtn3)
    return markup

def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_btn = telebot.types.InlineKeyboardButton('العودة 🔙', callback_data='back_to_main')
    dev_btn = telebot.types.InlineKeyboardButton('المطور 👨‍💻', url='https://t.me/q_w_c')
    markup.add(back_btn, dev_btn)
    return markup

def send_progress(chat_id, progress, message_id=None):
    progress_bar = "⬛" * (progress // 10) + "⬜" * (10 - (progress // 10))
    text = f"تحميل... {progress_bar} {progress}%"
    if message_id:
        bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    else:
        return bot.send_message(chat_id, text).message_id

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "مرحبًا! يمكنك التحكم في حساب هيروكو ومستودعات GitHub باستخدام الأوامر التالية:",
        reply_markup=create_main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'heroku_section':
        bot.edit_message_text(
            "قسم هيروكو:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_heroku_menu()
        )
    elif call.data == 'github_section':
        bot.edit_message_text(
            "قسم GitHub:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_github_menu()
        )
    elif call.data == 'deploy_to_heroku':
        prompt_for_github_repo_for_deploy(call.message)

def create_heroku_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('نشر كود 🚀', callback_data='deploy_to_heroku')
    markup.add(itembtn1)
    markup.add(telebot.types.InlineKeyboardButton('العودة 🔙', callback_data='back_to_main'))
    return markup

def create_github_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.InlineKeyboardButton('عرض مستودعات 📜', callback_data='list_github_repos')
    markup.add(itembtn1)
    markup.add(telebot.types.InlineKeyboardButton('العودة 🔙', callback_data='back_to_main'))
    return markup

def list_github_repos(message):
    response = requests.get(f'{GITHUB_BASE_URL}/user/repos', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        repos = response.json()
        repos_list = "\n".join([f"`{repo['name']}`" for repo in repos])
        bot.send_message(message.chat.id, f"المستودعات المتاحة في GitHub:\n{repos_list}", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.send_message(message.chat.id, "حدث خطأ في جلب المستودعات من GitHub.", reply_markup=create_back_button())

def prompt_for_github_repo_for_deploy(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم المستودع الذي تريد نشره في هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_github_repo_for_deploy_step)

def process_github_repo_for_deploy_step(message):
    repo_name = message.text
    msg = bot.send_message(message.chat.id, "أدخل اسم التطبيق في هيروكو:", reply_markup=create_back_button())
    bot.register_next_step_handler(msg, process_deploy_to_heroku_step, repo_name)

def process_deploy_to_heroku_step(message, repo_name):
    app_name = message.text
    progress_message = bot.send_message(message.chat.id, "جارٍ نشر التطبيق...")
    progress_message_id = progress_message.message_id
    
    for progress in range(0, 101, 10):
        progress_bar = "⬛" * (progress // 10) + "⬜" * (10 - (progress // 10))
        text = f"تحميل... {progress_bar} {progress}%"
        bot.edit_message_text(text, chat_id=message.chat.id, message_id=progress_message_id)
        
    deploy_response = requests.post(
        f'https://api.heroku.com/apps/{app_name}/builds',
        headers={
            'Authorization': f'Bearer {heroku_api_key}',
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json'
        },
        json={"source_blob": {"url": f"https://github.com/YOUR_GITHUB_USERNAME/{repo_name}/tarball/master"}}
    )
    
    if deploy_response.status_code == 201:
        bot.edit_message_text("تم نشر التطبيق بنجاح على هيروكو.", chat_id=message.chat.id, message_id=progress_message_id)
        bot.send_message(message.chat.id, f"تم نشر المستودع `{repo_name}` بنجاح على التطبيق `{app_name}` في هيروكو.", parse_mode='Markdown', reply_markup=create_back_button())
    else:
        bot.edit_message_text("حدث خطأ أثناء نشر التطبيق على هيروكو.", chat_id=message.chat.id, message_id=progress_message_id)
        bot.send_message(message.chat.id, "يرجى التحقق من صحة اسم التطبيق والمستودع ومحاولة مرة أخرى.", reply_markup=create_back_button())

bot.polling()
