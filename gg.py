import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

# Constants for conversation states
ASKING_API, MANAGING_APPS, ASKING_APP_FOR_MAINTENANCE, ASKING_APP_FOR_SELF_DELETE, SCHEDULING_DELETE, CHOOSING_DISPLAY_STYLE = range(6)

# Start function to initiate the conversation
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا بك في بوت المساعد لحذف التطبيقات من Heroku. للبدء، أرسل لي API الخاص بك.")
    return ASKING_API

# Function to ask for the API token
def ask_api(update: Update, context: CallbackContext) -> int:
    api_token = update.message.text
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        context.user_data['api_token'] = api_token
        update.message.reply_text("تم استقبال API بنجاح! جاري جلب التطبيقات...")
        return manage_apps(update, context)
    else:
        update.message.reply_text("API غير صالح. تأكد من صحته وأعد إرساله.")
        return ASKING_API

# Function to manage apps
def manage_apps(update: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        keyboard = [[InlineKeyboardButton(app['name'], callback_data=f'choose_{app["name"]}') for app in apps]]
        keyboard.append([InlineKeyboardButton("وضع الصيانة", callback_data='maintenance')])
        keyboard.append([InlineKeyboardButton("الحذف الذاتي", callback_data='self_delete')])
        keyboard.append([InlineKeyboardButton("تبديل API", callback_data='toggle_api')])
        keyboard.append([InlineKeyboardButton("ℹ️ معلومات", callback_data='info')])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر التطبيق لإدارته أو اختيار الخيارات الأخرى:", reply_markup=reply_markup)
        return MANAGING_APPS
    else:
        update.message.reply_text("حدث خطأ في جلب التطبيقات.")
        return ASKING_API

# Function to handle button clicks
def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'maintenance':
        query.edit_message_text("اختر التطبيق لوضعه في وضع الصيانة:", reply_markup=get_apps_buttons(context, 'set_maintenance'))
        return ASKING_APP_FOR_MAINTENANCE
    elif query.data == 'self_delete':
        query.edit_message_text("اختر التطبيق لحذفه ذاتياً:", reply_markup=get_apps_buttons(context, 'delete_self'))
        return ASKING_APP_FOR_SELF_DELETE
    elif query.data == 'toggle_api':
        return toggle_api(update, context)
    elif query.data == 'info':
        return info(update, context)
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

# Function to toggle API
def toggle_api(update: Update, context: CallbackContext) -> int:
    api_enabled = context.user_data.get('api_enabled', False)
    context.user_data['api_enabled'] = not api_enabled

    if api_enabled:
        update.callback_query.edit_message_text("API تم تعطيل.")
    else:
        update.callback_query.edit_message_text("API تم تمكينه.")

    return MANAGING_APPS

# Function to display information
def info(update: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/account', headers=headers)
    account_info = response.json()

    total_apps = account_info.get('quota_used', 0)
    maintenance_apps = account_info.get('apps_in_maintenance', 0)
    scheduled_deletion_apps = account_info.get('scheduled_deletion_apps', 0)

    message = f"عدد التطبيقات الكلي: {total_apps}\n"
    message += f"عدد التطبيقات في وضع الصيانة: {maintenance_apps}\n"
    message += f"عدد التطبيقات في الحذف الذاتي: {scheduled_deletion_apps}\n"

    update.callback_query.edit_message_text(message)

    return MANAGING_APPS

# Function to create inline keyboard buttons for apps
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

# Function to create inline keyboard buttons for delete time options
def get_delete_time_buttons() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("بعد ساعة", callback_data='delete_1_hour')],
        [InlineKeyboardButton("بعد يوم", callback_data='delete_1_day')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to set maintenance mode for an app
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

# Function to unset maintenance mode for an app
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

# Function to schedule app deletion
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

    query.edit_message_text(f"سيتم حذف التطبيق {app_name} بعد {time_option}.")
    
    context.job_queue.run_once(delete_app, delay, context=(api_token, app_name, query.message.chat_id))
    
    return manage_apps(update, context)

# Function to delete an app
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

# Function to cancel the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('تم إنهاء الجلسة.')
    return ConversationHandler.END

# Main function to run the bot
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
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
