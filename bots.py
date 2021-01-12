import discord
import config
import asyncio
import os
import csv

from dotenv import load_dotenv
from discord.ext import commands
from time_utils import standard_datetime, prune_members_window
from main_logger import logger
from collections import namedtuple
from instapost import force_make_image, make_image
from db_utils import prune_completed_trades

load_dotenv()
intents = discord.Intents.default()
intents.members = True
dev_bot = commands.Bot(command_prefix='$', description='Dev server bot')
fa_bot = commands.Bot(command_prefix='!',
                      description='FA server bot',
                      intents=intents)
FLOW_SIGNAL_CHANNEL = os.getenv("FA_SIGNAL_CHANNEL")
FLOW_SIGNAL_TOKEN = os.getenv("FA_DISCORD_TOKEN")
TRADE_CHANNEL = os.getenv("TRADE_CHANNEL")
MEMBERS_PATH = os.getenv("ACTIVE_DISCORD_MEMBERS_PATH")
INSTA_MEMBERS_PATH = os.getenv("ACTIVE_INSTA_MEMBERS_PATH")
TOKEN = os.getenv("DISCORD_TOKEN")
EVENT = config.EVENT
DEBUG = config.DEBUG


@dev_bot.event
async def on_ready():
    print(f'{dev_bot.user.name} has connected to Discord!')


@dev_bot.command()
async def trade(message):
    try:
        channel = message.channel

        if message.author.id == dev_bot.user.id:
            return

        if str(channel.id) != TRADE_CHANNEL:
            return

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
            payload = f"{str(message.author.name)}\n{str(message.message.clean_content).replace('$trade', '')}"
            config.new_unprocessed_trades.put(payload)
            config.has_unprocessed_trade.release()
            await channel.send("Trade submitted for processing!")
    except Exception:
        pass


@dev_bot.command()
async def post(message):
    try:
        image_colors = {
            'red': 'FA1',
            'orange': 'FA2',
            'yellow': 'FA3',
            'pink': 'FA4',
            'purple': 'FA5',
            'teal': 'FA6',
            'green': 'FA7',
            'darkblue': 'FA8',
            'lightgreen': 'FA9',
            'blue': 'FA10',
            'black': 'FA11',
            'gray': 'FA12',
            'grey': 'FA12',
            'darkred': 'FA13',
            'brown': 'FA14'
        }
        trade_message = message.message.clean_content
        trade_message = trade_message.replace('$post ', '')
        split_message = trade_message.split('-')
        split_message[-1] = image_colors.get(split_message[-1])
        split_message += ['force_trade']
        trade_tuple = tuple(split_message)
        filename = force_make_image(trade_tuple)
        split_message += [filename]
        trade_tuple = tuple(split_message)
        config.new_trades.put(trade_tuple)
        config.has_trade.release()
    except Exception:
        pass
    await message.send("Trade sent for posting!")


@fa_bot.event
async def on_ready():
    print(f'{fa_bot.user.name} has connected to Discord!')
    fa_bot.loop.create_task(listener())
    #fa_bot.loop.create_task(prune_members())


@fa_bot.event
async def listener():
    while True and DEBUG is False:
        if config.has_new_discord_trade.acquire(timeout=2):
            full_message = config.new_discord_trades.get()
            in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, trader, expiration, color, date, time = full_message[
                1]
            if 'in' in in_or_out:
                in_or_out = 'buy'
            if 'out' in in_or_out:
                in_or_out = 'sell'
            embed = discord.Embed(title="Signal", colour=0xffff80)
            embed.set_author(
                name="FlowAlerts",
                icon_url=
                "https://www.flowalerts.com/wp-content/uploads/2020/09/cropped-Untitled-3-32x32.png"
            )
            embed.add_field(name="Ticker:",
                            value=f"{ticker.upper()}",
                            inline=False)
            embed.add_field(name="Type:",
                            value=f"{call_or_put.upper()}",
                            inline=False)
            embed.add_field(name="Position:",
                            value=f"{in_or_out.upper()}",
                            inline=False)
            embed.add_field(name="Strike:",
                            value=f"{strike_price}",
                            inline=False)
            embed.add_field(name="Price:", value=f"${buy_price}", inline=False)
            embed.add_field(name="Expiration:",
                            value=f"{expiration}",
                            inline=False)
            embed.set_footer(
                text=
                "This is not investment advice, all data on this post represents a personal trade made public for others to see. Trading and investing carries a HIGH LEVEL OF RISK, you could lose some or all of your investment. Trading commodities or any other financial instrument may not be suitable for all traders. We accept no liability for any losses or damages you may incur—this means that you alone are responsible for your actions in any trading or investing activities. "
            )
            channel = fa_bot.get_channel(id=int(FLOW_SIGNAL_CHANNEL))
            await channel.send(embed=embed)
            config.new_discord_trades.task_done()
            logger.info(
                f"{standard_datetime()} : FA MSG POSTED : {full_message}")
            prune_completed_trades()
            make_image(full_message[1])
        else:
            await asyncio.sleep(2)


