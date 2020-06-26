import schedule
import time
import threading
import os
import logging
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from discord_grabber import parse, find_new_messages
from timeit import default_timer as timer

load_dotenv()
DRIVER_PATH = os.getenv("DRIVER_PATH")
DISCORD_USERNAME = os.getenv("DISCORD_USERNAME")
DISCORD_PW = os.getenv("DISCORD_PW")
CHROME = os.getenv("CHROME")
LIVE_USERNAME = os.getenv("LIVE_USERNAME")
LIVE_PW = os.getenv("LIVE_PW")
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PW = os.getenv("INSTA_PASSWORD")
CHROME_INSTA = os.getenv("INSTACHROME")


def check_discord():
    start = timer()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.debugger_address = '127.0.0.1:9222'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH,
                              options=chrome_options)
    #driver.get(
    #    'https://discord.com/channels/290278814217535489/699253100174770176')
    parse(find_new_messages(driver))
    end = timer()
    print(end - start)


# def check_discord():
#     options = webdriver.ChromeOptions()
#     options.add_argument("start-maximized")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
#     driver.execute_cdp_cmd(
#         "Page.addScriptToEvaluateOnNewDocument", {
#             "source":
#             """
#         Object.defineProperty(navigator, 'webdriver', {
#         get: () => undefined
#         })
#     """
#         })
#     driver.execute_cdp_cmd(
#         'Network.setUserAgentOverride', {
#             "userAgent":
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'
#         })
#     print(driver.execute_script("return navigator.userAgent;"))
#     driver.get(
#         'https://discord.com/channels/290278814217535489/699253100174770176')
#     time.sleep(2)
#     parse(find_new_messages(driver))


def post_trade():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    driver = webdriver.Chrome(executable_path=DRIVER_PATH,
                              options=chrome_options)
    driver.get('https://www.instagram.com/marginkings/')
    time.sleep(2)


def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


schedule.every(15).seconds.do(run_threaded, check_discord)
while True:
    schedule.run_pending()
    time.sleep(1)
