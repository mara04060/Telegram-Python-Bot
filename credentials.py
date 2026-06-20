import dotenv
import os

dotenv.load_dotenv()

ChatGPT_TOKEN = os.environ['CHATGPT_TOKEN']
BOT_TOKEN = os.environ['BOT_TOKEN']

BOT_MODE = os.getenv("BOT_MODE", "POLLING")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8443))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
