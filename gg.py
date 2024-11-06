import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio
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

db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])
if not db.exists("groups"):
    db.set("groups", [])

def main_buttons():
    return [
        [Button.inline("➕ إضافة حساب", data="add")],
        [Button.inline("🔄 رشق رابط دعوة", data="join_invite_link")]
    ]

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    await event.reply("👋 أهلاً بك! يمكنك اختيار أحد الخيارات أدناه.", buttons=main_buttons())

@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if data == "add":
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
                accounts = db.get("accounts")
                accounts.append({"phone_number": phone_number, "session": string_session})
                db.set("accounts", accounts)
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=main_buttons())
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await x.send_message("❌ الكود المدخل غير صحيح أو منتهي الصلاحية.", buttons=main_buttons())
            except SessionPasswordNeededError:
                await x.send_message("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                txt = await x.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                    string_session = app.session.save()
                    accounts = db.get("accounts")
                    accounts.append({"phone_number": phone_number, "session": string_session})
                    db.set("accounts", accounts)
                    await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=main_buttons())
                except PasswordHashInvalidError:
                    await x.send_message("❌ رمز التحقق بخطوتين المدخل غير صحيح.", buttons=main_buttons())
            finally:
                await app.disconnect()

    elif data == "join_invite_link":
        async with bot.conversation(user_id) as x:
            accounts = db.get("accounts")
            if not accounts:
                await x.send_message("⚠️ لا يوجد حسابات مضافة. قم بإضافة حساب أولاً.", buttons=main_buttons())
                return
            
            await x.send_message("🔢 أرسل عدد قنوات الاشتراك الإجباري كرقم.")
            try:
                num_channels = int((await x.get_response()).text)
                if num_channels <= 0:
                    raise ValueError
            except ValueError:
                await x.send_message("❌ تأكد من إدخال رقم صالح للعدد.", buttons=main_buttons())
                return

            channels = []
            for i in range(num_channels):
                await x.send_message(f"📎 أرسل رابط القناة رقم {i + 1}.")
                channel_link = (await x.get_response()).text
                channels.append(channel_link)

            await x.send_message("🔗 أرسل رابط الدعوة الخاص بالبوت المراد رشقه.")
            invite_link = (await x.get_response()).text

            await x.send_message("جاري المعالجة...\nعدد القنوات المختارة (0)\nعدد الانضمام الناجح (0)\nعدد الحسابات التي تمت العملية بها (0)\nعدد الحسابات قيد المعالجة (0)")
            msg_status = await x.send_message(f"عدد القنوات المختارة ({num_channels})\nعدد الانضمام الناجح (0)\nعدد الحسابات التي تمت العملية بها (0)\nعدد الحسابات قيد المعالجة (0)")

            successful_joins = 0
            processed_accounts = 0
            for account in accounts:
                app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
                await app.connect()
                try:
                    for i, channel_link in enumerate(channels):
                        channel = await app.get_entity(channel_link)
                        await app(functions.channels.JoinChannelRequest(channel=channel))
                        successful_joins += 1
                        await msg_status.edit(f"عدد القنوات المختارة ({num_channels})\nعدد الانضمام الناجح ({successful_joins})\nعدد الحسابات التي تمت العملية بها ({processed_accounts})\nعدد الحسابات قيد المعالجة (1)")

                    invite = await app.get_entity(invite_link)
                    await app(functions.messages.ImportChatInviteRequest(invite_link.split('/')[-1]))
                    processed_accounts += 1
                    await msg_status.edit(f"عدد القنوات المختارة ({num_channels})\nعدد الانضمام الناجح ({successful_joins})\nعدد الحسابات التي تمت العملية بها ({processed_accounts})\nعدد الحسابات قيد المعالجة (0)")
                except Exception as e:
                    await x.send_message(f"❌ حدث خطأ أثناء الانضمام بالحساب {account['phone_number']}: {str(e)}")
                finally:
                    await app.disconnect()

            await x.send_message("✅ تم الانتهاء من المعالجة.")
client.run_until_disconnected()
