import asyncio
import logging
from threading import Thread

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)


@app.route("/")
def home():
    # startup message for the web server, can be customized or removed
    return "Bot is running!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# Suppress Flask and Werkzeug logging to avoid cluttering the console
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("flask.app").setLevel(logging.ERROR)

import asyncio

_bot_loop = None


def set_loop(loop):
    global _bot_loop
    _bot_loop = loop


def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, _bot_loop)
    return future.result(timeout=10)