@fa_bot.command(pass_context=True)
@commands.cooldown(1, 30, commands.BucketType.member)
async def verify(ctx):
    member = ctx.author
    role = discord.utils.get(member.guild.roles, name='Members')
    with open(f"{MEMBERS_PATH}.txt", "r") as f:
        lines = f.readlines()
        for num, line in enumerate(lines):
            line = line.replace("\n", "")
            lines[num] = line.lower()
        if ctx.author.name.lower() in lines:
            await discord.Member.add_roles(member, role)
            await ctx.send("You have been added to Members!")
        else:
            await ctx.send(
                "Hmm.. you are not on the list. Please register on flowalerts.com and make sure you provide a discord username!"
            )


@fa_bot.command()
async def admin_verify(ctx):
    with open(f"{INSTA_MEMBERS_PATH}.txt", "r") as f:
        lines = f.readlines()
        for num, line in enumerate(lines):
            line = line.replace("\n", "")
            lines[num] = line.lower()
        message = ctx.message.clean_content.split(" ")
        message = message[1]
        if message.lower() in lines:
            await ctx.send("Verified user.")
        else:
            await ctx.send("Not an active user.")


@verify.error
async def verify_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("Try again in a couple minutes..")


@verify.error
async def verify_command_not_found(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("You typed the command wrong! Please type !verify")


@fa_bot.event
async def prune_members():
    while True:
        if prune_members_window():
            try:
                discord_users = []
                valid_members = []
                with open('active_users.csv', mode='r') as csv_file:
                    user_data = csv.reader(csv_file, delimiter=',')
                    for line in user_data:
                        if '#' in line[3]:
                            line[3] = line[3].split("#")
                            line[3].pop(1)
                            line[3] = line[3][0]
                        if line[3] != "":
                            valid_members.append(line[3])
                    valid_members.remove('discord')
                server = fa_bot.get_guild(771606400181862400)
                role = discord.utils.get(server.roles, name='Members')
                for member in server.members:
                    if role in member.roles:
                        discord_users.append(member)
                for privledged_member in discord_users:
                    if privledged_member.name.lower() not in valid_members:
                        await privledged_member.remove_roles(role)
                        print(
                            f"{privledged_member.name} removed from discord members list"
                        )
            except:
                pass
            finally:
                await asyncio.sleep(650)
        else:
            await asyncio.sleep(3)


# # First, we must attach an event signalling when the bot has been
# # closed to the client itself so we know when to fully close the event loop.
# def start_bot_loop(loop):
#     Entry = namedtuple('Entry', 'client event')
#     entries = [
#         Entry(client=fa_bot, event=asyncio.Event()),
#         Entry(client=dev_bot, event=asyncio.Event())
#     ]

#     # Then, we should login to all our clients and wrap the connect call
#     # so it knows when to do the actual full closure
#     async def login():
#         for e in entries:
#             if e.client.description == "FA server bot":
#                 await e.client.login(FLOW_SIGNAL_TOKEN)
#             elif e.client.description == "Dev server bot":
#                 await e.client.login(TOKEN)

#     async def wrapped_connect(entry):
#         try:
#             await entry.client.connect()
#         except Exception as e:
#             await entry.client.close()
#             print('We got an exception: ', e.__class__.__name__, e)
#             entry.event.set()

#     # actually check if we should close the event loop:
#     async def check_close():
#         futures = [e.event.wait() for e in entries]
#         await asyncio.wait(futures)

#     # here is when we actually login
#     loop.run_until_complete(login())

#     # now we connect to every client
#     for entry in entries:
#         loop.create_task(wrapped_connect(entry))

#     # now we're waiting for all the clients to close
#     loop.run_until_complete(check_close())

# def run_bots():
#     if os.name != 'win32':
#         asyncio.get_child_watcher()
#     loop = asyncio.get_event_loop()
#     loop.create_task(dev_bot.start(TOKEN))
#     loop.create_task(fa_bot.start(FLOW_SIGNAL_TOKEN))
#     return loop

# def start_bot_loop(loop=run_bots()):
#     try:
#         loop.run_forever()
#     finally:
#         loop.stop()
