import telebot
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread

bot_token = '7119817477:AAE2ri5rB-kt9S4rTeLIAReC5PGv1noe61I'
bot = telebot.TeleBot(bot_token)
user_data = {}


keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
btn_add_recipient = telebot.types.InlineKeyboardButton('اضف ايميل الدعم (اكثر من ايميل)', callback_data='add_recipient')
btn_add_sender = telebot.types.InlineKeyboardButton('اضف ايميل شد', callback_data='add_sender')
btn_change_recipient = telebot.types.InlineKeyboardButton('اختيار ايميل الدعم (ايميل واحد)', callback_data='change_recipient')
btn_set_subject = telebot.types.InlineKeyboardButton('تعيين موضوع', callback_data='set_subject')
btn_set_message = telebot.types.InlineKeyboardButton('تعيين كليشه', callback_data='set_message')
btn_set_interval = telebot.types.InlineKeyboardButton('تعيين سليب', callback_data='set_interval')
btn_set_message_count = telebot.types.InlineKeyboardButton('تعيين عدد الارسال', callback_data='set_message_count')
btn_start_sending = telebot.types.InlineKeyboardButton('بدء الارسال', callback_data='start_sending')
btn_show_accounts = telebot.types.InlineKeyboardButton('ايميلاتي', callback_data='show_accounts')
btn_show_all_info = telebot.types.InlineKeyboardButton('عرض المعلومات', callback_data='show_all_info')
btn_clear_all_info = telebot.types.InlineKeyboardButton('مسح كل المعلومات', callback_data='clear_all_info')
btn_delete_email = telebot.types.InlineKeyboardButton('حذف ايميل محدد', callback_data='delete_email')
btn_stop_sending = telebot.types.InlineKeyboardButton('', callback_data='stop_sending')

keyboard.add(btn_add_recipient, btn_add_sender)
keyboard.add(btn_change_recipient, btn_set_subject, btn_set_message)
keyboard.add(btn_set_interval, btn_set_message_count)
keyboard.add(btn_start_sending, btn_show_accounts)
keyboard.add(btn_show_all_info, btn_clear_all_info)
keyboard.add(btn_delete_email, btn_stop_sending)



@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id in allowed_users:
        add_user_to_data(user_id)
        bot.reply_to(message, 'اهلا بك في بوت الرفع الخارجي المطورين @KK8KC, شرح البوت تابعه قبل لا تبدي @Py_Val', reply_markup=keyboard)
    else:
        bot.reply_to(message, 'انت غير مشترك في البوت للاشتراك في البوت : @KK8KC')



@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = str(message.from_user.id)
    user_info = user_data.get(user_id)
    if user_info:
        user_info['stop_sending'] = True
        bot.reply_to(message, 'تم إيقاف عملية الإرسال بنجاح!')
    else:
        bot.reply_to(message, 'لم تقم ببدء عملية الإرسال بعد.')



@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = str(call.from_user.id)
    add_user_to_data(user_id)
    user_info = user_data[user_id]

    if call.data == 'add_recipient':
        bot.reply_to(call.message, 'الرجاء ارسال الايميل المراد الارسال اليه')
        bot.register_next_step_handler(call.message, add_recipient, user_id)
    elif call.data == 'add_sender':
        bot.reply_to(call.message, 'الرجاء ارسال الايميل الخاص بك')
        bot.register_next_step_handler(call.message, add_sender, user_id)
    elif call.data == 'change_recipient':
        bot.reply_to(call.message, 'الرجاء ارسال الايميل المراد الشد او الرفع عليه')
        bot.register_next_step_handler(call.message, change_recipient, user_id)
    elif call.data == 'set_subject':
        bot.reply_to(call.message, 'الرجاء ارسال الموضوع الخاص بكليشتك')
        bot.register_next_step_handler(call.message, set_subject, user_id)
    elif call.data == 'set_message':
        bot.reply_to(call.message, 'الرجاء ارسال الكلمة الخاصة بكليشتك')
        bot.register_next_step_handler(call.message, set_message, user_id)
    elif call.data == 'set_interval':
        bot.reply_to(call.message, 'الرجاء ارسال الفاصل الزمني بين الرسائل (بالثواني)')
        bot.register_next_step_handler(call.message, set_interval, user_id)
    elif call.data == 'set_message_count':
        bot.reply_to(call.message, 'الرجاء ارسال عدد الرسائل المطلوب إرسالها')
        bot.register_next_step_handler(call.message, set_message_count, user_id)
    elif call.data == 'start_sending':
        bot.reply_to(call.message, 'جارٍ بدء إرسال الرسائل...')
        start_sending(user_id)
    elif call.data == 'show_accounts':
        show_accounts(call.message, user_id)
    elif call.data == 'show_all_info':
        show_all_info(call.message, user_id)
    elif call.data == 'clear_all_info':
        clear_all_info(call.message, user_id)
    elif call.data == 'delete_email':
        bot.reply_to(call.message, 'الرجاء إرسال رقم البريد الإلكتروني الذي ترغب في حذفه.')
        bot.register_next_step_handler(call.message, delete_email, user_id)
    elif call.data == 'stop_sending':
        stop_sending(call.message)


