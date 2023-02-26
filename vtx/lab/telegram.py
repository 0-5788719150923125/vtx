from utils import bc, ad, get_daemon, get_identity, ship
from aiogram import Dispatcher, executor, Bot, types
import asyncio
import logging
import random
import head
import os
import re


async def subscribe() -> None:

    token = os.environ["TELEGRAMBOTAPIKEY"]

    dp = Dispatcher(Bot(token=token))

    async def polling():
        await dp.start_polling()

    @dp.message_handler()
    async def chat_bot(message: types.Message):
        head.build_context(str(get_identity()) + ship + " " + message["text"])
        daemon = get_daemon(random.randint(1, 9999))["name"]
        response = await head.gen()
        sanitized = re.sub(
            r"(?:<@)(\d+\s*\d*)(?:>)",
            f"{daemon}",
            response[1],
        )

        await message.answer(sanitized)
        head.build_context(str(get_identity()) + ship + " " + sanitized)
        print(bc.FOLD + "PEN@TELEGRAM: " + ad.TEXT + message["text"])
        print(bc.CORE + "INK@TELEGRAM: " + ad.TEXT + sanitized)

    dp.register_message_handler(chat_bot)
    await asyncio.gather(
        polling(),
    )
