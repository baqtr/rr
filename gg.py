import telebot
import requests
import json
tok = "token"
bot = telebot.TeleBot(tok)

def ask_gpt(msg):
    u = "https://us-central1-amor-ai.cloudfunctions.net/chatWithGPT"
    p = json.dumps({"data": {"messages": [{"role": "user", "content": msg}]}})
    h = {'User-Agent': "okhttp/5.0.0-alpha.2", 'Accept-Encoding': "gzip", 'content-type': "application/json; charset=utf-8"}
    r = requests.post(u, data=p, headers=h).text
    return json.loads(r)['result']['choices'][0]['message']['content']

@bot.message_handler(commands=['start'])
def send_welcome(m):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton('بدء المحادثة مع GPT', callback_data='start_chat')
    markup.add(btn)
    bot.send_message(m.chat.id, "أهلاً بك! اضغط على الزر لبدء المحادثة مع الذكاء الاصطناعي.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'start_chat')
def start_chat(c):
    bot.send_message(c.message.chat.id, "تم بدء المحادثة. اكتب أي شيء للبدء في الحديث.")
    bot.register_next_step_handler_by_chat_id(c.message.chat.id, handle_conversation)

def handle_conversation(m):
    if m.text.lower() == 'انهاء':
        bot.send_message(m.chat.id, "تم إنهاء المحادثة. اكتب /start للبدء من جديد.")
        return
    g = ask_gpt(m.text)
    bot.send_message(m.chat.id, g)
    bot.register_next_step_handler(m, handle_conversation)

bot.infinity_polling()
