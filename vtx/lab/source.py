from utils import bc, config, get_identity, propulsion, ship
import requests
import random
import json
import head

state = None

# Check the local GUN API for new messages
async def subscribe(channel):

    chance = config["source"][channel].get("chance", 0.33)

    roll = random.random()

    if roll > chance:
        return

    deep = requests.get("http://ctx:9666/channel")
    state = json.loads(deep.text)
    bot = get_identity()
    bias = get_identity()
    print(bc.ROOT + "ONE@ROOT:" + bc.ENDC + " " + state["message"][:99])
    context = [
        "A human talks to Penny, a powerful Artificial Intelligence that follows the humans' instructions.",
        propulsion + str(bias) + ship + " Your name is Penny.",
        propulsion + str(bot) + ship + " I am a chat bot named Penny.",
        propulsion + str(bias) + ship + " " + state["message"],
    ]
    url = "http://ctx:9666/message"
    print(bc.CORE + "INK@CORE:" + bc.ENDC + " ping")
    generation = await head.gen(int(bias), context)
    myobj = {"message": generation[1], "identifier": str(bias)}
    x = requests.post(url, json=myobj, headers={"Connection": "close"})
    x.close()
    deep.close()
    print(bc.ROOT + "ONE@ROOT:" + bc.ENDC + " " + generation[1])
    print(bc.FOLD + "PEN@FOLD:" + bc.ENDC + " pong")
