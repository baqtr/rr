import requests
import telebot
from telebot.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mak
import json

# Function to get Instagram profile information
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
        ok = f'🆔: {id}\n👤: {user}\n📛: {name}\n📄: {bio}\n📷: {mn}\n👥: {followed}\n🔄: {follow}\n🔒: {private}'
        return ok, img
    else:
        return None, None

# Token and bot initialization
token = "6419562305:AAHioiCY3MewQREnsxAKczTI7HJVt1MuseI"
bot = telebot.TeleBot(token, num_threads=30, skip_pending=True)

# Initialize favorites dictionary
favorites = {}

# Welcome message handler
@bot.message_handler(commands=["start"])
def Welcome(msg):
    name = f"[{msg.from_user.first_name}](tg://settings)"
    markup = Mak().add(
        Btn('البحث الأكثر 🔍', callback_data='most_searched'),
        Btn('المفضلة ❤️', callback_data='show_favorites'),
        Btn('More Bots 🤖', url="ttxxxn.t.me")
    )
    bot.reply_to(msg, f'مرحبا {name} في بوت معلومات الحساب على الانستقرام فقط ارسل اليوزر بدون @ او مع .', parse_mode="markdown", reply_markup=markup)

# Handler for text messages
@bot.message_handler(content_types=['text'])
def Info(m):
    user = m.text.replace("@", "")
    inf, img_url = info(user)
    
    if inf is not None:
        markup = Mak().add(
            Btn('مشاركة 🔗', switch_inline_query=user),
            Btn('إضافة إلى المفضلة ❤️', callback_data=f'add_fav:{user}')
        )
        bot.send_photo(m.chat.id, img_url, caption=inf, reply_to_message_id=m.message_id, reply_markup=markup)
    else:
        bot.reply_to(m, "❌ المستخدم غير موجود")

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith('add_fav:'):
        user = call.data.split(':')[1]
        if call.from_user.id not in favorites:
            favorites[call.from_user.id] = []
        if user not in favorites[call.from_user.id]:
            favorites[call.from_user.id].append(user)
            bot.answer_callback_query(call.id, "✅ تمت الإضافة إلى المفضلة!")
        else:
            bot.answer_callback_query(call.id, "⚠️ المستخدم موجود في المفضلة بالفعل!")
    
    elif call.data.startswith('remove_fav:'):
        user = call.data.split(':')[1]
        if call.from_user.id in favorites and user in favorites[call.from_user.id]:
            favorites[call.from_user.id].remove(user)
            bot.answer_callback_query(call.id, "❌ تمت الإزالة من المفضلة!")
    
    elif call.data == 'show_favorites':
        if call.from_user.id in favorites and favorites[call.from_user.id]:
            markup = Mak()
            for fav_user in favorites[call.from_user.id]:
                markup.add(Btn(fav_user, callback_data=f'show_fav_info:{fav_user}'))
            markup.add(Btn('🔙 رجوع', callback_data='back'))
            bot.send_message(call.message.chat.id, "❤️ المفضلة:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "❌ لا يوجد مستخدمون في المفضلة!")

    elif call.data.startswith('show_fav_info:'):
        user = call.data.split(':')[1]
        inf, img_url = info(user)
        if inf is not None:
            markup = Mak().add(
                Btn('❌ إزالة من المفضلة', callback_data=f'remove_fav:{user}'),
                Btn('🔙 رجوع', callback_data='show_favorites')
            )
            bot.send_photo(call.message.chat.id, img_url, caption=inf, reply_markup=markup)
    
    elif call.data == 'most_searched':
        # Dummy implementation for most searched feature
        bot.send_message(call.message.chat.id, "📈 الأكثر بحثا: \n1. user1\n2. user2\n3. user3")
    
    elif call.data == 'back':
        bot.delete_message(call.message.chat.id, call.message.message_id)

# Inline query handler
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
            reply_markup=Mak().add(
                Btn('معلومات حسابك 📋', url=f'{us}.t.me'),
                Btn('إضافة إلى المفضلة ❤️', callback_data=f'add_fav:{user}')
            )
        )
    ]

    bot.answer_inline_query(query.id, results=results)

# Polling
bot.infinity_polling()
