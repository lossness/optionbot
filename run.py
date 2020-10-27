import time
import threading
import os
import datetime
import pytz
import pathlib
import concurrent.futures
import queue
import config
import discord
import asyncio
import calendar

from collections import namedtuple
from progress.spinner import Spinner, LineSpinner
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from instapost import consumer
from grabber import DiscordGrabber
#from dev_listener import dev_bot
#from flowalerts_discord import fa_bot
from time_utils import get_time_and_day
#from insta_browser import switch_to_mobile
from main_logger import logger
from dotenv import load_dotenv
from bots import TOKEN, FLOW_SIGNAL_TOKEN, fa_bot, dev_bot
load_dotenv()
EVENT = config.EVENT
DEBUG = config.DEBUG
GRABBER = DiscordGrabber()

if os.name == 'nt':
    # DISCORD_DRIVER_PATH = os.path.join(os.path.curdir, 'selenium-utilities',
    #                                   'windows', 'discord',
    #                                   'chromedriver.exe')
    #INSTA_DRIVER_PATH = os.path.join(os.path.curdir, 'selenium-utilities',
    #                                 'windows', 'insta', 'chromedriver.exe')
    DISCORD_DRIVER_PATH = os.getenv('WINDOWS_DISCORD_DRIVER_PATH')
    INSTA_DRIVER_PATH = os.getenv('WINDOWS_INSTA_DRIVER_PATH')
if os.name == 'posix':
    DISCORD_DRIVER_PATH = r'/usr/bin/chromedriver'
    INSTA_DRIVER_PATH = r'/usr/bin/chromedriver'


# Market hours are 930-4pm est 9:30 -> 16:00 24hr format
def is_market_open():
    if DEBUG is False:
        the_time, day_of_the_week = get_time_and_day()
        market_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        #market_days = ['Saturday', 'Sunday']
        if datetime.time(9, 30, 00, 000000) <= the_time <= datetime.time(
                16, 3, 00, 000000) and day_of_the_week in market_days:
            return True
        else:
            return False
    else:
        return True


# def initiate_discord_driver():
#     chrome_options = Options()
#     # chrome_options.add_argument("--window-size=1920,1080")
#     # chrome_options.add_argument("--disable-extensions")
#     # chrome_options.add_argument("--start-maximized")
#     # chrome_options.add_argument("--headless")
#     # chrome_options.add_argument("--disable-gpu")
#     # chrome_options.add_argument("--disable-dev-shm-usage")
#     # chrome_options.add_argument("--no-sandbox")
#     # chrome_options.add_argument("--ignore-certificate-errors")
#     chrome_options.add_argument('--log-level=3')
#     chrome_options.debugger_address = '127.0.0.1:9222'
#     discord_driver = webdriver.Chrome(executable_path=DISCORD_DRIVER_PATH,
#                                       options=chrome_options)
#     try:
#         element = discord_driver.find_elements_by_xpath(
#             "//*[@role='group']")[-1]
#         element.location_once_scrolled_into_view

#     except (NoSuchElementException, TimeoutError) as error:
#         logger.fatal(f'{error}\n COULD NOT FIND LAST MESSAGE')
#     finally:
#         return discord_driver


def check_discord():
    listen_spinner = Spinner('Listening for new messages ')
    while True:
        if is_market_open():
            try:
                GRABBER.producer()

            except (TimeoutException, NoSuchElementException) as error:
                logger.fatal(f'{error}\n COULD NOT FIND LAST MESSAGE')
                continue

            finally:
                listen_spinner.next()
        else:
            listen_spinner.next()
            EVENT.wait(3)

    logger.fatal("INFINITE CHECK_DISCORD LISTENER GOT OUT THE LOOP FUCK")
    print("It should never reach here! check_discord")


def check_for_unprocessed_messages():
    while True:
        if is_market_open():
            try:
                GRABBER.processor()
            except:
                continue
        else:
            EVENT.wait(3)
    logger.fatal(
        "INFINITE CHECK_FOR_UNPROCESSED_MESSAGES GOT OUT OF THE LOOP FUCK")
    print(
        "Infinite loop exited in check_for_unprocessed_messages! Its become setinent!"
    )


