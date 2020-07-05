import schedule
import time
import threading
import os
import logging
import datetime
import pathlib
import concurrent.futures
import queue

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
from instapost import consumer
from discord_grabber import producer
from insta_browser import switch_to_mobile
from timeit import default_timer as timer

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
event = threading.Event()


class Pipeline(queue.Queue):
    def __init__(self):
        super().__init__(maxsize=2)

    def get_message(self, name):
        logging.debug("%s:about to get from queue", name)
        value = self.get()
        logging.debug("%s:got %d from queue", name, value)
        return value

    def set_message(self, value, name):
        logging.debug("%s:about to add %d to queue", name, value)
        self.put(value)
        logging.debug("%s:added %d to queue", name, value)


def check_discord(queue=queue, event=event):
    start = timer()
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
    try:
        producer(discord_driver, queue, event)
        end = timer()
        print(end - start)
    except (TimeoutException, NoSuchElementException) as error:
        logging.warning(error)
    #finally:
    #os.system('taskkill /f /im chromedriver.exe')


def post_driver(queue=queue, event=event):
    start = timer()
    chrome_options = Options()
    chrome_options.debugger_address = '127.0.0.1:9223'
    insta_driver = webdriver.Chrome(executable_path=INSTA_DRIVER_PATH,
                                    options=chrome_options)
    try:
        consumer(insta_driver, queue, event)
        end = timer()
        print(end - start)
        logging.info('Posted new instagram post!')
        print('posted to instagram!')
    except (TimeoutException, NoSuchElementException) as error:
        logging.warning(error)
    finally:
        switch_to_mobile(insta_driver)
        #os.system('taskkill /f /im chromedriver.exe')


format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
# logging.getLogger().setLevel(logging.DEBUG)
pipeline = queue.Queue(maxsize=2)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    executor.submit(check_discord, pipeline, event)
    executor.submit(post_driver, pipeline, event)
