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

# Default settings
default_settings = {
    "send_delay": 30,  # Default time between messages in seconds
    "repetitions": 5   # Default number of repetitions
}

# Create Database
db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])
if not db.exists("settings"):
    db.set("settings", default_settings)

def main_buttons(account_exists):
    buttons = [[Button.inline("➕ إضافة حساب", data="add")]]
    if account_exists:
        buttons.extend([
            [Button.inline("🔄 إرسال متكرر", data="send_repeatedly")],
            [Button.inline("⚙️ الإعدادات", data="settings")],
            [Button.inline("🔒 تسجيل خروج", data="logout")]
        ])
    return buttons

def settings_buttons():
    settings = db.get("settings")
    return [
        [Button.inline(f"⏲️ تعيين وقت الإرسال: {settings['send_delay']} ثانية", data="set_send_delay")],
        [Button.inline(f"🔢 عدد الرسائل: {settings['repetitions']}", data="set_repetitions")],
        [Button.inline("⬅️ العودة", data="back_to_main")]
    ]

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
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

    elif data == "logout":
        db.delete("account")
        await event.edit("✅ تم تسجيل الخروج بنجاح. يمكنك إضافة حساب جديد.", buttons=main_buttons(False))

    elif data == "settings":
        await event.edit("⚙️ الإعدادات:", buttons=settings_buttons())

    elif data == "set_send_delay":
        async with bot.conversation(user_id) as x:
            await x.send_message("⏲️ أرسل الوقت الجديد بين الرسائل بالثواني.")
            try:
                new_delay = int((await x.get_response()).text)
                settings = db.get("settings")
                settings["send_delay"] = new_delay
                db.set("settings", settings)
                await x.send_message(f"✅ تم تحديث وقت الإرسال إلى: {new_delay} ثانية", buttons=settings_buttons())
            except ValueError:
                await x.send_message("❌ تأكد من إدخال رقم صالح للوقت.")

    elif data == "set_repetitions":
        async with bot.conversation(user_id) as x:
            await x.send_message("🔢 أرسل عدد مرات التكرار الجديد.")
            try:
                new_repetitions = int((await x.get_response()).text)
                settings = db.get("settings")
                settings["repetitions"] = new_repetitions
                db.set("settings", settings)
                await x.send_message(f"✅ تم تحديث عدد الرسائل إلى: {new_repetitions}", buttons=settings_buttons())
            except ValueError:
                await x.send_message("❌ تأكد من إدخال رقم صالح للتكرار.")

    elif data == "back_to_main":
        await event.edit("👋 أهلاً بك! يمكنك اختيار أحد الخيارات أدناه.", buttons=main_buttons(account_exists))

    elif data == "send_repeatedly":
        if not account:
            await event.edit("⚠️ لا يوجد حساب مضاف حالياً. قم بإضافة حساب أولاً.", buttons=main_buttons(False))
            return

        async with bot.conversation(user_id) as x:
            await x.send_message("📝 أرسل اسم المستخدم الذي تريد إرسال الرسائل إليه.")
            txt = await x.get_response()
            username = txt.text
            if not username.startswith("@"):
                username = "@" + username

            await x.send_message("💬 أرسل النص الذي تريد إرساله.")
            message_text = (await x.get_response()).text

            settings = db.get("settings")
            delay = settings["send_delay"]
            repetitions = settings["repetitions"]

            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            try:
                msg_status = await x.send_message(f"✅ تم إرسال حتى الآن: (0/{repetitions})")
                for i in range(repetitions):
                    user = await app.get_entity(username)
                    await app.send_message(user, message_text)
                    await msg_status.edit(f"✅ تم إرسال حتى الآن: ({i + 1}/{repetitions})")
                    await asyncio.sleep(delay)
                await msg_status.delete()
                await x.send_message("✅ تم الانتهاء من إرسال الرسائل المتكررة.")
            except Exception as e:
                await x.send_message(f"❌ حدث خطأ أثناء الإرسال المتكرر: {str(e)}")
            finally:
                await app.disconnect()

client.run_until_disconnected()
