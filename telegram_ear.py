import os
import json
import telegram

from dotenv import load_dotenv

load_dotenv()
T_BOT_TOKEN = os.getenv("T_BOT_TOKEN")
CHANNEL = 'https://t.me/peepschain'
bot = telegram.Bot(token=str(T_BOT_TOKEN))
