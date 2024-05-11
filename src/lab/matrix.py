import asyncio
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pprint import pprint

from nio import AsyncClient, MatrixRoom, RoomMessage, RoomMessageText

import head
from common import colors, get_identity

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


if __name__ == "__main__":
    main(config)


async def subscribe(user, password, config) -> None:
    client = AsyncClient("https://matrix.org", user)
    dt = datetime.now(timezone.utc)
    connected = int(dt.timestamp()) * 1000

    async def message_callback(room: MatrixRoom, event: RoomMessage) -> None:
        try:

            if event.server_timestamp < connected:
                return
            if event.source["content"]["msgtype"] != "m.text":
                return

            if "m.relates_to" not in event.source["content"]:
                return

            if "m.in_reply_to" not in event.source["content"]["m.relates_to"]:
                return

            profiles = config.get("profiles", [])

            event_id = event.source["content"]["m.relates_to"]["m.in_reply_to"][
                "event_id"
            ]
            response = await client.room_get_event(room.room_id, event_id)
            original_sender = response.event.source["sender"]
            if not any(profile["username"] in original_sender for profile in profiles):
                return

            profile = None
            for profile in profiles:
                if profile["username"] in original_sender:
                    profile = profile
                    break

            message = event.source["content"]["body"]
            group = re.search(r"^(?:[>].*[\n][\n])(.*)", message)
            if group:
                message = group[1]

            sender_id = get_identity(event.sender)
            head.ctx.build_context(bias=int(sender_id), message=message)

            print(colors.BLUE + "ONE@MATRIX: " + colors.WHITE + message)

            success, bias, output, seeded = await head.ctx.chat(
                priority=True, personas=profile.get("persona", [])
            )

            if success == False:
                print(output)
                return

            tag = profile.get("tag", "[BOT]")
            response = f"{tag} {output}"

            await client.room_send(
                room_id=room.room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": response},
            )

            print(colors.RED + "ONE@MATRIX: " + colors.WHITE + response)

        except Exception as e:
            logging.error(e)

    client.add_event_callback(message_callback, RoomMessage)

    await client.login(password)

    await client.sync_forever(timeout=30000)
