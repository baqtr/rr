import requests
import telebot
from telebot.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mak
from collections import defaultdict

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
        ok = f'🔹 الايدي : {id}\n🔹 اليوزر : {user}\n🔹 الاسم : {name}\n🔹 البايو : {bio}\n🔹 عدد المنشورات : {mn}\n🔹 عدد المتابعين : {followed}\n🔹 عدد الذين يتابعهم : {follow}\n🔹 حالة الحساب : {private}'
        return ok, img
    else:
        return None, None

token = "6419562305:AAHioiCY3MewQREnsxAKczTI7HJVt1MuseI"
bot = telebot.TeleBot(token, num_threads=30, skip_pending=True)

user_favorites = defaultdict(list)  # to store favorite users for each user

@bot.message_handler(commands=["start"])
def Welcome(msg):
    name = f"[{msg.from_user.first_name}](tg://settings)"
    markup = Mak()
    markup.add(Btn('🤖 بوتات أكثر', url="ttxxxn.t.me"))
    markup.add(Btn('🔍 الأكثر بحثا', callback_data='most_searched'))
    markup.add(Btn('⭐ المفضلة', callback_data='favorites'))
    bot.reply_to(msg, f'مرحبا {name} في بوت معلومات الحساب على الانستقرام 🌟\nفقط ارسل اليوزر بدون @ او مع .', parse_mode="markdown", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def Info(m):
    user = m.text.replace("@", "")
    inf, img_url = info(user)
    
    if inf is not None:
        markup = Mak()
        markup.add(Btn('🔗 مشاركة', switch_inline_query=user))
        markup.add(Btn('⭐ إضافة إلى المفضلة', callback_data=f'add_favorite_{user}'))
        bot.send_photo(m.chat.id, img_url, caption=inf, reply_to_message_id=m.message_id, reply_markup=markup)
    else:
        bot.reply_to(m, "⚠️ المستخدم غير موجود")

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_favorite_'))
def add_to_favorites(call):
    user = call.data.split('_')[-1]
    user_favorites[call.from_user.id].append(user)
    bot.answer_callback_query(call.id, "تمت الإضافة إلى المفضلة! ⭐")

@bot.callback_query_handler(func=lambda call: call.data == 'favorites')
def show_favorites(call):
    favs = user_favorites[call.from_user.id]
    if favs:
        markup = Mak()
        for user in favs:
            markup.add(Btn(user, callback_data=f'view_favorite_{user}'))
        markup.add(Btn('🔙 رجوع', callback_data='back_to_main'))
        bot.send_message(call.message.chat.id, "⭐ المفضلة:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "⚠️ لا توجد حسابات في المفضلة.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_favorite_'))
def view_favorite(call):
    user = call.data.split('_')[-1]
    inf, img_url = info(user)
    if inf is not None:
        markup = Mak()
        markup.add(Btn('❌ إزالة من المفضلة', callback_data=f'remove_favorite_{user}'))
        markup.add(Btn('🔙 رجوع', callback_data='favorites'))
        bot.send_photo(call.message.chat.id, img_url, caption=inf, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_favorite_'))
def remove_favorite(call):
    user = call.data.split('_')[-1]
    user_favorites[call.from_user.id].remove(user)
    bot.answer_callback_query(call.id, "تمت الإزالة من المفضلة! ❌")
    show_favorites(call)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main(call):
    Welcome(call.message)

@bot.inline_handler(lambda query: True)
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
            reply_markup=Mak().add(Btn('معلومات حسابك 📱', url=f'{us}.t.me'))
        )
    ]

    bot.answer_inline_query(query.id, results=results)

bot.infinity_polling()