def post_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--ignore-certificate-errors")
    # chrome_options.add_argument("--log-level=3")
    chrome_options.debugger_address = '127.0.0.1:9223'
    insta_driver = webdriver.Chrome(executable_path=INSTA_DRIVER_PATH,
                                    options=chrome_options)
    while True:
        try:
            consumer(insta_driver)
        except (TimeoutException, NoSuchElementException) as error:
            logger.warning(error)
            continue
            #os.system('taskkill /f /im chromedriver.exe')


# def bot_main(bot1=dev_bot, bot2=fa_bot):
#     # First, we must attach an event signalling when the bot has been
#     # closed to the client itself so we know when to fully close the event loop.

#     Entry = namedtuple('Entry', 'client event')
#     entries = [
#         Entry(bot=bot1, event=asyncio.Event()),
#         Entry(bot=bot2, event=asyncio.Event())
#     ]

#     # Then, we should login to all our clients and wrap the connect call
#     # so it knows when to do the actual full closure

#     loop = asyncio.get_event_loop()

#     async def login():
#         for e in entries:
#             await e.bot.run()

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

#     # finally, we close the event loop
#     loop.close()

# def bot_start():
#     if os.name != 'win32':
#         asyncio.get_child_watcher()
#     loop = asyncio.get_event_loop()
#     loop.create_task(dev_bot)
#     loop.create_task(fa_bot)
#     return loop

# def bot_loop_start(loop=bot_start()):
#     try:
#         loop.run_forever()
#     finally:
#         loop.stop()

Entry = namedtuple('Entry', 'client event')
entries = [
    Entry(client=fa_bot, event=asyncio.Event()),
    Entry(client=dev_bot, event=asyncio.Event())
]


# Then, we should login to all our clients and wrap the connect call
# so it knows when to do the actual full closure
async def login():
    for e in entries:
        if e.client.description == "FA server bot":
            await e.client.login(FLOW_SIGNAL_TOKEN)
        elif e.client.description == "Dev server bot":
            await e.client.login(TOKEN)


async def wrapped_connect(entry):
    try:
        await entry.client.connect()
    except Exception as e:
        await entry.client.close()
        print('We got an exception: ', e.__class__.__name__, e)
        entry.event.set()


# actually check if we should close the event loop:
async def check_close():
    futures = [e.event.wait() for e in entries]
    await asyncio.wait(futures)


def get_the_loop():
    if os.name != 'win32':
        asyncio.get_child_watcher()
    loop = asyncio.get_event_loop()
    return loop


# here is when we actually login
def run_loop(loop=get_the_loop()):
    loop.run_until_complete(login())

    # now we connect to every client
    for entry in entries:
        loop.create_task(wrapped_connect(entry))

    # now we're waiting for all the clients to close
    loop.run_until_complete(check_close())

    loop.close()


def main():
    scraper = threading.Thread(target=check_discord)
    poster = threading.Thread(target=post_driver)
    processor = threading.Thread(target=check_for_unprocessed_messages)
    start_bots = threading.Thread(target=run_loop, daemon=True)

    scraper.start()
    processor.start()
    poster.start()
    start_bots.start()

    config.new_trades.join()
    config.new_unprocessed_trades.join()
    config.new_discord_trades.join()

    scraper.join()
    processor.join()
    poster.join()
    start_bots.join()


# if os.name != 'win32':
#     asyncio.get_child_watcher()
# loop = asyncio.get_event_loop()
# loop.create_task(dev_bot)
# loop.create_task(fa_bot)
# try:
#     loop.run_forever()
# finally:
#     loop.stop()

if __name__ == "__main__":
    main()

# format = "%(asctime)s: %(message)s"
# logger.basicConfig(format=format, level=loggej.INFO, datefmt="%H:%M:%S")
# # logger.getLogger().setLevel(loggej.DEBUG)
# new_trades = queue.Queue(maxsize=4)
# with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
#     executor.submit(check_discord, new_trades, event)
#     executor.submit(post_driver, new_trades, event)

#     time.sleep(0.1)
#     logger.info("Main: about to set event")
#     event.set()

# ERROR CHECKING FUNCTIONS BELOW ########

# def discord_error_checker():
#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")
#     # chrome_options.add_argument('--disable-gpu')
#     # chrome_options.add_argument('--log-level=3')
#     chrome_options.debugger_address = '127.0.0.1:9222'
#     discord_driver = webdriver.Chrome(executable_path=DISCORD_DRIVER_PATH,
#                                       options=chrome_options)
#     try:
#         error_producer_classic(discord_driver)
#     except (TimeoutException, NoSuchElementException) as error:
#         print(f"{error}")
