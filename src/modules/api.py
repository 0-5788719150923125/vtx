import asyncio
import logging

from flask import Flask, jsonify, request

import head
from common import colors


def main(config):
    app.run(debug=False, host="0.0.0.0", port=8881)


app = Flask(__name__)


@app.route("/generate/", methods=["GET", "POST"])
def generate():
    try:
        kwargs = request.get_json()
        print(f"{colors.BLUE}ONE@API:{colors.WHITE} Received a valid request via REST.")
        output = asyncio.run(head.ctx.prompt(**kwargs))
        if not output:
            raise Exception("Failed to generate an output from this API.")
    except Exception as e:
        logging.error(e)
        return jsonify(e), 400
    print(f"{colors.RED}ONE@API:{colors.WHITE} Successfully responded to REST request.")
    return jsonify({"response": output}), 200


if __name__ == "__main__":
    main(config)
