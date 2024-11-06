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
db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])
if not db.exists("settings"):
    db.set("settings", {})
if not db.exists("groups"):
    db.set("groups", [])

def main_buttons(account_exists):
    buttons = [[Button.inline("➕ إضافة حساب", data="add")]]
    if account_exists:
        buttons.append([Button.inline("🚀 رشق رابط دعوة", data="send_invites")])
    return buttons

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

    elif data == "send_invites":
        if not account:
            await event.edit("⚠️ لا يوجد حساب مضاف حالياً. قم بإضافة حساب أولاً.", buttons=main_buttons(False))
            return

        async with bot.conversation(user_id) as x:
            await x.send_message("🔗 أرسل رابط الدعوة الخاص بالبوت المراد رشقه.")
            txt = await x.get_response()
            invite_link = txt.text

            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            try:
                # Join the bot using the invite link
                await app(functions.messages.ImportChatInviteRequest(invite_link.split("/")[-1]))

                count = 0
                while True:
                    # Retrieve the last message from the bot
                    bot_entity = await app.get_entity(invite_link)
                    message = await app.get_messages(bot_entity, limit=1)

                    # Check if message contains a join link
                    if not message or "t.me/" not in message[0].message:
                        break
                    
                    # Join the provided channel link
                    channel_link = message[0].message.split("t.me/")[1]
                    await app(functions.messages.ImportChatInviteRequest(channel_link.split("/")[-1]))
                    count += 1
                    await asyncio.sleep(2)  # Wait before requesting the next invite link

                await x.send_message(f"✅ تم الانتهاء من عملية الرشق. عدد الروابط التي تم الاشتراك فيها: {count}")
            except Exception as e:
                await x.send_message(f"❌ حدث خطأ أثناء عملية الرشق: {str(e)}")
            finally:
                await app.disconnect()

client.run_until_disconnected()
