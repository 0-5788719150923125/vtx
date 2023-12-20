import asyncio
import logging

from flask import Flask, jsonify, request

import head
from common import colors


def main(config):
    app.run(debug=False, host="0.0.0.0", port=5010)


app = Flask(__name__)


@app.route("/generate")
def generate():
    kwargs = request.get_json()
    print(f"{colors.BLUE}ONE@API:{colors.WHITE} Received a valid prompt to this API.")
    output = asyncio.run(head.ctx.prompt(**kwargs))
    if not output:
        response = "Failed to generate an output from this API."
        logging.error(response)
        return jsonify(response), 400
    print(f"{colors.RED}ONE@API:{colors.WHITE} {output}")
    return jsonify({"response": output}), 200


if __name__ == "__main__":
    main(config)
