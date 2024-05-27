import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# إعداد السجل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# وضع الـ API الخاص بتيليجرام
TELEGRAM_BOT_TOKEN = '6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE'

# تخزين بيانات المستخدمين
user_data = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 مرحباً! الرجاء إدخال Heroku API الخاص بك:")

def handle_api_key(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    api_key = update.message.text
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/account', headers=headers)

    if response.status_code == 200:
        user_data[user_id] = {'api_key': api_key}
        update.message.reply_text("✅ تم التحقق من الـ API بنجاح. يمكنك الآن التحكم بتطبيقاتك.",
                                  reply_markup=main_menu())
    else:
        update.message.reply_text("❌ الـ API غير صحيح. الرجاء إدخال API صالح:")

def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("عرض التطبيقات", callback_data='list_apps')],
        [InlineKeyboardButton("وضع الصيانة", callback_data='maintenance')],
        [InlineKeyboardButton("حذف ذاتي", callback_data='self_delete')]
    ]
    return InlineKeyboardMarkup(keyboard)

def list_apps(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    # التحقق من وجود الـ API في البيانات المخزنة
    if user_id not in user_data or 'api_key' not in user_data[user_id]:
        query.edit_message_text("❌ لم يتم إدخال API صالح. الرجاء إدخال API صالح.")
        return

    api_key = user_data[user_id]['api_key']
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    apps = response.json()

    if response.status_code == 200:
        if apps:
            keyboard = [[InlineKeyboardButton(app['name'], callback_data=f'copy_{app["name"]}') for app in apps]]
            query.edit_message_text("📦 التطبيقات الموجودة على حسابك:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("لا توجد تطبيقات على حسابك.", reply_markup=main_menu())
    else:
        query.edit_message_text("حدث خطأ أثناء جلب التطبيقات.", reply_markup=main_menu())

def copy_app_name(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    app_name = query.data.split('_', 1)[1]
    query.edit_message_text(f"📋 تم نسخ اسم التطبيق: `{app_name}`", parse_mode='Markdown')

def maintenance(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("الرجاء إدخال اسم التطبيق الذي ترغب في وضعه في وضع الصيانة:")

def handle_maintenance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # التحقق من وجود الـ API في البيانات المخزنة
    if user_id not in user_data or 'api_key' not in user_data[user_id]:
        update.message.reply_text("❌ لم يتم إدخال API صالح. الرجاء إدخال API صالح.")
        return

    app_name = update.message.text
    api_key = user_data[user_id]['api_key']
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3',
        'Content-Type': 'application/json'
    }
    data = {
        'maintenance': True
    }
    response = requests.patch(f'https://api.heroku.com/apps/{app_name}', headers=headers, json=data)

    if response.status_code == 200:
        update.message.reply_text(f"✅ تم وضع التطبيق {app_name} في وضع الصيانة.", reply_markup=main_menu())
    else:
        update.message.reply_text(f"❌ حدث خطأ أثناء وضع التطبيق {app_name} في وضع الصيانة. تأكد من اسم التطبيق وحاول مرة أخرى.", reply_markup=main_menu())

def self_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("الرجاء إدخال اسم التطبيق الذي ترغب في حذفه ذاتياً:")

def handle_self_delete(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # التحقق من وجود الـ API في البيانات المخزنة
    if user_id not in user_data or 'api_key' not in user_data[user_id]:
        update.message.reply_text("❌ لم يتم إدخال API صالح. الرجاء إدخال API صالح.")
        return

    app_name = update.message.text
    user_data[user_id]['app_to_delete'] = app_name

    keyboard = [
        [InlineKeyboardButton("بعد ساعة", callback_data='delete_1_hour')],
        [InlineKeyboardButton("بعد يوم", callback_data='delete_1_day')],
        [InlineKeyboardButton("بعد أسبوع", callback_data='delete_1_week')],
        [InlineKeyboardButton("وضع الصيانة", callback_data='maintenance_app')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر وقت الحذف:", reply_markup=reply_markup)

def schedule_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    # التحقق من وجود الـ API في البيانات المخزنة
    if user_id not in user_data or 'api_key' not in user_data[user_id]:
        query.edit_message_text("❌ لم يتم إدخال API صالح. الرجاء إدخال API صالح.")
        return

    api_key = user_data[user_id]['api_key']
    app_name = user_data[user_id]['app_to_delete']
    time_option = query.data

    if time_option == 'delete_1_hour':
        delay = 3600
    elif time_option == 'delete_1_day':
        delay = 86400
    elif time_option == 'delete_1_week':
        delay = 604800

    query.edit_message_text(f"سيتم حذف التطبيق {app_name} بعد {time_option}.")
    
    context.job_queue.run_once(delete_app, delay, context=(api_key, app_name, user_id))

def delete_app(context: CallbackContext) -> None:
    job = context.job
    api_key, app_name, user_id = job.context
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'https://api.heroku.com/apps/{app_name}', headers=headers)

    if response.status_code == 202:
        context.bot.send_message(chat_id=user_id, text=f"✅ تم حذف التطبيق {app_name}.")
    else:
        context.bot.send_message(chat_id=user_id, text=f"❌ حدث خطأ أثناء حذف التطبيق {app_name}.")

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_api_key))
    dp.add_handler(CallbackQueryHandler(list_apps, pattern='list_apps'))
    dp.add_handler(CallbackQueryHandler(copy_app_name, pattern=r'copy_'))
    dp.add_handler(CallbackQueryHandler(maintenance, pattern='maintenance'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_maintenance))
    dp.add_handler(CallbackQueryHandler(self_delete, pattern='self_delete'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_self_delete))
    dp.add_handler(CallbackQueryHandler(schedule_delete, pattern='delete_1_hour'))
    dp.add_handler(CallbackQueryHandler(schedule_delete, pattern='delete_1_day'))
    dp.add_handler(CallbackQueryHandler(schedule_delete, pattern='delete_1_week'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
