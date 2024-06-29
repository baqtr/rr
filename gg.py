import os
import telebot
import requests
import json
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# إعداد توكن البوت
bot_token = "7464446606:AAE_uwUBeetbUCWc9sUoZws2O3NlqUKzTpA"
bot = telebot.TeleBot(bot_token)

# إعداد المتغيرات العامة
total_money = 0
Good = 0
Bad = 0
session_cookies = {}
status_message_id = None
start_time = time.time()

# إعداد الألوان والرموز التعبيرية
check_mark = "✅"
cross_mark = "❌"
money_bag = "💰"
email_icon = "📧"
password_icon = "🔑"
wave_icon = "🌊"
login_icon = "🔓"
error_icon = "⚠️"
clock_icon = "⏰"

# دالة لتسجيل الدخول
def Login(email, password, chat_id):
    global session_cookies
    headers = {
        'authority': 'faucetearner.org',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'ar-YE,ar;q=0.9,en-YE;q=0.8,en-US;q=0.7,en;q=0.6',
        'content-type': 'application/json',
        'origin': 'https://faucetearner.org',
        'referer': 'https://faucetearner.org/login.php',
        'sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML، مثل Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'.encode('latin-1', 'ignore').decode('latin-1'),
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'act': 'login',
    }

    json_data = {
        'email': email,
        'password': password,
    }

    response = requests.post('https://faucetearner.org/api.php', params=params, headers=headers, json=json_data)
    
    if "Login successful" in response.text:
        session_cookies = response.cookies.get_dict()
        bot.send_message(chat_id, f'{login_icon} تسجيل الدخول ناجح!')
        show_status_buttons(chat_id)
        Money(chat_id)
    elif "wrong username or password" in response.text:
        bot.send_message(chat_id, f'{cross_mark} اسم المستخدم أو كلمة المرور خاطئة.')
    else:
        bot.send_message(chat_id, f'{error_icon} خطأ أثناء تسجيل الدخول.')

# دالة لجلب المال بشكل دوري
def Money(chat_id):
    global total_money, Good, Bad, session_cookies
    while True:
        time.sleep(5)
        headers = {
            'authority': 'faucetearner.org',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ar-YE,ar;q=0.9,en-YE;q=0.8,en-US;q=0.7,en;q=0.6',
            'origin': 'https://faucetearner.org',
            'referer': 'https://faucetearner.org/faucet.php',
            'sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML، مثل Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'.encode('latin-1', 'ignore').decode('latin-1'),
            'x-requested-with': 'XMLHttpRequest',
        }

        params = {
            'act': 'faucet',
        }

        rr = requests.post('https://faucetearner.org/api.php', params=params, cookies=session_cookies, headers=headers).text
        
        if 'Congratulations on receiving' in rr:
            Good += 1
            json_data = json.loads(rr)
            message = json_data["message"]
            start_index = message.find(">") + 1
            end_index = message.find(" ", start_index)
            balance = message[start_index:end_index]
            total_money += float(balance)
        elif 'You have already claimed, please wait for the next wave!' in rr:
            Bad += 1
        update_status_buttons(chat_id)

# دالة لإظهار الأزرار
def show_status_buttons(chat_id):
    global status_message_id
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(f"{check_mark} المحاولات الناجحة: {Good}", callback_data="good_attempts"),
        InlineKeyboardButton(f"{cross_mark} المحاولات الفاشلة: {Bad}", callback_data="bad_attempts"),
        InlineKeyboardButton(f"{money_bag} المجموع الكلي: {total_money}", callback_data="total_money"),
        InlineKeyboardButton(f"{clock_icon} وقت التشغيل: {get_uptime()}", callback_data="uptime")
    )
    msg = bot.send_message(chat_id, "الحالة الحالية:", reply_markup=markup)
    status_message_id = msg.message_id

# دالة لتحديث الأزرار
def update_status_buttons(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(f"{check_mark} المحاولات الناجحة: {Good}", callback_data="good_attempts"),
        InlineKeyboardButton(f"{cross_mark} المحاولات الفاشلة: {Bad}", callback_data="bad_attempts"),
        InlineKeyboardButton(f"{money_bag} المجموع الكلي: {total_money}", callback_data="total_money"),
        InlineKeyboardButton(f"{clock_icon} وقت التشغيل: {get_uptime()}", callback_data="uptime")
    )
    try:
        bot.edit_message_reply_markup(chat_id, message_id=status_message_id, reply_markup=markup)
    except Exception as e:
        print(f"Error updating buttons: {e}")

# دالة لحساب وقت التشغيل
def get_uptime():
    uptime_seconds = time.time() - start_time
    uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
    return uptime_string

# دالة لمعالجة أوامر البوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحبًا بك في بوت الصنبور! استخدم /login لبدء التسجيل.")

@bot.message_handler(commands=['login'])
def handle_login(message):
    msg = bot.send_message(message.chat.id, f"{email_icon} يرجى إدخال بريدك الإلكتروني:")
    bot.register_next_step_handler(msg, process_email_step)

def process_email_step(message):
    email = message.text
    msg = bot.send_message(message.chat.id, f"{password_icon} يرجى إدخال كلمة المرور:")
    bot.register_next_step_handler(msg, process_password_step, email)

def process_password_step(message, email):
    password = message.text
    Login(email, password, message.chat.id)

# دالة لمعرفة الرصيد الحالي
@bot.message_handler(commands=['balance'])
def send_balance(message):
    bot.send_message(message.chat.id, f"{money_bag} المجموع الكلي للرصيد: {total_money}")

# دالة لمعرفة عدد المحاولات الناجحة والفاشلة
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.send_message(message.chat.id, f"{check_mark} المحاولات الناجحة: {Good}\n{cross_mark} المحاولات الفاشلة: {Bad}")

# تشغيل البوت
bot.polling(none_stop=True)
