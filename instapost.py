import pathlib
import time
import os
import re
import sqlite3
import random
import pyperclip
import config

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
from insta_browser import switch_to_mobile
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from timeit import default_timer as timer
from main_logger import logger
from exceptions import MakeImageError
from db_utils import convert_date_to_text

load_dotenv()
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PW = os.getenv("INSTA_PASSWORD")
CHROME_INSTA = os.getenv("INSTACHROME")
DRIVER_PATH = os.getenv("DRIVER_PATH")
# include parent directory in path
PATH = pathlib.Path.cwd()
KEYBOARD = Controller()


def make_image(msg):
    suffix = '.png'
    in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = msg
    try:
        expiration = convert_date_to_text(expiration)
        if in_or_out == 'in':
            in_or_out = 'buy'
        if in_or_out == 'out':
            in_or_out = 'sell'

        im = Image.open(os.path.join(PATH, 'template_images', color + suffix))
        text = f'We are going\n {in_or_out.upper()} on {ticker.upper()}\n Strike price: {strike_price.upper()}\n {call_or_put.upper()} Price: {buy_price}\n Expiration: {expiration}'
        filename = f'{in_or_out}.{ticker}.{strike_price}.{call_or_put}.{expiration}.png'
        my_font = ImageFont.truetype('micross.ttf', 75)
        draw = ImageDraw.Draw(im)
        # w, h = draw.multiline_textsize(text, font=my_font)
        # draw text
        draw.multiline_text((235, 415),
                            text,
                            fill='black',
                            font=my_font,
                            spacing=4,
                            align='center')
        # save file
        trade_image_path = os.path.join(PATH, 'trade_images', filename)
        im.save(trade_image_path)
    except:
        logger.fatal("COULD NOT OPEN IMAGE TO POST TRADE!")
        print("COULD NOT OPEN IMAGE TO POST TRADE")
        trade_image_path = 'error'

    finally:
        return trade_image_path


def consumer(driver):
    while config.has_trade.acquire():
        start = timer()
        print("\nInstagram posting initiated..")
        message = config.new_trades.get()
        try:
            image_path = make_image(message)
            if 'error' in image_path:
                raise MakeImageError

            upload_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[@id='react-root']//div[3][@data-testid='new-post-button']"
                )))
            upload_element.click()
            driver.find_elements_by_css_selector('form input')[0].send_keys(
                image_path)
            next_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[text()='Next']")))
            next_button.click()
            share_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[text()='Share']")))
            share_button.click()
            print("\ninstagram posting completed")
            time.sleep(2)

        except MakeImageError as error:
            logger.fatal(f'{error}')
            # caption_field = WebDriverWait(driver, 5).until(
            # EC.presence_of_element_located((By.XPATH, "//textarea")))
        finally:
            end = timer()
            print(f"\n{end - start}")
            config.new_trades.task_done()
