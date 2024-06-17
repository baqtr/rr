import requests
import telebot
from telebot.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mak

def get_profile_info(user):
    headers = {
        'referer': 'https://storiesig.info/en/',
    }
    
    response = requests.get(f'https://storiesig.info/api/ig/profile/{user}', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        profile_info = {
            'id': data['result']['id'],
            'username': data['result']['username'],
            'biography': data['result']['biography'],
            'full_name': data['result']['full_name'],
            'media_count': data['result']['edge_owner_to_timeline_media']['count'],
            'followers_count': data['result']['edge_followed_by']['count'],
            'following_count': data['result']['edge_follow']['count'],
            'profile_pic_url': data['result']['profile_pic_url'],
            'is_private': data['result']['is_private'],
        }
        
        profile_info['status'] = 'عام' if not profile_info['is_private'] else 'خاص'
        
        return profile_info
    else:
        return None

def get_followers_list(user):
    headers = {
        'referer': 'https://storiesig.info/en/',
    }
    
    response = requests.get(f'https://storiesig.info/api/ig/followers/{user}', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['result']
    else:
        return None

token = "6419562305:AAHioiCY3MewQREnsxAKczTI7HJVt1MuseI"
bot = telebot.TeleBot(token, num_threads=30, skip_pending=True)

@bot.message_handler(commands=["start"])
def Welcome(msg):
    name = f"[{msg.from_user.first_name}](tg://settings)"
    welcome_message = (f"مرحبا {name} في بوت معلومات الحساب على الانستقرام. "
                       "فقط ارسل اليوزر بدون @ او مع .", 
                       parse_mode="markdown",
                       reply_markup=Mak().add(Btn('بحث عن حساب', callback_data='search')))
    bot.reply_to(msg, welcome_message)

@bot.callback_query_handler(func=lambda call: call.data == 'search')
def prompt_for_username(call):
    msg = bot.send_message(call.message.chat.id, "الرجاء إرسال اليوزر بدون @ أو مع .")
    bot.register_next_step_handler(msg, process_username)

def process_username(message):
    user = message.text.replace("@", "")
    profile_info = get_profile_info(user)
    
    if profile_info is not None:
        inf = (f"الايدي : {profile_info['id']}\n"
               f"اليوزر : {profile_info['username']}\n"
               f"الاسم : {profile_info['full_name']}\n"
               f"البايو : {profile_info['biography']}\n"
               f"عدد المنشورات : {profile_info['media_count']}\n"
               f"عدد المتابعين : {profile_info['followers_count']}\n"
               f"عدد ليتابعهم : {profile_info['following_count']}\n"
               f"حالة الحساب : {profile_info['status']}")
        
        bot.send_photo(message.chat.id, profile_info['profile_pic_url'], caption=inf, reply_to_message_id=message.message_id, reply_markup=Mak().add(
            Btn('مشاركة', switch_inline_query=user),
            Btn('عرض المتابعين', callback_data=f'followers:{user}')
        ))
    else:
        bot.reply_to(message, "لم يتم العثور على المستخدم")

@bot.callback_query_handler(func=lambda call: call.data.startswith('followers:'))
def show_followers(call):
    user = call.data.split(":")[1]
    followers = get_followers_list(user)
    
    if followers:
        followers_list = []
        for follower in followers:
            followers_list.append([
                Btn(follower['username'], url=f"https://instagram.com/{follower['username']}"),
                Btn("التالي", callback_data=f'next_follower:{user}:{follower["username"]}')
            ])
        bot.send_message(call.message.chat.id, "المتابعين:", reply_markup=Mak(inline_keyboard=followers_list))
    else:
        bot.send_message(call.message.chat.id, "لم يتم العثور على المتابعين")

@bot.callback_query_handler(func=lambda call: call.data.startswith('next_follower:'))
def next_follower(call):
    data = call.data.split(":")
    user = data[1]
    current_follower = data[2]
    
    followers = get_followers_list(user)
    if followers:
        for i, follower in enumerate(followers):
            if follower['username'] == current_follower:
                next_index = (i + 1) % len(followers)
                next_follower = followers[next_index]
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="المتابعين:", reply_markup=Mak().add(
                    Btn(next_follower['username'], url=f"https://instagram.com/{next_follower['username']}"),
                    Btn("التالي", callback_data=f'next_follower:{user}:{next_follower["username"]}')
                ))
                break

@bot.inline_handler(lambda query: True)
def inline_query(query):
    user = query.query
    profile_info = get_profile_info(user)

    if profile_info:
        inf = (f"الايدي : {profile_info['id']}\n"
               f"اليوزر : {profile_info['username']}\n"
               f"الاسم : {profile_info['full_name']}\n"
               f"البايو : {profile_info['biography']}\n"
               f"عدد المنشورات : {profile_info['media_count']}\n"
               f"عدد المتابعين : {profile_info['followers_count']}\n"
               f"عدد ليتابعهم : {profile_info['following_count']}\n"
               f"حالة الحساب : {profile_info['status']}")
        
        results = [
            telebot.types.InlineQueryResultPhoto(
                id='1',
                photo_url=profile_info['profile_pic_url'],
                thumb_url=profile_info['profile_pic_url'],
                caption=inf, 
                reply_markup=Mak().add(Btn('معلومات حسابك', url=f't.me/{bot.get_me().username}'))
            )
        ]
        bot.answer_inline_query(query.id, results=results)

bot.infinity_polling()
