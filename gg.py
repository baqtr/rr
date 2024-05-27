import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

ASKING_API, MANAGING_APPS, ASKING_DELETE_TIME, ASKING_APP_FOR_MAINTENANCE, ASKING_APP_NAME_FOR_SELF_DELETE, CHOOSING_DISPLAY_STYLE = range(6)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا بك في بوت المساعد لحذف التطبيقات من Heroku. للبدء، أرسل لي API الخاص بك.")
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
        update.message.reply_text("تم استقبال API بنجاح! جاري جلب التطبيقات...")
        return manage_apps(update, context)
    else:
        update.message.reply_text("API غير صالح. تأكد من صحته وأعد إرساله.")
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
        keyboard = [[InlineKeyboardButton(app['name'], callback_data=f'delete_{app["id"]}') for app in apps]]
        keyboard.append([InlineKeyboardButton("حذف الكل", callback_data='delete_all')])
        keyboard.append([InlineKeyboardButton("تغيير ترتيب الأزرار", callback_data='change_display_style')])
        keyboard.append([InlineKeyboardButton("وضع الصيانة", callback_data='maintenance')])
        keyboard.append([InlineKeyboardButton("عرض تطبيقات الصيانة", callback_data='show_maintenance')])
        keyboard.append([InlineKeyboardButton("حذف ذاتي", callback_data='self_delete')])
        keyboard.append([InlineKeyboardButton("👨‍💻 مطور البوت", url='https://t.me/xx44g')])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر التطبيق لحذفه أو إدارة التطبيقات:", reply_markup=reply_markup)
        return MANAGING_APPS
    else:
        update.message.reply_text("حدث خطأ في جلب التطبيقات.")
        return ASKING_API

def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'change_display_style':
        return choose_display_style(update, context)
    elif query.data == 'delete_all':
        return delete_all_apps(query, context)
    elif query.data == 'maintenance':
        query.edit_message_text("الرجاء إدخال اسم التطبيق الذي ترغب في وضعه في وضع الصيانة:")
        return ASKING_APP_FOR_MAINTENANCE
    elif query.data == 'self_delete':
        query.edit_message_text("الرجاء إدخال اسم التطبيق الذي ترغب في حذفه ذاتياً:")
        return ASKING_APP_NAME_FOR_SELF_DELETE
    elif query.data == 'show_maintenance':
        return show_maintenance_apps(query, context)
    elif query.data == 'back':
        return manage_apps(update, context)
    elif query.data.startswith('delete_'):
        app_id = query.data.split('_')[1]
        return delete_app(update, context, app_id)

def choose_display_style(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("عمودي", callback_data='vertical_display')],
        [InlineKeyboardButton("أفقي", callback_data='horizontal_display')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text("اختر ترتيب الأزرار:", reply_markup=reply_markup)
    return CHOOSING_DISPLAY_STYLE

def handle_display_style(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    style = query.data

    context.user_data['display_style'] = style
    
    return manage_apps(update, context)

def handle_maintenance(update: Update, context: CallbackContext) -> int:
    app_name = update.message.text
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3',
        'Content-Type': 'application/json'
    }
    data = {
        'maintenance': True
    }
    response = requests.patch(f'https://api.heroku.com/apps/{app_name}', headers=headers, json=data)

    if response.status_code == 200:
        update.message.reply_text(f"✅ تم وضع التطبيق {app_name} في وضع الصيانة.")
    else:
        update.message.reply_text(f"❌ حدث خطأ أثناء وضع التطبيق {app_name} في وضع الصيانة. تأكد من اسم التطبيق وحاول مرة أخرى.")
    
    return MANAGING_APPS

def handle_self_delete(update: Update, context: CallbackContext) -> int:
    app_name = update.message.text
    context.user_data['app_to_delete'] = app_name

    keyboard = [
        [InlineKeyboardButton("بعد ساعة", callback_data='delete_1_hour')],
        [InlineKeyboardButton("بعد يوم", callback_data='delete_1_day')],
        [InlineKeyboardButton("بعد أسبوع", callback_data='delete_1_week')],
        [InlineKeyboardButton("عرض الوقت المتبقي", callback_data='show_remaining_time')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر وقت الحذف:", reply_markup=reply_markup)
    
    return MANAGING_APPS

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
    elif time_option == 'delete_1_week':
        delay = 604800

    query.edit_message_text(f"سيتم حذف التطبيق {app_name} بعد {time_option}.")
    
    context.job_queue.run_once(delete_app, delay, context=(api_token, app_name, query.message.chat_id))
    
    return MANAGING_APPS

def delete_app(context: CallbackContext, app_id=None) -> None:
    if app_id:
        api_token = context.user_data.get('api_token')
        chat_id = context.job.context[2] if context.job else context.job_queue._dispatcher.bot_data['chat_id']
    else:
        job = context.job
        api_token, app_name, chat_id = job.context
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.delete(f'https://api.heroku.com/apps/{app_id}', headers=headers)

    if response.status_code == 202:
        context.bot.send_message(chat_id=chat_id, text=f"✅ تم حذف التطبيق {app_id}.")
    else:
        context.bot.send_message(chat_id=chat_id, text=f"❌ حدث خطأ أثناء حذف التطبيق {app_id}.")

def delete_all_apps(query: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        deleted_count = 0
        
        for app in apps:
            app_id = app['id']
            del_response = requests.delete(f'https://api.heroku.com/apps/{app_id}', headers=headers)
            if del_response.status_code == 202:
                deleted_count += 1
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f"تم حذف جميع التطبيقات بنجاح! (عدد التطبيقات المحذوفة: {deleted_count})", reply_markup=reply_markup)
    else:
        query.edit_message_text("حدث خطأ أثناء جلب التطبيقات.")

def show_maintenance_apps(query: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        maintenance_apps = [app for app in apps if app['maintenance']]
        
        if maintenance_apps:
            message = "تطبيقات في وضع الصيانة:\n"
            for app in maintenance_apps:
                message += f"- {app['name']}\n"
        else:
            message = "لا توجد تطبيقات في وضع الصيانة حالياً."
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        query.edit_message_text("حدث خطأ أثناء جلب التطبيقات.")
    
    return MANAGING_APPS

def main() -> None:
    updater = Updater(os.getenv("6529257547:AAG2MGxNXMLGxQtyUtA2zWEylP9QD5m-hGE"))

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING_API: [MessageHandler(Filters.text & ~Filters.command, ask_api)],
            MANAGING_APPS: [CallbackQueryHandler(button)],
            ASKING_DELETE_TIME: [MessageHandler(Filters.text & ~Filters.command, schedule_delete)],
            ASKING_APP_FOR_MAINTENANCE: [MessageHandler(Filters.text & ~Filters.command, handle_maintenance)],
            ASKING_APP_NAME_FOR_SELF_DELETE: [MessageHandler(Filters.text & ~Filters.command, handle_self_delete)],
            CHOOSING_DISPLAY_STYLE: [CallbackQueryHandler(handle_display_style)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
