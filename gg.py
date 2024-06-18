import requests
import telebot
from telebot.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mak

def info(user):
    headers = {
        'referer': 'https://storiesig.info/en/',
    }
    
    response = requests.get(f'https://storiesig.info/api/ig/profile/{user}', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        id = data['result']['id']
        user = data['result']['username']
        bio = data['result']['biography']
        name = data['result']['full_name']
        mn = data['result']['edge_owner_to_timeline_media']['count']
        followed = data['result']['edge_followed_by']['count']
        follow = data['result']['edge_follow']['count']
        img = data['result']['profile_pic_url']
        private = data['result']['is_private']
        
        if private == False:
            private = "عام"
        else:
            private = "خاص"
        ok = f'الايدي : {id}\nاليوزر : {user}\nالاسم : {name}\nالبايو : {bio}\nعدد المنشورات : {mn}\nعدد المتابعين : {followed}\nعدد ليتابعهم : {follow}\nحالة الحساب : {private}'
        return ok, img
    else:
        return None, None
        

token = "6419562305:AAHioiCY3MewQREnsxAKczTI7HJVt1MuseI"
bot = telebot.TeleBot(token, num_threads=30, skip_pending=True)

@bot.message_handler(commands=["start"])
def Welcome(msg):
	name = f"[{msg.from_user.first_name}](tg://settings)"
	bot.reply_to(msg,f'مرحبا {name} في بوت معلومات الحساب على الانستقرام فقط ارسل اليوزر بدون @ او مع .',parse_mode="markdown",reply_markup=Mak().add(Btn('More Bots',url="ttxxxn.t.me")))

@bot.message_handler(content_types=['text'])
def Info(m):
    user = m.text.replace("@","")
    inf, img_url = info(user)
    
    if inf is not None:
        bot.send_photo(m.chat.id, img_url, caption=inf, reply_to_message_id=m.message_id, reply_markup=Mak().add(Btn('مشاركة', switch_inline_query=user)))
    else:
        bot.reply_to(m,"user not found")

@bot.inline_handler(lambda query:True)
def inline_query(query):
    user = query.query
    inf, img_url = info(user)

    us = bot.get_me().username
    results = [
        telebot.types.InlineQueryResultPhoto(
            id='1',
            photo_url=img_url,
            thumb_url=img_url,
            caption=inf, 
            reply_markup=Mak().add(Btn('معلومات حسابك', url=f'{us}.t.me'))
        )
    ]

    bot.answer_inline_query(query.id, results=results)

bot.infinity_polling()
