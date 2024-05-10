import telebot
import os
import importlib_metadata

TOKEN = "7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = message.document.file_name

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    try:
        module_info = importlib_metadata.metadata(file_name)
        libraries = "\n".join(f"- {library}" for library in module_info.requires_dist)
        message_text = f"معلومات الملف: {file_name}\n\nالمكتبات المستخدمة:\n{libraries}"
    except:
        message_text = "حدث خطأ أثناء قراءة معلومات الملف."

    bot.send_message(message.chat.id, message_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_message(message.chat.id, "مرحبًا! يرجى إرسال ملف Python.")

bot.polling()
