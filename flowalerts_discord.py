# import discord
# import config
# import asyncio
# import os

# from dotenv import load_dotenv
# from discord.ext import commands
# from time_utils import standard_datetime
# from main_logger import logger

# load_dotenv()
# bot = commands.Bot(command_prefix='$')
# FLOW_SIGNAL_CHANNEL = os.getenv("TRADE_CHANNEL")
# FLOW_SIGNAL_TOKEN = os.getenv("DISCORD_TOKEN")
# EVENT = config.EVENT

# @bot.event
# async def on_ready():
#     print(f'{bot.user.name} has connected to Discord!')
#     while True:
#         if config.has_new_discord_trade.acquire():
#             full_message = config.new_discord_trades.get()
#             in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, trader, expiration, color, date, time = full_message[
#                 1]
#             if 'in' in in_or_out:
#                 in_or_out = 'buy'
#             if 'out' in in_or_out:
#                 in_or_out = 'sell'
#             trade_message = f"\n Symbol: {ticker.upper()}\n Action: {in_or_out.upper()}\n Strike: {strike_price}\n Price: {buy_price}\n Expiration: {expiration}"
#             embed = Embed(
#                 title="Trade Alert",
#                 description=trade_message,
#             )
#             channel = bot.get_channel(id=753068137225781343)
#             await channel.send_embed(embed)
#             config.new_discord_trades.task_done()
#             logger.info(f"{standard_datetime()} : {full_message}")
#             return
#         else:
#             EVENT.wait(1)
#             return

# async def bot_async_start():
#     await bot.start(TOKEN)