import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

ASKING_API, MANAGING_APPS, ASKING_APP_FOR_MAINTENANCE, ASKING_APP_FOR_SELF_DELETE, SCHEDULING_DELETE, SYNC_DYNO, ASKING_DYNO_COUNT = range(7)

# حافظات للمهام المجدولة
self_delete_jobs = {}

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا بك في بوت المساعد لإدارة التطبيقات على Heroku. للبدء، أرسل لي API الخاص بك.")
    return ASKING_API

def ask_api(update: Update, context: CallbackContext) -> int:
    api_token = update.message.text
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        context.user_data['api_token'] = api_token
        update.message.reply_text("✅ تم استقبال API بنجاح! جاري جلب التطبيقات...")
        return manage_apps(update, context)
    else:
        update.message.reply_text("❌ API غير صالح. تأكد من صحته وأعد إرساله.")
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
        keyboard = [[InlineKeyboardButton(f"📱 {app['name']}", callback_data=f'choose_{app["name"]}')] for app in apps]
        keyboard.append([InlineKeyboardButton("🔧 وضع الصيانة", callback_data='maintenance')])
        keyboard.append([InlineKeyboardButton("🚫 إلغاء وضع الصيانة", callback_data='cancel_maintenance')])
        keyboard.append([InlineKeyboardButton("🗑 الحذف الذاتي", callback_data='self_delete')])
        keyboard.append([InlineKeyboardButton("⏰ الوقت المتبقي للحذف الذاتي", callback_data='check_delete_time')])
        keyboard.append([InlineKeyboardButton("🔄 مزامنة الدينامو", callback_data='sync_dyno')])
        keyboard.append([InlineKeyboardButton("ℹ️ عرض المعلومات", callback_data='show_info')])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر التطبيق لإدارته أو اختيار الخيارات الأخرى:", reply_markup=reply_markup)
        return MANAGING_APPS
    else:
        update.message.reply_text("❌ حدث خطأ في جلب التطبيقات.")
        return ASKING_API

def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'maintenance':
        query.edit_message_text("اختر التطبيق لوضعه في وضع الصيانة:", reply_markup=get_apps_buttons(context, 'set_maintenance'))
        return ASKING_APP_FOR_MAINTENANCE
    elif query.data == 'cancel_maintenance':
        query.edit_message_text("اختر التطبيق لإلغاء وضع الصيانة:", reply_markup=get_apps_buttons(context, 'unset_maintenance'))
        return ASKING_APP_FOR_MAINTENANCE
    elif query.data == 'self_delete':
        query.edit_message_text("اختر التطبيق لحذفه ذاتياً:", reply_markup=get_apps_buttons(context, 'delete_self'))
        return ASKING_APP_FOR_SELF_DELETE
    elif query.data == 'check_delete_time':
        return check_delete_time(update, context)
    elif query.data == 'show_info':
        return show_info(update, context)
    elif query.data == 'sync_dyno':
        query.edit_message_text("أدخل عدد الدينامو المطلوب (الحد الأقصى 100):")
        return ASKING_DYNO_COUNT
    elif query.data.startswith('set_maintenance_'):
        app_name = query.data.split('_')[2]
        return set_maintenance(update, context, app_name)
    elif query.data.startswith('unset_maintenance_'):
        app_name = query.data.split('_')[2]
        return unset_maintenance(update, context, app_name)
    elif query.data.startswith('delete_self_'):
        app_name = query.data.split('_')[2]
        context.user_data['app_to_delete'] = app_name
        query.edit_message_text("اختر وقت الحذف:", reply_markup=get_delete_time_buttons())
        return SCHEDULING_DELETE
    elif query.data.startswith('delete_'):
        return schedule_delete(update, context)
    elif query.data == 'back':
        return manage_apps(update, context)

def get_apps_buttons(context: CallbackContext, action: str) -> InlineKeyboardMarkup:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    apps = response.json()
    keyboard = [[InlineKeyboardButton(f"📱 {app['name']}", callback_data=f'{action}_{app["name"]}')] for app in apps]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back')])
    return InlineKeyboardMarkup(keyboard)

