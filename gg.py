import os
import logging
import zipfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext) -> None:
    welcome_message = "يرجاء ارسال ملف php او Python لنبدا يمكنك 🪯\n\n"
    welcome_message += "ذا كنت لاتعرف كيف تستخدم البوت فاضغط على زر شرح البوت ✅"
    
    # Custom emojis
    emoji_link = u'\U0001F517'
    emoji_help = u'\U00002753'
    
    keyboard = [
        [InlineKeyboardButton("المطور موهان ♾️", url="https://t.me/XX44g")],
        [InlineKeyboardButton("شرح البوت ❓❓", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def receive_file(update: Update, context: CallbackContext) -> None:
    file = context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    file_extension = os.path.splitext(file_name)[1]
    file.download(file_name)
    
    if file_extension == '.php':
        os.rename(file_name, 'index.php')
        zip_file_name = 'index_php.zip'
        with zipfile.ZipFile(zip_file_name, "w") as zipf:
            zipf.write('index.php')
        
        # Generate link for file conversion
        conversion_link = f"https://t.me/SERSA1BOT?start=convert_{zip_file_name}"
        
        keyboard = [[InlineKeyboardButton("بوت جيتهاب ✅", url=conversion_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_document(update.effective_chat.id, document=open(zip_file_name, 'rb'), filename=zip_file_name, caption="تم ضغط الملف ووضع جميع المتطلبات قم بتحويله لبوت جيتهاب الان", reply_markup=reply_markup)
        os.remove('index.php')
        os.remove(zip_file_name)
    elif file_extension == '.py':
        os.rename(file_name, 'main.py')
        zip_file_name = 'main_py.zip'
        # Create requirements.txt content
        requirements_content = """APScheduler==3.6.3
cachetools==4.2.2
certifi==2022.6.15
charset-normalizer==2.1.0
click==8.1.3
docopt==0.6.2
fast-proxy-list==0.0.2
idna==3.3
Flask==2.1.2
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.1
pipreqs==0.4.11
pyTelegramBotAPI==4.6.0
python-telegram-bot==13.3
Pytz==2022.1
pytz-deprecation-shim==0.1
requests==2.28.1
six==1.16.0
telebot==0.0.4
tzdata==2022.1
tornado==6.1
tzlocal==4.2
Werkzeug==2.1.2
yarg==0.1.9
uuid==1.30
user-agent==0.1.10
urllib3==1.26.9
pyperclip==1.8.2
beautifulsoup4==4.10.0
websocket-client==1.2.1
autopep8==1.5.7
pyrogram==2.0.106
kvsqlite==0.2.1
schedule==1.1.0
psutil==5.8.0
PyGithub"""
        # Write requirements.txt
        with open("requirements.txt", 'w') as req_file:
            req_file.write(requirements_content)
        # Write Procfile
        with open("Procfile", 'w') as proc_file:
            proc_file.write("bot: python main.py")
            
        with zipfile.ZipFile(zip_file_name, "w") as zipf:
            zipf.write('main.py')
            zipf.write("requirements.txt")
            zipf.write("Procfile")
        
        # Generate link for file conversion
        conversion_link = f"https://t.me/SERSA1BOT?start=convert_{zip_file_name}"
        
        keyboard = [[InlineKeyboardButton("بوت جيتهاب ♾️", url=conversion_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_document(update.effective_chat.id, document=open(zip_file_name, 'rb'), filename=zip_file_name, caption="تم وبنجاح قم الان بتحويل الملف لبوت جيتهاب ✅", reply_markup=reply_markup)

        os.remove('main.py')
        os.remove("requirements.txt")
        os.remove("Procfile")
        os.remove(zip_file_name)
    else:
        update.message.reply_text("يزي بيزي اليك الخطوات1️⃣: قبل ارسال الملف تاكد من وضع التوكن والايدي2️⃣: ارسال ملف بايثون او بي اتش بي فقط3️⃣: بعده ان يقوم البوت برسال ملف مضغوط اليك قم مباشره برساله الى بوت جيتهاب @SERSA1BOT")
        return

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == "help":
        query.message.reply_text("يزي بيزي اليك الخطوات1️⃣: قبل ارسال الملف تاكد من وضع التوكن والايدي2️⃣: ارسال ملف بايثون او بي اتش بي فقط3️⃣: بعده ان يقوم البوت برسال ملف مضغوط اليك قم مباشره برساله الى بوت جيتهاب @SERSA1BOT")

def main() -> None:
    TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, receive_file))
    dp.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