def add_user_to_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'email_senders': [],
            'email_passwords': [],
            'recipients': [],
            'email_subject': '',
            'email_message': '',
            'interval_seconds': 0,
            'message_count': 0
        }


def add_recipient(message, user_id):
    recipient = message.text
    if recipient:
        user_data[user_id]['recipients'].append(recipient)
        bot.reply_to(message, 'تمت إضافة الحساب المستلم بنجاح!')
    else:
        bot.reply_to(message, 'خطأ في إضافة الحساب المستلم. الرجاء المحاولة مرة أخرى.')


def add_sender(message, user_id):
    sender_email = message.text
    if sender_email:
        user_data[user_id]['email_senders'].append(sender_email)
        bot.reply_to(message, 'الرجاء إرسال كلمة المرور الخاصة بالحساب المرسل.')
        bot.register_next_step_handler(message, add_sender_password, user_id)
    else:
        bot.reply_to(message, 'خطأ في إضافة الحساب المرسل. الرجاء المحاولة مرة أخرى.')


def add_sender_password(message, user_id):
    sender_password = message.text
    if sender_password:
        user_data[user_id]['email_passwords'].append(sender_password)
        bot.reply_to(message, 'تمت إضافة الحساب المرسل بنجاح!')
    else:
        bot.reply_to(message, 'خطأ في إضافة كلمة المرور. الرجاء المحاولة مرة أخرى.')


def change_recipient(message, user_id):
    recipient = message.text
    if recipient:
        user_data[user_id]['recipients'].clear()
        user_data[user_id]['recipients'].append(recipient)
        bot.reply_to(message, 'تم تغيير الحساب المستلم بنجاح!')
    else:
        bot.reply_to(message, 'خطأ في تغيير الحساب المستلم. الرجاء المحاولة مرة أخرى.')


def set_subject(message, user_id):
    user_data[user_id]['email_subject'] = message.text
    bot.reply_to(message, 'تم تعيين الموضوع بنجاح!')


def set_message(message, user_id):
    user_data[user_id]['email_message'] = message.text
    bot.reply_to(message, 'تم تعيين الكلمة الخاصة بالرسالة بنجاح!')


def set_interval(message, user_id):
    try:
        user_data[user_id]['interval_seconds'] = int(message.text)
        bot.reply_to(message, 'تم تعيين الفاصل الزمني بنجاح!')
    except ValueError:
        bot.reply_to(message, 'خطأ في التحويل إلى رقم. يرجى إدخال قيمة صحيحة للفاصل الزمني.')


def set_message_count(message, user_id):
    try:
        user_data[user_id]['message_count'] = int(message.text)
        bot.reply_to(message, 'تم تعيين عدد الرسائل بنجاح!')
    except ValueError:
        bot.reply_to(message, 'خطأ في التحويل إلى رقم. يرجى إدخال قيمة صحيحة لعدد الرسائل.')


def delete_email(message, user_id):
    try:
        index = int(message.text) - 1
        if index >= 0 and index < len(user_data[user_id]['email_senders']):
            del user_data[user_id]['email_senders'][index]
            bot.reply_to(message, 'تم حذف البريد الإلكتروني بنجاح!')
        else:
            bot.reply_to(message, 'خطأ في حذف البريد الإلكتروني. الرجاء المحاولة مرة أخرى.')
    except ValueError:
        bot.reply_to(message, 'خطأ في التحويل إلى رقم. يرجى إدخال رقم صحيح لحذف البريد الإلكتروني.')


def send_email(sender_email, sender_password, recipient, subject, message):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(str(e))
        return False


def start_sending(user_id):
    user_info = user_data[user_id]
    if len(user_info['recipients']) == 0:
        bot.send_message(user_id, 'لا يوجد حسابات مستلمة. الرجاء إضافة حساب مستلم أولاً.')
        return

    if len(user_info['email_senders']) == 0:
        bot.send_message(user_id, 'لا يوجد حسابات مرسلة. الرجاء إضافة حساب مرسل أولاً.')
        return

    if user_info['email_subject'] == '':
        bot.send_message(user_id, 'لم يتم تعيين الموضوع. الرجاء تعيين الموضوع أولاً.')
        return

    if user_info['email_message'] == '':
        bot.send_message(user_id, 'لم يتم تعيين الرسالة. الرجاء تعيين الرسالة أولاً.')
        return

    if user_info['interval_seconds'] == 0:
        bot.send_message(user_id, 'لم يتم تعيين الفاصل الزمني. الرجاء تعيين الفاصل الزمني أولاً.')
        return

    if user_info['message_count'] == 0:
        bot.send_message(user_id, 'لم يتم تعيين عدد الرسائل. الرجاء تعيين عدد الرسائل أولاً.')
        return

    bot.send_message(user_id, 'جارٍ بدء إرسال الرسائل...')
    error_message = 'حدث أخطاء أثناء الإرسال:\n'
    success_message = 'تم إرسال الرسائل بنجاح.\n'
    prev_message = None
    
    for i in range(user_info['message_count']):
        for sender, password in zip(user_info['email_senders'], user_info['email_passwords']):
            try:
                sender_email = sender
                recipient_email = random.choice(user_info['recipients'])

                if user_info.get('stop_sending'):
                    del user_info['stop_sending']
                    bot.send_message(user_id, 'تم إيقاف عملية الإرسال.')
                    return

                if prev_message:
                    bot.delete_message(user_id, prev_message.message_id)

                if send_email(sender_email, password, recipient_email, user_info['email_subject'],
                              user_info['email_message']):
                    success_message += f'تم إرسال الرسالة رقم {i + 1} بنجاح!\n'
                else:
                    error_message += f'حدث خطأ أثناء إرسال الرسالة رقم {i + 1}\n'
                prev_message = bot.send_message(user_id, success_message + '\n' + error_message + 'لإيقاف الإرسال ارسل /stop')
            except Exception as e:
                error_message += f'حدث خطأ أثناء إرسال الرسالة رقم {i + 1}: {str(e)}\n'

        time.sleep(user_info['interval_seconds'])
    
    final_message = success_message + '\n' + error_message + 'لإيقاف الإرسال ارسل /stop'
    bot.send_message(user_id, final_message)




