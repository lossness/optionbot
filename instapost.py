import pathlib
import time
import os
import re
import sqlite3
import random
import pyperclip
import config

from datetime import datetime
#from pynput.keyboard import Key, Controller
#from insta_browser import switch_to_mobile
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from timeit import default_timer as timer
from main_logger import logger
from exceptions import *
from db_utils import convert_date, is_posted_to_insta, db_insta_posting_successful, prune_completed_trades

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

load_dotenv()
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PW = os.getenv("INSTA_PASSWORD")
CHROME_INSTA = os.getenv("INSTACHROME")
DRIVER_PATH = os.getenv("DRIVER_PATH")
# include parent directory in path
PATH = pathlib.Path.cwd()
# debug flag to skip posting the image to insta
DEBUG = config.DEBUG


def make_image(msg):
    suffix = '.png'
    in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, date, time = msg
    try:
        expiration = convert_date(expiration)
        expiration = expiration.replace('/', '-')
        if in_or_out == 'in':
            in_or_out = 'BUYing'
        if in_or_out == 'out':
            in_or_out = 'SELLing'

        im = Image.open(os.path.join(PATH, 'template_images', color + suffix))
        text = f'We\'re {in_or_out} {ticker.upper()}\n Strike: {strike_price.upper()}\n {call_or_put.upper()} Price: {buy_price}\n Expires: {expiration}'
        filename = f'{in_or_out}.{ticker}.{strike_price}.{call_or_put}.{expiration}.png'
        #my_font = ImageFont.truetype('micross.ttf', 75)
        my_font = ImageFont.truetype(
            r'/home/swing/projects/fonts/Eurostile LT Bold.ttf', 60)
        draw = ImageDraw.Draw(im)
        # w, h = draw.multiline_textsize(text, font=my_font)
        # draw text
        draw.multiline_text((215, 425),
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
    while config.has_trade.acquire(blocking=True):
        start = timer()
        print("\nInstagram posting initiated..")
        full_message = config.new_trades.get()
        trade_id = full_message[0]
        message = full_message[1]
        try:
            if DEBUG:
                db_insta_posting_successful(trade_id)
                print(message)
                prune_completed_trades()
            elif message[0] == 'out' and is_posted_to_insta(
                    message).lower() == 'true' or message[0] == 'in':
                image_path = make_image(message)
                if 'error' in image_path:
                    raise MakeImageError
                upload_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//*[@id='react-root']//div[3][@data-testid='new-post-button']"
                    )))
                upload_element.click()
                #driver.find_elements_by_css_selector('form input')[0].send_keys(
                #    image_path)
                form_field = WebDriverWait(driver, 8).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "form input")))
                form_field[0].send_keys(image_path)
                next_button = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[text()='Next']")))
                next_button.click()
                share_button = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[text()='Share']")))
                try:
                    form_field_description = WebDriverWait(driver, 8).until(
                        EC.presence_of_all_elements_located((
                            By.XPATH,
                            "//*[@id='react-root']/section/div[2]/section[1]/div[1]/textarea"
                        )))
                    form_field_description[0].send_keys(
                        "\n.\n.\n.\n#flowalerts #optionstrading #daytrader #trader #stockmarket #investing #wallstreet #entrepreneur #investment #tradingswing #tradingoptions #tradingsignals #marketanalysis #optionswings #easytrading #optionstrading #swingtrading #callsandputs #swingtrader #swingtrade #stockoptions #makingmoney #makemoney #success #successfultrading"
                    )
                except TimeoutException:
                    pass
                share_button.click()
                print("\ninstagram posting completed")
                db_insta_posting_successful(trade_id)
                config.EVENT.wait(.5)
                prune_completed_trades()
                config.EVENT.wait(1.0)
            else:
                raise MatchingInNeverPosted

        except (MakeImageError, NoSuchElementException,
                TimeoutException) as error:
            logger.fatal(f'{error}\n COULD NOT POST TO INSTA. ', exc_info=True)
            # caption_field = WebDriverWait(driver, 5).until(
            # EC.presence_of_element_located((By.XPATH, "//textarea")))

        except MatchingInNeverPosted:
            logger.fatal(
                "The matching in for this trade had an error while being posted to insta.  This trade will not post."
            )

        finally:
            end = timer()
            print(f"\n{end - start}")
            config.new_trades.task_done()
