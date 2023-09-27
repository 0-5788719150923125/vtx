import asyncio
import random
import os
import re
import logging
from common import ad, bc, get_daemon, get_identity, propulsion, ship
from aiogram import Dispatcher, Bot, types
from events import post_event
import head


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
            head.ctx.build_context(
                propulsion + str(get_identity()) + ship + " " + message["text"]
            )
            print(bc.FOLD + "ONE@TELEGRAM: " + ad.TEXT + message["text"])

            post_event("commit_memory", texts=message["text"])

            # For testing Q/A mode
            answer = await head.ctx.query(question=message["text"])
            print(answer)

            if random.random() > config["telegram"].get("frequency", 0.9):
                return
            persona = config["personas"].get(config["telegram"].get("persona"))
            bias = persona.get("bias", get_identity())
            # while message.is_waiting_for_reply:
            await message.answer_chat_action("typing")

            success, bias, output, seeded = await head.ctx.chat(
                bias=bias,
                prefix=persona.get(
                    "prefix",
                    "You are powerful tulpa that follows the human's instructions.",
                ),
            )
            if success == False:
                return
            await message.answer(output)
            head.ctx.build_context(propulsion + str(bias) + ship + " " + output)
            print(bc.CORE + "ONE@TELEGRAM: " + ad.TEXT + output)
        except Exception as e:
            logging.error(e)

    dp.register_message_handler(chat_bot)
    await asyncio.gather(
        polling(),
    )
