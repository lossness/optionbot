import time
import threading
import os
import logging
import datetime
import pathlib
import concurrent.futures
import queue
import config

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
from instapost import consumer
from discord_grabber import producer
from insta_browser import switch_to_mobile

load_dotenv()
DISCORD_DRIVER_PATH = os.getenv("DISCORD_DRIVER_PATH")
INSTA_DRIVER_PATH = os.getenv("INSTA_DRIVER_PATH")
DISCORD_USERNAME = os.getenv("DISCORD_USERNAME")
DISCORD_PW = os.getenv("DISCORD_PW")
CHROME = os.getenv("CHROME")
LIVE_USERNAME = os.getenv("LIVE_USERNAME")
LIVE_PW = os.getenv("LIVE_PW")
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PW = os.getenv("INSTA_PASSWORD")
CHROME_INSTA = os.getenv("INSTACHROME")
PATH = pathlib.Path.cwd()


def check_discord():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--log-level=3')
    chrome_options.debugger_address = '127.0.0.1:9222'
    discord_driver = webdriver.Chrome(executable_path=DISCORD_DRIVER_PATH,
                                      options=chrome_options)
    #driver.get(
    #    'https://discord.com/channels/290278814217535489/699253100174770176')
    # parse(find_new_messages(driver))
    while True:
        try:
            producer(discord_driver)
        except (TimeoutException, NoSuchElementException) as error:
            logging.warning(error)
            continue
        #finally:
        #os.system('taskkill /f /im chromedriver.exe')


def post_driver():
    chrome_options = Options()
    chrome_options.debugger_address = '127.0.0.1:9223'
    insta_driver = webdriver.Chrome(executable_path=INSTA_DRIVER_PATH,
                                    options=chrome_options)
    while True:
        try:
            consumer(insta_driver)
        except (TimeoutException, NoSuchElementException) as error:
            logging.warning(error)
            continue
            #os.system('taskkill /f /im chromedriver.exe')


scraper = threading.Thread(target=check_discord)
poster = threading.Thread(target=post_driver)

scraper.start()
poster.start()

config.new_trades.join()

scraper.join()
poster.join()

# format = "%(asctime)s: %(message)s"
# logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
# # logging.getLogger().setLevel(logging.DEBUG)
# new_trades = queue.Queue(maxsize=4)
# with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
#     executor.submit(check_discord, new_trades, event)
#     executor.submit(post_driver, new_trades, event)

#     time.sleep(0.1)
#     logging.info("Main: about to set event")
#     event.set()
