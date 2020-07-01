import pathlib
import time
import os
import re
import sqlite3
import random
import pyperclip

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from pynput.keyboard import Key, Controller
from PIL import Image, ImageDraw
from dotenv import load_dotenv

load_dotenv()
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PW = os.getenv("INSTA_PASSWORD")
CHROME_INSTA = os.getenv("INSTACHROME")
DRIVER_PATH = os.getenv("DRIVER_PATH")
# include parent directory in path
PATH = pathlib.Path.cwd()
KEYBOARD = Controller()


def switch_to_mobile():
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('j')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('j')
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('m')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('m')
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('j')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('j')


# def prepare_post(path):
#     try:
#         # Chrome setup
#         chrome_options = Options()
#         chrome_options.debugger_address = "127.0.0.1:9223"
#         driver = webdriver.Chrome(options=chrome_options,
#                                   executable_path=DRIVER_PATH)
#         #driver.get('https://www.instagram.com/marginkings/')
#         upload_element = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located(
#                 (By.XPATH, "//*[@id='react-root']//button[2]")))
#         upload_element.send_keys(r"shaaaa")
#         upload_element.click()
#         pyperclip.copy(path)
#         KEYBOARD.press(Key.ctrl)
#         KEYBOARD.press('v')
#         KEYBOARD.release(Key.ctrl)
#         KEYBOARD.release('v')
#         KEYBOARD.press(Key.enter)
#         KEYBOARD.release(Key.enter)
#         next_button = driver.find_element_by_xpath("//button[text()='Next']")
#         next_button.click()
#         caption_field = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located((By.XPATH, "//textarea")))

#         print("stop")

#     finally:
#         driver.quit()
#         driver.close()


def post_conductor(path, driver):
    try:
        upload_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='react-root']//button[2]")))
        upload_element.send_keys('shazam')
        upload_element.click()
        time.sleep(.2)
        pyperclip.copy(path)
        KEYBOARD.press(Key.ctrl)
        KEYBOARD.press('v')
        KEYBOARD.release(Key.ctrl)
        KEYBOARD.release('v')
        KEYBOARD.press(Key.enter)
        KEYBOARD.release(Key.enter)
        next_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[text()='Next']")))
        next_button.click()
        share_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[text()='Share']")))
        share_button.click()
        #caption_field = WebDriverWait(driver, 5).until(
        #    EC.presence_of_element_located((By.XPATH, "//textarea")))
    finally:
        driver.quit()


def insta_login(driver):
    try:
        login_username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//input[@name='username']")))

        login_password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//input[@name='password']")))
        for letter in INSTA_USERNAME:
            login_username.send_keys(letter)
            sleep_time = random.random()
            time.sleep(sleep_time)

        for letter in INSTA_PW:
            login_password.send_keys(letter)
            sleep_time = random.random()
            time.sleep(sleep_time)

        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//button[@type='submit']")))
        sleep_time = random.uniform(1.1, 2.9)
        time.sleep(sleep_time)
        login_button.click()
        print("Logged into instagram successfully.")
    except TimeoutException:
        print("Already logged into instagram.")


# def collect_match(trade:tuple, trades_list:list):
#     (in_or_out, ticker, strike_price, user_name, expiration) = trade
#     ticker = ticker.lower()
#     matched_trades = re.findall(
#                 rf'\(((?:[\'in\', \'out\'])+, (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'))\)',
#                 str(trades_list))

# def complete_trade_match():
#     try:
#         con = db_connect()
#         cur = con.cursor()
#         filtered_trade_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration from trades"
#         cur.execute(filtered_trade_sql)
#         filtered_trades = cur.fetchall()
#         matched_trades_list = []
#         for trade in filtered_trades:
#             (in_or_out, ticker, strike_price, user_name, expiration) = trade
#             ticker = ticker.lower()
#             matched_trades = re.findall(
#                 rf'\(((?:[\'in\', \'out\'])+, (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'))\)',
#                 str(filtered_trades))
#             if len(matched_trades) == 2:
#                 # delete_matched_trade_sql = "DELETE from trades WHERE (ticker, strike_price, user_name, expiration) = (?, ?, ?, ?)"
#                 # cur.execute(delete_matched_trade_sql,
#                 #             (ticker, strike_price, user_name, expiration))
#                 # con.commit()
#                 matched_trades_list.append(
#                     (matched_trades[0][0], matched_trades[1][0]))
#         return matched_trades_list

#     except ValueError:
#         pass

#     finally:
#         if (con):
#             con.close()
#             print('Trade match search completed')
