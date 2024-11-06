import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio
import shutil
from kvsqlite.sync import Client as uu
from telethon import TelegramClient, events, Button
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

# Default settings
default_settings = {
    "send_delay": 30,
    "repetitions": 5
}

# Create Database
db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])
if not db.exists("settings"):
    db.set("settings", default_settings)
if not db.exists("groups"):
    db.set("groups", [])

def main_buttons():
    account_count = len(db.get("accounts"))
    buttons = [[Button.inline(f"➕ إضافة حساب ({account_count})", data="add")]]
    if account_count > 0:
        buttons.append([Button.inline("📥 جلب رسائل مستخدم", data="fetch_messages")])
    return buttons

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    await event.reply(
        "👋 أهلاً بك! يمكنك اختيار أحد الخيارات أدناه.",
        buttons=main_buttons()
    )

@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if data == "add":
        async with bot.conversation(user_id) as conv:
            account_count = len(db.get("accounts"))
            if account_count >= 5:
                await conv.send_message("⚠️ الحد الأقصى لعدد الحسابات هو 5.")
                return

            await conv.send_message("✔️ الآن أرسل رقمك مع رمز دولتك، مثال: +201000000000")
            txt = await conv.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")
            
            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            try:
                await app.send_code_request(phone_number)
            except (ApiIdInvalidError, PhoneNumberInvalidError):
                await conv.send_message("❌ هناك خطأ في API_ID أو HASH_ID أو رقم الهاتف.")
                return

            await conv.send_message("- تم إرسال كود التحقق الخاص بك على تليجرام. أرسل الكود بالتنسيق التالي: 1 2 3 4 5")
            txt = await conv.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code)
                string_session = app.session.save()
                accounts = db.get("accounts")
                accounts.append({"phone_number": phone_number, "session": string_session})
                db.set("accounts", accounts)
                await conv.send_message("✅ تم حفظ الحساب بنجاح.", buttons=main_buttons())
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await conv.send_message("❌ الكود المدخل غير صحيح أو منتهي الصلاحية.", buttons=main_buttons())
            except SessionPasswordNeededError:
                await conv.send_message("- أرسل رمز التحقق بخطوتين الخاص بحسابك.")
                txt = await conv.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                    string_session = app.session.save()
                    accounts = db.get("accounts")
                    accounts.append({"phone_number": phone_number, "session": string_session})
                    db.set("accounts", accounts)
                    await conv.send_message("✅ تم حفظ الحساب بنجاح.", buttons=main_buttons())
                except PasswordHashInvalidError:
                    await conv.send_message("❌ رمز التحقق بخطوتين المدخل غير صحيح.", buttons=main_buttons())
            finally:
                await app.disconnect()

    elif data == "fetch_messages":
        account_count = len(db.get("accounts"))
        if account_count == 0:
            await event.edit("⚠️ لا يوجد حساب مضاف حاليًا. قم بإضافة حساب أولاً.", buttons=main_buttons())
            return

        async with bot.conversation(user_id) as conv:
            await conv.send_message("أدخل معرف المستخدم أو ID الخاص بالمستخدم المراد جلب رسائله.")
            txt = await conv.get_response()
            user_input = txt.text.strip()

            if not user_input:
                await conv.send_message("❌ تأكد من إدخال معرف المستخدم أو ID صحيح.", buttons=main_buttons())
                return

            processing_msg = await conv.send_message("🔄 جاري جلب الرسائل...")
            messages = []

            for account_data in db.get("accounts"):
                try:
                    app = TelegramClient(StringSession(account_data['session']), API_ID, API_HASH)
                    await app.connect()

                    async for message in app.iter_messages(user_input, limit=100):
                        messages.append(message.text)

                    await conv.send_message(f"✅ تم جلب الرسائل بنجاح من الحساب {account_data['phone_number']}:\n\n" + "\n".join(messages[-10:]), buttons=main_buttons())
                except Exception as e:
                    await conv.send_message(f"❌ حدث خطأ أثناء جلب الرسائل بالحساب: {str(e)}", buttons=main_buttons())
                finally:
                    await app.disconnect()
            
            await processing_msg.delete()

# بدء تشغيل البوت
print("Bot is running...")
client.run_until_disconnected()
