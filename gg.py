import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

ASKING_API, MANAGING_APPS, ASKING_APP_FOR_SELF_DELETE, SCHEDULING_DELETE, CHECK_DELETE_TIME = range(5)

# حافظات للمهام المجدولة
self_delete_jobs = {}

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا بك في بوت التحكم في تطبيقات Heroku. للبدء، أرسل لي API الخاص بك.")
    return ASKING_API

def ask_api(update: Update, context: CallbackContext) -> int:
    api_token = update.message.text.strip()
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        context.user_data['api_token'] = api_token
        update.message.reply_text("تم استلام API بنجاح! جاري جلب التطبيقات...")
        return manage_apps(update, context)
    else:
        update.message.reply_text("API غير صالح. يرجى التحقق من صحته وإعادة المحاولة.")
        return ASKING_API

def manage_apps(update: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        keyboard = [[InlineKeyboardButton(app['name'], callback_data=f'self_delete_{app["name"]}')] for app in apps]
        keyboard.append([InlineKeyboardButton("عرض الوقت المتبقي للحذف الذاتي", callback_data='check_delete_time')])
        keyboard.append([InlineKeyboardButton("تسجيل خروج", callback_data='logout')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر التطبيق للحذف الذاتي أو عرض الوقت المتبقي أو تسجيل الخروج:", reply_markup=reply_markup)
        return MANAGING_APPS
    else:
        update.message.reply_text("حدث خطأ في جلب التطبيقات.")
        return ASKING_API

def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data.startswith('self_delete_'):
        app_name = query.data.split('_')[2]
        context.user_data['app_to_delete'] = app_name
        return ask_delete_time(update, context, app_name)
    
    elif query.data == 'check_delete_time':
        return check_delete_time(update, context)
    
    elif query.data == 'logout':
        context.user_data.clear()
        query.edit_message_text("تم تسجيل الخروج. أرسل API جديد للبدء.")
        return ASKING_API
    
    elif query.data == 'back':
        return manage_apps(update, context)

def ask_delete_time(update: Update, context: CallbackContext, app_name: str) -> int:
    keyboard = [
        [InlineKeyboardButton("🕒 بعد ساعة", callback_data='delete_1_hour')],
        [InlineKeyboardButton("🕒 بعد يوم", callback_data='delete_1_day')],
        [InlineKeyboardButton("🕒 بعد 25 دقيقة", callback_data='delete_25_minutes')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(f"اختر وقت الحذف لتطبيق {app_name}:", reply_markup=reply_markup)
    return SCHEDULING_DELETE

def schedule_delete(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    api_token = context.user_data.get('api_token')
    app_name = context.user_data.get('app_to_delete')
    time_option = query.data

    if time_option == 'delete_1_hour':
        delay = 3600
    elif time_option == 'delete_1_day':
        delay = 86400
    elif time_option == 'delete_25_minutes':
        delay = 1500

    delete_time = time.time() + delay
    self_delete_jobs[app_name] = (delete_time, context.job_queue.run_once(delete_app, delay, context=(api_token, app_name, query.message.chat_id)))
    
    query.edit_message_text(f"⏰ سيتم حذف التطبيق {app_name} بعد الوقت المحدد.")
    
    return manage_apps(update, context)

def delete_app(context: CallbackContext) -> None:
    job = context.job
    api_token, app_name, chat_id = job.context
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'https://api.heroku.com/apps/{app_name}', headers=headers)

    if response.status_code == 202:
        context.bot.send_message(chat_id=chat_id, text=f"✅ تم حذف التطبيق {app_name}.")
    else:
        context.bot.send_message(chat_id=chat_id, text=f"❌ حدث خطأ أثناء حذف التطبيق {app_name}.")
    
    if app_name in self_delete_jobs:
        del self_delete_jobs[app_name]

def check_delete_time(update: Update, context: CallbackContext) -> int:
    message = "🕒 الأوقات المتبقية للتطبيقات في الحذف الذاتي:\n"
    for app_name, (delete_time, job) in self_delete_jobs.items():
        remaining_time = delete_time - time.time()
        if remaining_time > 0:
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            message += f"📱 {app_name}: {int(hours)} ساعة, {int(minutes)} دقيقة, {int(seconds)} ثانية\n"
        else:
            message += f"📱 {app_name}: يتم الحذف الآن.\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    return MANAGING_APPS

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('تم إنهاء الجلسة.')
    return ConversationHandler.END

def main():
    TOKEN = '7031770762:AAEKh2HzaEn-mUm6YkqGm6qZA2JRJGOUQ20'
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING_API: [MessageHandler(Filters.text & ~Filters.command, ask_api)],
            MANAGING_APPS: [CallbackQueryHandler(button)],
            SCHEDULING_DELETE: [CallbackQueryHandler(schedule_delete)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
