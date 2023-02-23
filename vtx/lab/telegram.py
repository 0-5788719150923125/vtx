import asyncio
from aiogram import Bot, Dispatcher, executor, types
from utils import config
import os

token = os.environ["TELEGRAMBOTAPIKEY"]
bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


async def subscribe(loop):
    # Register message handler function
    dp.register_message_handler(send_welcome, commands=["start", "help"])
    # Start the bot
    try:
        await executor.start_polling(dp)
        # loop.run_forever()
    except Exception as e:
        print(e)
