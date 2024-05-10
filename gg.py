import telebot
import os
import ast
import sys
import importlib.util
import inspect

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
            libraries = {}
            errors = []

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

            for module in modules:
                try:
                    imported_module = importlib.import_module(module)
                    libraries[module] = {
                        'functions': [func[0] for func in inspect.getmembers(imported_module, inspect.isfunction)],
                        'classes': [cls[0] for cls in inspect.getmembers(imported_module, inspect.isclass)],
                        'documentation': inspect.getdoc(imported_module)
                    }
                except Exception as e:
                    errors.append((module, str(e)))

            module_info = ""
            for library, info in libraries.items():
                module_info += f"\n\n{name_module(library)}:\n  الوظائف: {', '.join(info['functions'])}\n  الكلاسات: {', '.join(info['classes'])}\n  الوثائق: {info['documentation']}"

            error_info = ""
            if errors:
                error_info = "أخطاء في استيراد:"
                for module, error_msg in errors:
                    error_info += f"\n- {name_module(module)}: {error_msg}"

            return f"تم تحليل الملف بنجاح!\n\nمعلومات عن الملف:\n- اسم الملف: {file_name}\n- الوحدات المستوردة: {', '.join(sorted(modules))}\n{module_info}\n\n{error_info}"
    except Exception as e:
        return f"حدث خطأ أثناء تحليل الملف: {e}"

def name_module(module):
    return module.split('.')[-1]

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"حدث خطأ أثناء تشغيل البوت: {e}")
