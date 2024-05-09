import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

# Import heroku3 library
import heroku3

# Define the welcome message
welcome_message = "مرحبًا بك! يرجى إرسال API key الخاص بـ Heroku."

# Define the bot token
TOKEN = os.environ.get('7065007495:AAHubA_qSq69iOSNylbFAdl7kVygHUk5yHo')

# Define the function to handle the start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(welcome_message)

# Define the function to handle the API key
def handle_api(update: Update, context: CallbackContext) -> None:
    # Get the API key from the user's message
    api_key = update.message.text.strip()

    # Initialize a Heroku client
    heroku = heroku3.from_key(api_key)

    # Get all apps associated with the Heroku account
    apps = heroku.apps()

    # Delete all apps
    deleted_apps_count = 0
    for app in apps:
        app.delete()
        deleted_apps_count += 1

    # Send the result
    update.message.reply_text(f"تم حذف {deleted_apps_count} تطبيق/تطبيقات بنجاح.")

# Define the main function to run the bot
def main() -> None:
    # Initialize the bot
    updater = Updater(TOKEN)
    bot = Bot(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("api", handle_api))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

# Call the main function to run the bot
if __name__ == '__main__':
    main()
