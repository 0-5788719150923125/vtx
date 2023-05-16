import asyncio
import logging
import random
import os
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
from aiogram import Dispatcher, executor, Bot, types
import head


async def subscribe() -> None:
    token = os.environ["TELEGRAMBOTAPIKEY"]

    dp = Dispatcher(Bot(token=token))

    async def polling():
        await dp.start_polling()

    @dp.message_handler()
    async def chat_bot(message: types.Message):
        head.build_context(
            propulsion + str(get_identity()) + ship + " " + message["text"]
        )
        response = await head.gen(bias=config["telegram"].get("bias", None))
        print(bc.FOLD + "PEN@TELEGRAM: " + ad.TEXT + message["text"])
        if response[0] == "error":
            return
        await message.answer(response[1])
        head.build_context(propulsion + str(get_identity()) + ship + " " + response[1])
        print(bc.CORE + "INK@TELEGRAM: " + ad.TEXT + response[1])

    dp.register_message_handler(chat_bot)
    await asyncio.gather(
        polling(),
    )
