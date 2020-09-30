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


def discord_bot():
    @bot.event
    async def on_ready():
        print(f'{bot.user.name} has connected to Discord!')

    @bot.event
    async def on_message(message):
        channel = message.channel
        mentioned_users_int = message.raw_mentions
        mentioned_users_str = str(message.raw_mentions)
        await bot.process_commands(message)
        if message.author == bot.user:
            return
        if str(channel) != TRADE_CHANNEL:
            return
        else:
            try:
                await channel.send(
                    "Would you like to submit this trade for processing? y/n?")

                def check_for_yes(m):
                    return 'y' in m.content and m.channel == channel

                msg = await bot.wait_for('message',
                                         check=check_for_yes,
                                         timeout=15)
                if msg is not None:
                    payload = f"{str(message.author)}\n{str(msg)}"
                    config.new_unprocessed_trades.put(payload)
                    config.has_unprocessed_trade.release()
            except asyncio.TimeoutError:
                await channel.send("Alright then.")
            finally:
                return

    bot.run(TOKEN)
