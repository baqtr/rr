import requests
import json
import telebot,webbrowser
from telebot import types

token = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo" 
bot = telebot.TeleBot(token)
print('\033[2;32m\n \n        run')

headers = {
    'authority': 'randommer.io',
    'accept': '*/*',
    'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://randommer.io',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 12; M2004J19C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

@bot.message_handler(commands=["start"])
def welcome(message):
 
 my = types.InlineKeyboardButton(text='Please join the developer channel',url="t.me/MKOOSH")
 xx = types.InlineKeyboardMarkup()
 xx.add(my)
 name = message.chat.first_name
 
 bot.reply_to(message,f'''Send a word
ـ  /Koshovaly''',reply_markup=xx)

@bot.message_handler(commands=['Koshovaly'])
def visa(message):
     data = {
     'Type': 'visa',
     'X-Requested-With': 'XMLHttpRequest',}
     url = requests.post('https://randommer.io/Card',headers=headers, data=data)
     data = json.loads(url.content)
     card = data['cardNumber']
     name = data['fullName']
     cvv = data['cvv']
     pin = data['pin']
     type = data['type']
     date = data['date']
     text =f'{card}\n {cvv}\n {pin}\n {date}\n \n by @AsiacellI2'
     bot.reply_to(message,text)


     

bot.infinity_polling()
