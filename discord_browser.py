import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BROWSER = os.getenv('DISCORD_CHROME')
os.startfile(DISCORD_BROWSER)
