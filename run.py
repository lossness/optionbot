import time
import threading
import os
import datetime
import pytz
import pathlib
import concurrent.futures
import queue
import config

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
from discord_grabber import DiscordGrabber
#from insta_browser import switch_to_mobile
from main_logger import logger
from dotenv import load_dotenv

load_dotenv()
EVENT = config.EVENT

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


def time_now():
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    return ast_now.time()


# Market hours are 930-4pm est 9:30 -> 16:00 24hr format
def is_market_open():
    if datetime.time(0, 30, 00, 000000) <= time_now() <= datetime.time(
            23, 59, 00, 000000):
        return True
    else:
        return False


def check_discord():
    chrome_options = Options()
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument('--log-level=3')
    chrome_options.debugger_address = '127.0.0.1:9222'
    discord_driver = webdriver.Chrome(executable_path=DISCORD_DRIVER_PATH,
                                      options=chrome_options)
    try:
        element = discord_driver.find_elements_by_xpath(
            "//*[@role='group']")[-1]
        element.location_once_scrolled_into_view

    except (NoSuchElementException, TimeoutError) as error:
        logger.fatal(f'{error}\n COULD NOT FIND LAST MESSAGE')
    listen_spinner = Spinner('Listening for new messages ')

    grabber = DiscordGrabber(driver=discord_driver)
    while True:
        if is_market_open():
            try:
                grabber.producer()

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


def main():
    scraper = threading.Thread(target=check_discord)
    poster = threading.Thread(target=post_driver)

    scraper.start()
    poster.start()

    config.new_trades.join()

    scraper.join()
    poster.join()


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