def show_accounts(message, user_id):
    user_info = user_data[user_id]
    if len(user_info['email_senders']) == 0:
        bot.reply_to(message, 'لم يتم إضافة أي حسابات مرسلة حتى الآن.')
    else:
        accounts = []
        for i, sender in enumerate(user_info['email_senders']):
            accounts.append(f'حساب رقم {i + 1}: {sender}')

        bot.reply_to(message, '\n'.join(accounts))


def show_all_info(message, user_id):
    user_info = user_data[user_id]
    info_message = f"المستلمين: {', '.join(user_info['recipients'])}\n"
    info_message += f"المرسلين: {', '.join(user_info['email_senders'])}\n"
    info_message += f"الموضوع: {user_info['email_subject']}\n"
    info_message += f"الرسالة: {user_info['email_message']}\n"
    info_message += f"الفاصل الزمني: {user_info['interval_seconds']} ثانية\n"
    info_message += f"عدد الرسائل: {user_info['message_count']}\n"
    bot.reply_to(message, info_message)


def clear_all_info(message, user_id):
    user_data[user_id] = {
        'email_senders': [],
        'email_passwords': [],
        'recipients': [],
        'email_subject': '',
        'email_message': '',
        'interval_seconds': 0,
        'message_count': 0
    }
    bot.reply_to(message, 'تم مسح جميع المعلومات بنجاح!')





allowed_users = ['1020311286']


allowed_add_user_users = ['1020311286']


def add_user_to_allowed_users(user_id):
    allowed_users.append(user_id)
    return True


def is_user_allowed_to_add_user(user_id):
    return user_id in allowed_add_user_users


@bot.message_handler(commands=['adduser'])
def add_user_command(message):
    user_id = str(message.from_user.id)
    if is_user_allowed_to_add_user(user_id):
        new_user_id = None
        try:
            new_user_id = message.text.split()[1]
        except IndexError:
            bot.reply_to(message, 'الرجاء توفير معرف المستخدم لإضافته.')
            return       
        if new_user_id not in allowed_users:
            if add_user_to_allowed_users(new_user_id):
                bot.reply_to(message, 'تمت إضافة المستخدم بنجاح.')
            else:
                bot.reply_to(message, 'حدثت مشكلة أثناء إضافة المستخدم. يرجى المحاولة مرة أخرى لاحقًا.')
        else:
            bot.reply_to(message, 'المستخدم بالفعل مضاف إلى القائمة.')
    else:
        bot.reply_to(message, 'غير مسموح لك باستخدام هذا الأمر.')



allowed_users = ['1020311286']

allowed_remove_user_users = ['1020311286']

def remove_user_from_allowed_users(user_id):
    if user_id in allowed_users:
        allowed_users.remove(user_id)
        return True
    return False

def is_user_allowed_to_remove_user(user_id):
    return user_id in allowed_remove_user_users

@bot.message_handler(commands=['removeuser'])
def remove_user_command(message):
    user_id = str(message.from_user.id)
    if is_user_allowed_to_remove_user(user_id):
        user_to_remove_id = None
        try:
            user_to_remove_id = message.text.split()[1]
        except IndexError:
            bot.reply_to(message, 'الرجاء توفير معرف المستخدم لإزالته.')
            return
        if user_to_remove_id in allowed_users:
            if remove_user_from_allowed_users(user_to_remove_id):
                bot.reply_to(message, 'تمت إزالة المستخدم بنجاح.')
            else:
                bot.reply_to(message, 'حدثت مشكلة أثناء إزالة المستخدم. يرجى المحاولة مرة أخرى لاحقًا.')
        else:
            bot.reply_to(message, 'المستخدم غير موجود في القائمة.')
    else:
        bot.reply_to(message, 'غير مسموح لك باستخدام هذا الأمر.')


bot.polling()
