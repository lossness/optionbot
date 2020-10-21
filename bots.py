import discord
import config
import asyncio
import os

from dotenv import load_dotenv
from discord.ext import commands
from time_utils import standard_datetime
from main_logger import logger

load_dotenv()
dev_bot = commands.Bot(command_prefix='$', description='Dev server bot')
fa_bot = commands.Bot(command_prefix='^', description='FA server bot')
FLOW_SIGNAL_CHANNEL = os.getenv("FA_SIGNAL_CHANNEL")
FLOW_SIGNAL_TOKEN = os.getenv("FA_DISCORD_TOKEN")
TRADE_CHANNEL = os.getenv("TRADE_CHANNEL")
TOKEN = os.getenv("DISCORD_TOKEN")
EVENT = config.EVENT


@dev_bot.event
async def on_ready():
    print(f'{dev_bot.user.name} has connected to Discord!')


@dev_bot.event
async def on_message(message):
    channel = message.channel

    if message.author.id == dev_bot.user.id:
        return

    if str(channel.id) != TRADE_CHANNEL:
        return

    elif message.content.startswith('$trade'):
        await channel.send(
            "Would you like to submit this trade for processing? y/n")

        def check_for_yes(m):
            return 'y' in m.content and m.channel == channel

        try:
            msg = await dev_bot.wait_for('message',
                                         check=check_for_yes,
                                         timeout=15)
        except asyncio.TimeoutError:
            return await channel.send("No trade was submitted.")

        if check_for_yes(msg):
            payload = f"{str(message.author.name)}\n{str(message.clean_content).replace('$trade', '')}"
            config.new_unprocessed_trades.put(payload)
            config.has_unprocessed_trade.release()
            await channel.send("Trade submitted for processing!")


@fa_bot.event
async def on_ready():
    print(f'{fa_bot.user.name} has connected to Discord!')
    while True:
        if config.has_new_discord_trade.acquire():
            full_message = config.new_discord_trades.get()
            in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, trader, expiration, color, date, time = full_message[
                1]
            if 'in' in in_or_out:
                in_or_out = 'buy'
            if 'out' in in_or_out:
                in_or_out = 'sell'
            trade_message = f"\n Symbol: {ticker.upper()}\n Action: {in_or_out.upper()}\n Strike: {strike_price}\n Price: {buy_price}\n Expiration: {expiration}"
            embed = discord.Embed(
                colour=discord.Colour.blurple(),
                title="Trade Alert",
                description=trade_message,
            )
            channel = fa_bot.get_channel(id=FLOW_SIGNAL_CHANNEL)
            await channel.send_embed(embed)
            config.new_discord_trades.task_done()
            logger.info(
                f"{standard_datetime()} : FA MSG POSTED : {full_message}")
            return
        else:
            EVENT.wait(1)
            return


def run_bots():
    if os.name != 'win32':
        asyncio.get_child_watcher()
    loop = asyncio.get_event_loop()
    loop.create_task(dev_bot.start(TOKEN))
    loop.create_task(fa_bot.start(FLOW_SIGNAL_TOKEN))
    return loop


def start_bot_loop(loop=run_bots()):
    try:
        loop.run_forever()
    finally:
        loop.stop()
