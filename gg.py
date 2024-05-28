from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

ASKING_API, MANAGING_APPS, ASKING_APP_FOR_MAINTENANCE, ASKING_APP_FOR_SELF_DELETE, SCHEDULING_DELETE, SHOW_REMAINING_TIME, ASKING_NEW_API = range(7)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا بك في بوت المساعد لحذف التطبيقات من Heroku. للبدء، أرسل لي API الخاص بك.")
    return ASKING_API

def ask_api(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم استلام API بنجاح! يمكنك الآن إدارة التطبيقات.")
    return manage_apps(update, context)

def manage_apps(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("وضع الصيانة", callback_data='maintenance')],
        [InlineKeyboardButton("الحذف الذاتي", callback_data='self_delete')],
        [InlineKeyboardButton("عرض الوقت المتبقي للحذف الذاتي", callback_data='show_remaining_time')],
        [InlineKeyboardButton("تبديل API", callback_data='change_api')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر الخيار الذي تريده:", reply_markup=reply_markup)
    return MANAGING_APPS

def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'maintenance':
        query.edit_message_text("اختر التطبيق لوضعه في وضع الصيانة:", reply_markup=get_apps_buttons(context, 'set_maintenance'))
        return ASKING_APP_FOR_MAINTENANCE
    elif query.data == 'self_delete':
        query.edit_message_text("اختر التطبيق لحذفه ذاتيًا:", reply_markup=get_apps_buttons(context, 'delete_self'))
        return ASKING_APP_FOR_SELF_DELETE
    elif query.data == 'show_remaining_time':
        # Logic to show remaining time for self deletion
        return SHOW_REMAINING_TIME
    elif query.data == 'change_api':
        query.edit_message_text("أرسل لي API الجديد:")
        return ASKING_NEW_API
    elif query.data.startswith('set_maintenance_'):
        app_name = query.data.split('_')[2]
        return set_maintenance(update, context, app_name)
    elif query.data.startswith('delete_self_'):
        app_name = query.data.split('_')[2]
        context.user_data['app_to_delete'] = app_name
        query.edit_message_text("اختر وقت الحذف:", reply_markup=get_delete_time_buttons())
        return SCHEDULING_DELETE
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
    keyboard = [[InlineKeyboardButton(app['name'], callback_data=f'{action}_{app["name"]}') for app in apps]]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back')])
    return InlineKeyboardMarkup(keyboard)

def get_delete_time_buttons() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("بعد ساعة", callback_data='delete_1_hour')],
        [InlineKeyboardButton("بعد يوم", callback_data='delete_1_day')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def change_api(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("أرسل لي API الجديد:")
    return ASKING_NEW_API

def ask_new_api(update: Update, context: CallbackContext) -> int:
    api_token = update.message.text
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        context.user_data['api_token'] = api_token
        update.message.reply_text("تم استقبال API بنجاح! يمكنك الآن إدارة التطبيقات.")
        return manage_apps(update, context)
    else:
        update.message.reply_text("API غير صالح. تأكد من صحته وأعد إرساله.")
        return ASKING_NEW_API

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
            SHOW_REMAINING_TIME: [CallbackQueryHandler(button)],
            ASKING_NEW_API: [MessageHandler(Filters.text & ~Filters.command, ask_new_api)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
