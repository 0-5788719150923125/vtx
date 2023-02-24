from aiogram import Dispatcher, executor, Bot, types
from utils import bc, ad, get_identity, ship
import asyncio
import logging
import head
import os

token = os.environ["TELEGRAMBOTAPIKEY"]

dp = Dispatcher(Bot(token=token))


async def polling():
    await dp.start_polling()


async def looping():
    while True:
        await asyncio.sleep(1)


@dp.message_handler()
async def chat_bot(message: types.Message):
    head.build_context(str(get_identity()) + ship + " " + message["text"])
    response = await head.gen()
    await message.answer(response[1])
    print(bc.FOLD + "PEN@TELEGRAM: " + ad.TEXT + message["text"])
    print(bc.CORE + "INK@TELEGRAM: " + ad.TEXT + response[1])


async def subscribe() -> None:
    dp.register_message_handler(chat_bot)
    await asyncio.gather(
        polling(),
        looping(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    subscribe()