def get_delete_time_buttons() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🕒 بعد ساعة", callback_data='delete_1_hour')],
        [InlineKeyboardButton("🕒 بعد يوم", callback_data='delete_1_day')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def set_maintenance(update: Update, context: CallbackContext, app_name: str) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3',
        'Content-Type': 'application/json'
    }
    data = {'maintenance': True}
    response = requests.patch(f'https://api.heroku.com/apps/{app_name}', headers=headers, json=data)

    if response.status_code == 200:
        update.callback_query.edit_message_text(f"✅ تم وضع التطبيق {app_name} في وضع الصيانة.")
    else:
        update.callback_query.edit_message_text(f"❌ حدث خطأ أثناء وضع التطبيق {app_name} في وضع الصيانة.")
    
    return manage_apps(update, context)

def unset_maintenance(update: Update, context: CallbackContext, app_name: str) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3',
        'Content-Type': 'application/json'
    }
    data = {'maintenance': False}
    response = requests.patch(f'https://api.heroku.com/apps/{app_name}', headers=headers, json=data)

    if response.status_code == 200:
        update.callback_query.edit_message_text(f"✅ تم إلغاء وضع الصيانة للتطبيق {app_name}.")
    else:
        update.callback_query.edit_message_text(f"❌ حدث خطأ أثناء إلغاء وضع الصيانة للتطبيق {app_name}.")
    
    return manage_apps(update, context)

def schedule_delete(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    api_token = context.user_data.get('api_token')
    app_name = context.user_data.get('app_to_delete')
    time_option = query.data

    if time_option == 'delete_1_hour':
        delay = 3600
        delay_text = "ساعة"
    elif time_option == 'delete_1_day':
        delay = 86400
        delay_text = "يوم"

    # تسجيل وقت الحذف
    delete_time = time.time() + delay
    self_delete_jobs[app_name] = (delete_time, context.job_queue.run_once(delete_app, delay, context=(api_token, app_name, query.message.chat_id)))
    
    query.edit_message_text(f"⏰ سيتم حذف التطبيق {app_name} بعد {delay_text}.")
    
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
    
    # إزالة التطبيق من قائمةالحذف الذاتي
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

    update.callback_query.edit_message_text(message)
    return manage_apps(update, context)

def show_info(update: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    if response.status_code == 200:
        apps = response.json()
        total_apps = len(apps)
        maintenance_apps = sum(1 for app in apps if app['maintenance'])
        self_delete_apps = len(self_delete_jobs)

        message = (
            f"ℹ️ معلومات الحساب:\n"
            f"📊 عدد التطبيقات الكلي: {total_apps}\n"
            f"🔧 عدد التطبيقات في وضع الصيانة: {maintenance_apps}\n"
            f"🗑 عدد التطبيقات في الحذف الذاتي: {self_delete_apps}\n"
        )
        update.callback_query.edit_message_text(message)
    else:
        update.callback_query.edit_message_text("❌ حدث خطأ في جلب المعلومات.")
    return manage_apps(update, context)

def ask_dyno_count(update: Update, context: CallbackContext) -> int:
    dyno_count = int(update.message.text)
    if dyno_count < 1 or dyno_count > 100:
        update.message.reply_text("❌ الرجاء إدخال عدد صحيح بين 1 و 100.")
        return ASKING_DYNO_COUNT
    else:
        return sync_dyno(update, context, dyno_count)

def sync_dyno(update: Update, context: CallbackContext, dyno_count: int) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3',
        'Content-Type': 'application/json'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    apps = response.json()

    for app in apps:
        app_name = app['name']
        data = {'quantity': dyno_count}
        requests.patch(f'https://api.heroku.com/apps/{app_name}/formation/web', headers=headers, json=data)
    
    update.message.reply_text(f"🔄 تم مزامنة جميع التطبيقات ليكون لديهم {dyno_count} دينامو.")
    return manage_apps(update, context)

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
            ASKING_APP_FOR_MAINTENANCE: [CallbackQueryHandler(button)],
            ASKING_APP_FOR_SELF_DELETE: [CallbackQueryHandler(button)],
            SCHEDULING_DELETE: [CallbackQueryHandler(schedule_delete)],
            ASKING_DYNO_COUNT: [MessageHandler(Filters.text & ~Filters.command, ask_dyno_count)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
