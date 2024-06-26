import asyncio
import logging
import os
import random
import re

from aiogram import Bot, Dispatcher, types

import head
from common import colors, get_daemon, get_identity


def main(config):
    asyncio.run(client(config))


if __name__ == "__main__":
    main(config)


async def client(config) -> None:
    token = os.environ["TELEGRAMBOTAPIKEY"]

    dp = Dispatcher(Bot(token=token))

    async def polling():
        await dp.start_polling()

    @dp.message_handler()
    async def chat_bot(message: types.Message):
        try:
            sender_id = message["from"]["id"]
            head.ctx.build_context(
                bias=int(get_identity(sender_id)), message=message["text"]
            )
            print(colors.BLUE + "ONE@TELEGRAM: " + colors.WHITE + message["text"])

            # post_event("commit_memory", texts=message["text"])

            if random.random() > config["telegram"].get("frequency", 0.9):
                return
            persona = config["telegram"].get("persona", [])

            # while message.is_waiting_for_reply:
            await message.answer_chat_action("typing")

            success, bias, output, seeded = await head.ctx.chat(
                personas=persona, priority=True
            )
            if not success:
                return

            await message.answer(output)
            head.ctx.build_context(bias=int(bias), message=output)
            print(colors.RED + "ONE@TELEGRAM: " + colors.WHITE + output)
        except Exception as e:
            logging.error(e)

    dp.register_message_handler(chat_bot)
    await asyncio.gather(
        polling(),
    )
