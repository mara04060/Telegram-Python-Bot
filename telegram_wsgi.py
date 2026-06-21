import asyncio
import traceback

from flask import Flask, request, abort

from telegram import Update
from bot import create_application
from credentials import WEBHOOK_SECRET_TOKEN

flask_app = Flask(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
ptb_app = create_application()
loop.run_until_complete(ptb_app.initialize())
loop.run_until_complete(ptb_app.start())


@flask_app.route("/webhook", methods=["POST"])
def webhook():
    try:
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token" )
        if secret != WEBHOOK_SECRET_TOKEN:
            abort(403)

        data = request.get_json()
        update = Update.de_json(data,ptb_app.bot )
        loop.run_until_complete(ptb_app.process_update(update))
        return "OK", 200

    except Exception:
        traceback.print_exc()
        return "ERROR", 500

application = flask_app