import os
import time
import re
import threading
import asyncio
from datetime import datetime
from pprint import pprint
from nio import AsyncClient, MatrixRoom, RoomMessage, RoomMessageText
import logging
import head
from common import ad, bc, get_identity, propulsion, ship

logging.getLogger("nio").setLevel(logging.WARNING)


def main(config):
    tasks = {}
    while True:
        for task in tasks.copy():
            if not tasks[task].is_alive():
                del tasks[task]

        if "matrix" not in tasks:
            user = os.environ["MATRIXUSER"]
            password = os.environ["MATRIXPASSWORD"]
            t = threading.Thread(
                target=asyncio.run,
                args=(subscribe(user, password, config["matrix"]),),
                daemon=True,
                name="matrix",
            )
            tasks[t.name] = t
            t.start()

        time.sleep(6.66)


if __name__ == "main":
    main(config)


async def subscribe(user, password, config) -> None:
    client = AsyncClient("https://matrix.org", user)
    dt = datetime.utcnow()
    connected = int(dt.timestamp()) * 1000

    async def message_callback(room: MatrixRoom, event: RoomMessage) -> None:
        try:
            if event.server_timestamp < connected:
                return
            if event.source["content"]["msgtype"] != "m.text":
                return

            message = event.source["content"]["body"]

            group = re.search(r"^(?:[>].*[\n][\n])(.*)", message)
            if group:
                message = group[1]

            identity = get_identity(event.sender)
            bias = 806051627198709760

            if event.sender == client.user:
                identity = str(bias)

            head.ctx.build_context(propulsion + identity + ship + " " + message)

            if "Architect" not in message:
                if "m.relates_to" in event.source["content"]:
                    if "m.in_reply_to" not in event.source["content"]["m.relates_to"]:
                        return
                    if "luciferianink" not in event.source["content"]["body"]:
                        return
                else:
                    return

            print(bc.FOLD + "ONE@MATRIX: " + ad.TEXT + message)

            task = asyncio.create_task(client.room_typing(room.room_id))
            await asyncio.gather(task)

            success, bias, output, seeded = await head.ctx.chat(
                prefix="I am Ryan's bot, and I am connected to GUN's Matrix room.",
                bias=bias,
            )

            if success == False:
                print(output)
                return

            response = f"[BOT] {output}"

            await client.room_send(
                room_id=room.room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": response},
            )

            print(bc.CORE + "ONE@MATRIX: " + ad.TEXT + response)

        except Exception as e:
            logging.error(e)

    client.add_event_callback(message_callback, RoomMessage)

    await client.login(password)

    await client.sync_forever(timeout=30000)
