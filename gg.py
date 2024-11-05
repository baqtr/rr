import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio, json, shutil
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

# Create DataBase
db = uu('database/elhakem.ss', 'bot')

if not db.exists("account"):
    db.set("account", None)

def main_buttons():
    account = db.get("account")
    if account:
        return [
            [Button.inline("📸 جلب ذاتية", data="fetch_self")],
            [Button.inline("🔒 تسجيل خروج", data="logout")]
        ]
    else:
        return [[Button.inline("➕ إضافة حساب", data="add")]]

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
    if user_id != admin:
        await event.reply("👋 أهلاً بك عزيزي! هذا البوت مخصص لإدارة حساب تيليجرام واحد فقط.")
        return

    await event.reply("👋 مرحبًا بك في بوت إدارة الحساب، اختر من الزر أدناه لإضافة حساب.", buttons=main_buttons())

@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id
    account = db.get("account")

    if data == "add":
        if account:
            await event.edit("⚠️ حساب واحد مضاف بالفعل. لا يمكنك إضافة حساب آخر دون تسجيل الخروج من الحساب الحالي.", buttons=main_buttons())
            return
        async with bot.conversation(user_id) as x:
            await x.send_message("✔️ أرسل رقمك مع رمز دولتك , مثال :+201000000000")
            txt = await x.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")

            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            password = None
            try:
                await app.send_code_request(phone_number)
            except (ApiIdInvalidError, PhoneNumberInvalidError):
                await x.send_message("❌ هناك خطأ في API_ID أو HASH_ID أو رقم الهاتف.")
                return

            await x.send_message("- تم إرسال كود التحقق الخاص بك على تيليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
            txt = await x.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code, password=None)
                string_session = app.session.save()
                db.set("account", {"phone_number": phone_number, "session": string_session, "two-step": "لا يوجد"})
                await x.send_message("- تم إضافة الحساب بنجاح ✅", buttons=main_buttons())
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await x.send_message("❌ الكود المدخل غير صحيح أو منتهي الصلاحية.")
                return
            except SessionPasswordNeededError:
                await x.send_message("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                txt = await x.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                except PasswordHashInvalidError:
                    await x.send_message("❌ رمز التحقق بخطوتين المدخل غير صحيح.")
                    return
                string_session = app.session.save()
                db.set("account", {"phone_number": phone_number, "session": string_session, "two-step": password})
                await x.send_message("- تم إضافة الحساب بنجاح ✅", buttons=main_buttons())

    elif data == "fetch_self":
        if not account:
            await event.edit("⚠️ لا يوجد حساب مضاف حالياً. قم بإضافة حساب أولاً.", buttons=main_buttons())
            return

        async with bot.conversation(user_id) as x:
            await x.send_message("📝 أرسل اسم المستخدم المراد جلب الذاتية منه.")
            txt = await x.get_response()
            username = txt.text
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            try:
                user = await app.get_entity(username)
                photo = await app.download_profile_photo(user, file=bytes)
                await x.send_file(file=photo, caption="📸 هذه هي الذاتية.")
            except Exception as e:
                await x.send_message("❌ حدث خطأ أثناء جلب الذاتية. تأكد من صحة اسم المستخدم.")
            finally:
                await app.disconnect()

    elif data == "logout":
        if not account:
            await event.edit("⚠️ لا يوجد حساب مضاف حالياً.", buttons=main_buttons())
            return

        app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
        await app.connect()
        await app.log_out()
        await app.disconnect()
        
        db.set("account", None)
        await event.edit("- تم تسجيل الخروج وحذف الحساب بنجاح. يمكنك الآن إضافة حساب جديد.", buttons=main_buttons())

client.run_until_disconnected()
