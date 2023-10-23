import asyncio
import logging
import os
import random
import re

from aiogram import Bot, Dispatcher, types

import head
from common import ad, bc, get_daemon, get_identity
from events import post_event


def main(config):
    asyncio.run(client(config))


if __name__ == "main":
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
            print(bc.FOLD + "ONE@TELEGRAM: " + ad.TEXT + message["text"])

            post_event("commit_memory", texts=message["text"])

            if random.random() > config["telegram"].get("frequency", 0.9):
                return
            persona = config["telegram"].get("persona", [])

            # while message.is_waiting_for_reply:
            await message.answer_chat_action("typing")

            if "!Q" in message["text"]:
                prompt = message["text"].replace("!Q", "")
                bias = get_identity()
                output = await head.ctx.query(question=prompt)
            else:
                success, bias, output, seeded = await head.ctx.chat(personas=persona)
                if success == False:
                    return
            await message.answer(output)
            head.ctx.build_context(bias=int(bias), message=output)
            print(bc.CORE + "ONE@TELEGRAM: " + ad.TEXT + output)
        except Exception as e:
            logging.error(e)

    dp.register_message_handler(chat_bot)
    await asyncio.gather(
        polling(),
    )
