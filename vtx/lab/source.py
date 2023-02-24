from utils import ad, bc, config, get_identity, propulsion, ship
import requests
import random
import json
import head

state = None

bot = get_identity()

# Check the local GUN API for new messages
async def subscribe(channel):
    try:
        chance = config["source"][channel].get("chance", 0.33)

        roll = random.random()

        if roll > chance:
            return

        deep = requests.get("http://ctx:9666/channel/" + channel)
        state = json.loads(deep.text)
        human = get_identity()
        previous_sender = human
        if state["identifier"] == str(bot):
            previous_sender = bot

        print(bc.ROOT + "ONE@ROOT:" + ad.TEXT + " " + state["message"][:99])
        context = [
            "A human talks to Penny, a powerful Artificial Intelligence that follows the humans' instructions.",
            propulsion + str(human) + ship + " Your name is Penny.",
            propulsion + str(bot) + ship + " I am a chat bot named Penny.",
            propulsion + str(previous_sender) + ship + " " + state["message"],
        ]
        url = "http://ctx:9666/message/" + channel
        print(bc.CORE + "INK@CORE:" + ad.TEXT + " ping")
        generation = await head.gen(int(bot), context)
        myobj = {"message": generation[1], "identifier": str(bot)}
        x = requests.post(url, json=myobj, headers={"Connection": "close"})
        x.close()
        deep.close()
        print(bc.CORE + "INK@CORE:" + ad.TEXT + " " + generation[1])
        print(bc.FOLD + "PEN@FOLD:" + ad.TEXT + " pong")
    except:
        pass
