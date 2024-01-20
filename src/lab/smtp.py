import asyncio
import os
import re
import smtplib
import textwrap
import time
from email.encoders import encode_7or8bit
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apscheduler.schedulers.background import BackgroundScheduler

import head
from common import colors, get_current_date, unified_newlines


def main(config) -> None:
    settings = config["smtp"]

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_email,
        args=(settings,),
        trigger="cron",
        day_of_week=settings.get("day", "tue"),
        hour=settings.get("hour", 8),
        minute=settings.get("minute", 0),
        timezone=settings.get("timezone", "US/Central"),
    )
    scheduler.start()
    while True:
        time.sleep(66.6)


def send_email(config):
    smtp_server = os.environ["SMTP_SERVER"]
    smtp_port = int(os.environ["SMTP_PORT"])
    sender_user = os.environ["SMTP_USER"]
    sender_email = os.environ["SMTP_EMAIL"]
    password = os.environ["SMTP_PASSWORD"]

    subject = config.get("subject")

    for subscriber in config.get("to"):
        print(
            f"{colors.RED}ONE@SMTP: {colors.WHITE}" + "sending message to " + subscriber
        )
        output = asyncio.run(
            head.ctx.prompt(
                prompt=f"""```
title: {subject}
author: {config.get('author', 'Ink')}
date: {get_current_date()}
description: {config.get('description', 'A short email and a story, written for a friend.')}
```

# {subject}
---
{config.get('prompt')}""",
                temperature=0.7,
                min_new_tokens=512,
                max_new_tokens=768,
                generation_profile="longform",
                disposition=config.get("disposition", None),
                # eos_tokens=["\n", "\n\n", "\\", ".", "?", "!"],
            )
        )

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

            server.login(sender_user, password)

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = subscriber
            message["Subject"] = Header(subject, "utf-8")

            strip_prompt = "\n".join(output.splitlines()[9:])
            unified = unified_newlines(strip_prompt.replace(r"\r\n|\r|\n", "\n"), 2)
            redacted = re.sub(
                r"http\S+",
                "$REDACTED",
                unified,
            )
            uniform = textwrap.dedent(redacted)

            prepared = MIMEText(uniform, "plain", "utf-8")
            encode_7or8bit(prepared)

            message.attach(prepared)
            server.sendmail(sender_email, subscriber, message.as_string())
            server.quit()
        except smtplib.SMTPSenderRefused as e:
            error_code = e.smtp_code
            error_msg = e.smtp_error
            print(f"Error Code: {error_code}")
            print(f"Error Message: {error_msg}")


if __name__ == "__main__":
    main(config)
