0%", chat_id=call.message.chat.id, message_id=call.message.message_id)
    time.sleep(2)
    response = requests.get(f'{HEROKU_BASE_URL}/apps', headers=headers)
    if response.status_code == 200:
        apps = response.json()
        apps_list = "\n".join([f"`{app['name']}`" for app in apps])
        bot.edit_message_text("جلب التطبيقات... ⬛⬛ 50%", chat_id=call.message.chat.id, message_id=call.message.message_id)
        time.sleep(2)
        bot.edit_message_text(f"التطبيقات المتاحة في هيروكو:\n{apps_list}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button(), parse_mode='Markdown')
    else:
        bot.edit_message_text("حدث خطأ في جلب التطبيقات من هيروكو.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"إدارة حساب {account_index + 1}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_heroku_apps_"):
        list_heroku_apps(call)
    elif call.data.startswith("delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_deletion(m, account_index))
    elif call.data.startswith("self_delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق للحذف الذاتي:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_self_deletion(m, account_index))
    elif call.data == "remaining_time":
        show_remaining_time(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    elif call.data == "github_section":
        bot.edit_message_text("قسم جيتهاب:\nيرجى اختيار إحدى الخيارات:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_github_control_buttons())

# دالة لعرض الوقت المتبقي للحذف الذاتي
def show_remaining_time(call):
    remaining_time_message = "التطبيقات المجدولة للحذف الذاتي:\n"
    for app_name, data in list(self_deleting_apps.items()):
        if app_name in self_deleting_apps:
            elapsed_time = (datetime.now(pytz.timezone('Asia/Baghdad')) - data['start_time']).total_seconds() // 60
            remaining_minutes = max(data['minutes'] - elapsed_time, 0)
            remaining_time_message += f"- {app_name}:\n  الوقت المتبقي: {format_remaining_time(remaining_minutes)}\n  تاريخ الحذف: {calculate_deletion_time(remaining_minutes)}\n"
        else:
            remaining_time_message += f"- {app_name}: تم حذفه."
    bot.edit_message_text(remaining_time_message, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=create_back_button())

# زر عرض الوقت المتبقي
def create_remaining_time_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("الوقت المتبقي ⏳", callback_data="remaining_time")
    markup.add(button)
    return markup

# دالة لمعالجة اسم التطبيق للحذف
def handle_app_name_for_deletion(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    if validate_heroku_app(app_name, account_index, user_id):
        delete_heroku_app(app_name, message, account_index)
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# تحقق من صحة اسم التطبيق
def validate_heroku_app(app_name, account_index, user_id):
    headers = {
        'Authorization': f'Bearer {user_accounts[user_id][account_index]["api_key"]}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get(f'{HEROKU_BASE_URL}/apps/{app_name}', headers=headers)
    return response.status_code == 200

# دالة لمعالجة اسم التطبيق للحذف الذاتي
def handle_app_name_for_self_deletion(message, account_index):
    app_name = message.text.strip()
    user_id = message.from_user.id
    if validate_heroku_app(app_name, account_index, user_id):
        if app_name in self_deleting_apps:
            bot.send_message(message.chat.id, f"تم وضع التطبيق `{app_name}` مسبقًا في قائمة الحذف الذاتي.", parse_mode='Markdown')
        else:
            msg = bot.send_message(message.chat.id, "يرجى إدخال الوقت المطلوب بالدقائق لحذف التطبيق:")
            bot.register_next_step_handler(msg, lambda m: handle_self_deletion_time(m, app_name, account_index))
    else:
        bot.send_message(message.chat.id, f"اسم التطبيق `{app_name}` غير صحيح.", parse_mode='Markdown')

# دالة لمعالجة الوقت للحذف الذاتي
def handle_self_deletion_time(message, app_name, account_index):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
        self_deleting_apps[app_name] = {'minutes': minutes, 'start_time': datetime.now(pytz.timezone('Asia/Baghdad'))}
        bot.send_message(message.chat.id, f"سيتم حذف التطبيق `{app_name}` بعد {minutes} دقيقة.\n", reply_markup=create_remaining_time_button())
        # بدء عملية الحذف الذاتي
        threading.Timer(minutes * 60, lambda: delete_and_remove_app(app_name, message, account_index)).start()
    except ValueError:
        bot.send_message(message.chat.id, "الرجاء إدخال عدد صحيح إيجابي للدقائق.")

# زر رفع ملف
def create_upload_file_button():
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("رفع ملف 📁", callback_data="upload_file")
    markup.add(button)
    return markup

# دالة لعرض زر رفع ملف
def upload_file(call):
    bot.edit_message_text("يرجى رفع ملف مضغوط (ZIP) لإنشاء مستودع جديد.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())

# دالة لمعالجة رفع الملف
def handle_upload_file(message):
    user_id = message.from_user.id
    file_id = message.document.file_id
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)
    zip_file_name = f"{user_id}_repo.zip"
    with open(zip_file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.send_message(message.chat.id, f"تم تحميل الملف بنجاح: {zip_file_name}")
    # بدء عملية فك الضغط
    threading.Thread(target=extract_zip_and_create_repo, args=(zip_file_name, user_id, message.chat.id)).start()

# دالة لفك الضغط وإنشاء مستودع جديد
def extract_zip_and_create_repo(zip_file_name, user_id, chat_id):
    try:
        with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
            zip_ref.extractall(f"{user_id}_repo")
        # إنشاء مستودع جديد
        repo_name = create_github_repo(user_id)
        # رفع الملفات إلى المستودع الجديد
        upload_files_to_github_repo(user_id, repo_name)
        # حذف الملفات المؤقتة
        shutil.rmtree(f"{user_id}_repo")
        os.remove(zip_file_name)
        bot.send_message(chat_id, f"تم إنشاء المستودع بنجاح: [{repo_name}](https://github.com/{user_id}/{repo_name})\nعدد الملفات المرفوعة: {count_files_in_repo(user_id, repo_name)}", parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ أثناء معالجة الملف: {e}")

# دالة لإنشاء مستودع جديد على جيتهاب
def create_github_repo(user_id):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        "name": f"{user_id}_repo",
        "auto_init": True,
        "private": False
    }
    response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
    if response.status_code == 201:
        return f"{user_id}_repo"
    else:
        return None

# دالة لرفع الملفات إلى مستودع جيتهاب
def upload_files_to_github_repo(user_id, repo_name):
    repo_path = f"{user_id}_repo"
    repo_full_name = f"{user_id}/{repo_name}"
    files = os.listdir(repo_path)
    for file in files:
        file_path = os.path.join(repo_path, file)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as content_file:
                file_content = content_file.read()
            headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Content-Type': 'application/octet-stream',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.put(f"https://api.github.com/repos/{repo_full_name}/contents/{file}", headers=headers, data=json.dumps({
                "message": "Add file",
                "content": base64.b64encode(file_content).decode("utf-8")
            }))
            if response.status_code != 201:
                print(f"Failed to upload file {file} to GitHub repo {repo_full_name}")
    shutil.rmtree(repo_path)

# دالة لعد الفايلات الموجودة في مستودع جيتهاب
def count_files_in_repo(user_id, repo_name):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(f"https://api.github.com/repos/{user_id}/{repo_name}/contents")
    if response.status_code == 200:
        files = response.json()
        return len(files)
    else:
        return 0

# دالة لإنشاء زر للعودة
def create_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton("العودة ↩️", callback_data="go_back")
    markup.add(back_button)
    return markup

# دالة لإنشاء زر للرفع
def create_upload_button():
    markup = telebot.types.InlineKeyboardMarkup()
    upload_button = telebot.types.InlineKeyboardButton("رفع ملف 📁", callback_data="upload_file")
    markup.add(upload_button)
    return markup

# دالة لإنشاء زر للحذف الذاتي
def create_self_delete_button():
    markup = telebot.types.InlineKeyboardMarkup()
    self_delete_button = telebot.types.InlineKeyboardButton("حذف الكل للحذف جمييع المستودعات 🗑️", callback_data="delete_all_repos")
    markup.add(self_delete_button)
    return markup

# دالة لحذف جميع المستودعات
def delete_all_repos(call):
    user_id = call.from_user.id
    repo_names = get_user_repo_names(user_id)
    if repo_names:
        for repo_name in repo_names:
            delete_github_repo(user_id, repo_name)
        bot.send_message(call.message.chat.id, "تم حذف جميع المستودعات بنجاح.", reply_markup=create_back_button())
    else:
        bot.send_message(call.message.chat.id, "لا توجد مستودعات لحذفها.", reply_markup=create_back_button())

# دالة لجلب أسماء مستودعات المستخدم
def get_user_repo_names(user_id):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(f"https://api.github.com/user/repos", headers=headers)
    if response.status_code == 200:
        repos = response.json()
        repo_names = [repo["name"] for repo in repos if repo["owner"]["login"] == str(user_id)]
        return repo_names
    else:
        return []

# دالة لحذف مستودع جيتهاب
def delete_github_repo(user_id, repo_name):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.delete(f"https://api.github.com/repos/{user_id}/{repo_name}", headers=headers)
    if response.status_code == 204:
        print(f"Repository {repo_name} deleted successfully.")
    else:
        print(f"Failed to delete repository {repo_name}.")

# دالة لمعالجة النقرات على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_account":
        add_account(call)
    elif call.data == "list_accounts":
        list_accounts(call)
    elif call.data.startswith("select_account_"):
        account_index = int(call.data.split("_")[-1])
        bot.edit_message_text(f"إدارة حساب {account_index + 1}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_account_control_buttons(account_index))
    elif call.data.startswith("list_heroku_apps_"):
        list_heroku_apps(call)
    elif call.data.startswith("delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق لحذفه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_deletion(m, account_index))
    elif call.data.startswith("self_delete_app_"):
        account_index = int(call.data.split("_")[-1])
        msg = bot.edit_message_text("يرجى إرسال اسم التطبيق للحذف الذاتي:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_back_button())
        bot.register_next_step_handler(msg, lambda m: handle_app_name_for_self_deletion(m, account_index))
    elif call.data == "remaining_time":
        show_remaining_time(call)
    elif call.data == "go_back":
        bot.edit_message_text("مرحبًا بك! اضغط على الأزرار أدناه لتنفيذ الإجراءات.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_main_buttons())
    elif call.data == "upload_file":
        upload_file(call)
    elif call.data == "delete_all_repos":
        delete_all_repos(call)

# التشغيل
if __name__ == "__main__":
    bot.polling()
