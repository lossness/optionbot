import discord
import config
import asyncio
import os

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
bot = commands.Bot(command_prefix='$')
TRADE_CHANNEL = os.getenv("TRADE_CHANNEL")
TOKEN = os.getenv("DISCORD_TOKEN")


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_message(message):
    channel = message.channel
    if message.author == bot.user or message.author.bot is True:
        return
    if str(channel.id) != TRADE_CHANNEL:
        return
    elif message.author != bot.user:
        await channel.send(
            "Would you like to submit this trade for processing? y/n")
        try:
            msg = await bot.wait_for('message', timeout=15)

            def check_for_yes(m):
                return 'y' in m.content and m.channel == channel

            if check_for_yes(msg):
                payload = f"{str(message.author.name)}\n{str(message.clean_content)}"
                config.new_unprocessed_trades.put(payload)
                config.has_unprocessed_trade.release()
                await channel.send("Trade submitted for processing!")
                return
        except asyncio.TimeoutError:
            await channel.send("Alright then.")


async def bot_async_start():
    await bot.start(TOKEN)
