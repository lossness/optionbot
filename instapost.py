import pathlib
import time
import os
import re
import sqlite3
import random
import pyperclip
import logging

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
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PW = os.getenv("INSTA_PASSWORD")
CHROME_INSTA = os.getenv("INSTACHROME")
DRIVER_PATH = os.getenv("DRIVER_PATH")
# include parent directory in path
PATH = pathlib.Path.cwd()
KEYBOARD = Controller()


def consumer(driver, pipeline, event):
    while not event.is_set() or not pipeline.empty():
        event.set()
        message = pipeline.get_message("Consumer")
        logging.info(
            f"Consumer storing message {message}  queue size={pipeline.qsize()}"
        )
        (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price,
         user_name, expiration, color) = message
        expiration = expiration.replace(r'/', '.')
        text = f'We are going\n {in_or_out.upper()} on {ticker.upper()}\n Strike price: {strike_price.upper()}\n {call_or_put.upper()} Price: {buy_price}\n Expiration: {expiration}'
        filename = f'{in_or_out}.{ticker}.{strike_price}.{call_or_put}.{expiration}.png'
        my_font = ImageFont.truetype('micross.ttf', 180)
        # create image
        max_w, max_h = (1080, 1080)
        image = Image.new("RGBA", (max_w, max_h), color)
        draw = ImageDraw.Draw(image)
        w, h = draw.multiline_textsize(text, font=my_font)
        # draw text
        draw.multiline_text((0, 0),
                            text,
                            fill='black',
                            font=my_font,
                            spacing=4,
                            align='center')
        # save file
        image.save(filename)
        try:
            image_path = f"{PATH}\\{filename}"
            upload_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='react-root']//button[2]")))
            upload_element.click()
            driver.find_elements_by_css_selector('form input')[0].send_keys(
                image_path)
            KEYBOARD.press(Key.esc)
            next_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[text()='Next']")))
            next_button.click()
            share_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[text()='Share']")))
            share_button.click()
            event.clear()
            # caption_field = WebDriverWait(driver, 5).until(
            # EC.presence_of_element_located((By.XPATH, "//textarea")))
        finally:
            driver.quit()
