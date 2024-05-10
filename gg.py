import telebot
import os
import ast

# استبدل 'YOUR_TELEGRAM_BOT_TOKEN_HERE' برمز المصادقة الخاص ببوتك
TOKEN = '7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['document'])
def handle_document(message):
    # قم بتنزيل الملف
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = message.document.file_name

    # احفظ الملف
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    # قم بتحليل الملف
    file_info = analyze_python_file(file_name)

    # أرسل نتيجة التحليل
    bot.reply_to(message, file_info)

def analyze_python_file(file_name):
    try:
        with open(file_name, 'r') as file:
            tree = ast.parse(file.read())
            modules = set()
            libraries = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        modules.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    modules.add(node.module)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'import':
                    for arg in node.args:
                        modules.add(arg.s)
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == '__import__':
                    modules.add(node.attr)
                elif isinstance(node, ast.ImportFrom):
                    modules.add(node.module)

            for module in modules:
                try:
                    __import__(module)
                    libraries.add(module)
                except ImportError:
                    pass

            return f"الملف: {file_name}\n\nالوحدات: {', '.join(modules)}\n\nالمكتبات: {', '.join(libraries)}"
    except Exception as e:
        return f"خطأ في تحليل الملف: {e}"

if __name__ == '__main__':
    bot.polling()
