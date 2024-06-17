import telebot
import os
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# تهيئة نموذج الذكاء الاصطناعي
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

TOKEN = "6419562305:AAHioiCY3MewQREnsxAKczTI7HJVt1MuseI"
bot = telebot.TeleBot(TOKEN)

# معالج أمر البدء
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "👋 مرحبا بك في البوت الخاص بنا! يمكنك استخدام الأزرار أدناه للتنقل في البوت."
    main_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    main_menu.row(KeyboardButton('💡 معلومات عن البوت'), KeyboardButton('📜 التعليمات'))
    main_menu.row(KeyboardButton('❓ المساعدة'), KeyboardButton('📂 إنشاء كود برمجي'))
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu)

# معالج الرسائل النصية
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    chat_id = message.chat.id
    
    if text == '💡 معلومات عن البوت':
        info_text = "هذا البوت مصمم لمساعدتك في العديد من الأمور. استخدم الأزرار أدناه للتفاعل."
        bot.send_message(chat_id, info_text)
    
    elif text == '📜 التعليمات':
        instructions_text = "إليك قائمة بالأوامر التي يمكنك استخدامها:\n\n/start - بدء البوت\n/help - المساعدة\n/info - معلومات عن البوت\n/generate - إنشاء كود برمجي"
        bot.send_message(chat_id, instructions_text)
    
    elif text == '❓ المساعدة':
        help_text = "إذا كنت بحاجة إلى مساعدة، لا تتردد في طرح سؤالك هنا!"
        bot.send_message(chat_id, help_text)
    
    elif text == '📂 إنشاء كود برمجي':
        bot.send_message(chat_id, "📤 الرجاء إرسال وصف للكود البرمجي الذي ترغب في إنشائه.")
    
    elif text == '/generate':
        bot.send_message(chat_id, "📝 الرجاء إرسال وصفٍ للكود البرمجي الذي تود إنشائه.")
    
    else:
        response = generate_code(text)
        send_code_as_file(chat_id, response)

def generate_code(prompt):
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    output = model.generate(input_ids, max_length=100, num_return_sequences=1, no_repeat_ngram_size=2)
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return generated_text

def send_code_as_file(chat_id, code):
    filename = "generated_code.py"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(code)
    with open(filename, 'rb') as file:
        bot.send_document(chat_id, file)
    os.remove(filename)

# تشغيل البوت
bot.polling()
