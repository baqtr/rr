import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio, json, shutil
from kvsqlite.sync import Client as uu
from telethon import TelegramClient, events, Button
from telethon.tl.types import DocumentAttributeFilename
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

if not db.exists("accounts"):
    db.set("accounts", [])

def main_buttons():
    account = db.get("accounts")
    if account:
        return [
            [Button.inline("🖼️ جلب ذاتية", data="fetch_self")],
            [Button.inline("🔒 تسجيل خروج", data="logout")]
        ]
    else:
        return [[Button.inline("➕ إضافة حساب", data="add")]]

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
    if user_id != admin:
        await event.reply("👋 أهلاً بك عزيزي! هذا البوت مخصص للإدارة ولا يمكنك استخدامه.")
        return

    await event.reply("👋 مرحبًا بك في بوت إدارة الحسابات، اختر من الأزرار أدناه ما تود فعله.", buttons=main_buttons())

@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id
    account = db.get("accounts")[0] if db.get("accounts") else None

    if data == "add":
        if account:
            await event.edit("⚠️ يمكنك إضافة حساب واحد فقط. سجل خروج أولاً لإضافة حساب جديد.", buttons=main_buttons())
            return

        async with bot.conversation(user_id) as x:
            await x.send_message("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000")
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

            await x.send_message("- تم ارسال كود التحقق الخاص بك علي تليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
            txt = await x.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code, password=None)
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
                db.set("accounts", [data])
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=main_buttons())
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await x.send_message("❌ الكود المدخل غير صحيح أو منتهي الصلاحية.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return
            except SessionPasswordNeededError:
                await x.send_message("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                txt = await x.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                except PasswordHashInvalidError:
                    await x.send_message("❌ رمز التحقق بخطوتين المدخل غير صحيح.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                    return
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": password, "session": string_session}
                db.set("accounts", [data])
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=main_buttons())

    elif data == "fetch_self":
        if not account:
            await event.edit("⚠️ لا يوجد حساب مضاف حالياً. قم بإضافة حساب أولاً.", buttons=main_buttons())
            return

        async with bot.conversation(user_id) as x:
            await x.send_message("📝 أرسل اسم المستخدم المراد جلب آخر صورة منه.")
            txt = await x.get_response()
            username = txt.text
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            try:
                user = await app.get_entity(username)
                messages = await app.get_messages(user, limit=10)  # جلب أحدث 10 رسائل للتحقق من وجود صورة

                image_found = False
                for message in messages:
                    if message.photo or message.media and hasattr(message.media, 'ttl_seconds'):  # التحقق إذا كانت الرسالة تحتوي على صورة ذاتية التدمير
                        image_found = True
                        await x.send_file(file=message.media, caption="🖼️ هذه هي آخر صورة تم إرسالها من المستخدم.")
                        break

                if not image_found:
                    await x.send_message("❌ لم يتم العثور على صور مرسلة من هذا المستخدم في أحدث 10 رسائل.")
            except Exception as e:
                await x.send_message("❌ حدث خطأ أثناء جلب الصورة. تأكد من صحة اسم المستخدم.")
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

        db.set("accounts", [])
        await event.edit("🔒 تم تسجيل الخروج بنجاح. يمكنك الآن إضافة حساب جديد.", buttons=main_buttons())

client.run_until_disconnected()
