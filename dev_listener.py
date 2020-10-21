import discord
import config
import asyncio
import os

from dotenv import load_dotenv
from discord.ext import commands
from time_utils import standard_datetime
from main_logger import logger

load_dotenv()
bot = commands.Bot(command_prefix='$')
TRADE_CHANNEL = os.getenv("TRADE_CHANNEL")
TOKEN = os.getenv("DISCORD_TOKEN")
EVENT = config.EVENT


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_message(message):
    channel = message.channel

    if message.author.id == bot.user.id:
        return

    if str(channel.id) != TRADE_CHANNEL:
        return

    elif message.content.startswith('$trade'):
        await channel.send(
            "Would you like to submit this trade for processing? y/n")

        def check_for_yes(m):
            return 'y' in m.content and m.channel == channel

        try:
            msg = await bot.wait_for('message',
                                     check=check_for_yes,
                                     timeout=15)
        except asyncio.TimeoutError:
            return await channel.send("No trade was submitted.")

        if check_for_yes(msg):
            payload = f"{str(message.author.name)}\n{str(message.clean_content).replace('$trade', '')}"
            config.new_unprocessed_trades.put(payload)
            config.has_unprocessed_trade.release()
            await channel.send("Trade submitted for processing!")


async def bot_async_start():
    await bot.start(TOKEN)
