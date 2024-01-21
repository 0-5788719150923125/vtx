import requests


def send_webhook():
    data = {
        "username": "Luciferian Ink",
        "avatar_url": "https://cdn.discordapp.com/avatars/957758215075004416/1c79616ea084910675e5df259bea1cf5.webp",
        "content": "For immediate disclosure...",
        "embeds": [
            {
                "title": "This is a Title",
                "description": "This is content...",
                "url": "https://src.eco",
                "thumbnail": {
                    "url": "https://styles.redditmedia.com/t5_2sqtn6/styles/communityIcon_xfdgcz8156751.png",
                },
                "footer": {
                    "text": "/r/TheInk",
                },
            }
        ],
    }

    webhook_url = (
        "https://discord.com/api/webhooks/1176415382937018399/QmnZFmAFz80U......."
    )

    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        logging.error(response)


send_webhook()
