import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    Updater,
    CallbackContext,
)
import os
import threading
import asyncio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


updater = Updater(os.environ["TELEGRAMBOTAPIKEY"], True)

# updater.dispatcher.add_handler(CommandHandler("start", start))


async def start_polling():
    async with updater:
        # await updater.initialize()
        await updater.start_polling()
    # updater.idle()


async def subscribe():
    print("running telegram stub")


# application = ApplicationBuilder().token(os.environ["TELEGRAMBOTAPIKEY"]).build()

# start_handler = CommandHandler("start", start)
# application.add_handler(start_handler)

# polling_thread = threading.Thread(target=asyncio.run(start_polling()), daemon=True)
# polling_thread.start()
# # Updater.stop()
# print("finishing")
