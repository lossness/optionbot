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
from time_utils import minutes_difference, standard_datetime

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
EVENT = config.EVENT
# debug flag to skip posting the image to insta
DEBUG = config.DEBUG
NICHE_TAGS = [
    "#optionstrader", "#optionstrade", "#tradingswing", "#tradingoptions",
    "#easytrading", "#swingtrading", "#callsandputs", "#swingtrader",
    "#swingtrade"
]
BRAND_TAG = "#flowalerts"
AVERAGE_TAGS = ["#optionstrading", "#tradingstocks", "#tradingsignals"]
FREQUENT_TAGS = [
    "#daytrader", "#stockmarket", "#investing", "#stocks", "#wallstreet",
    "#investment", "#entrepreneur", "#wealth", "#invest", "#investor",
    "#success", "#makemoneyonline", "#daytrading", "#makemoney", "#makingmoney"
]


def create_image(img_path, text, filename):
    my_font = ImageFont.truetype(
        r'/home/swing/projects/fonts/Eurostile LT Bold.ttf', 60)
    draw = ImageDraw.Draw(img_path)
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
    img_path.save(trade_image_path)
    return trade_image_path


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
        trade_image_path = create_image(im, text, filename)
        im.save(trade_image_path)
        #if config.RANDOM_TAG_COUNTER < 4:
        delayed_im = Image.open(
            os.path.join(PATH, 'delayed_template_images', color + suffix))
        delayed_filename = f'{in_or_out}.{ticker}.{strike_price}.{call_or_put}.{expiration}.delayed.png'
        delayed_image_path = create_image(delayed_im, text, delayed_filename)
        delayed_trade = (datetime, delayed_image_path)
        delayed_im.save(delayed_image_path)
        config.new_delayed_trades.put(delayed_trade)
        config.has_delayed_trade.release()
    except:
        logger.fatal("COULD NOT OPEN IMAGE TO POST TRADE!")
        print("COULD NOT OPEN IMAGE TO POST TRADE")
        trade_image_path = 'error'

    finally:
        return trade_image_path


def force_make_image(msg):
    suffix = '.png'
    in_or_out, ticker, strike_price, call_or_put, buy_price, expiration, color, force = msg
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
        datetime = standard_datetime()
    except:
        logger.fatal("COULD NOT OPEN IMAGE TO POST TRADE!")
        print("COULD NOT OPEN IMAGE TO POST TRADE")
        trade_image_path = 'error'

    finally:
        return trade_image_path


def consumer(driver):
    while config.has_trade.acquire(blocking=True):
        full_message = config.new_trades.get()
        start = timer()
        if 'force_trade' not in full_message:
            trade_id = full_message[0]
            message = full_message[1]
            try:
                if DEBUG:
                    print("\nDebug mode: Not posted to instagram.")
                    db_insta_posting_successful(trade_id)
                    print(message)
                    prune_completed_trades()
                    return
                if message[0] == 'out' and is_posted_to_insta(
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
                    share_button.click()
                    print("\ninstagram posting completed")
                    db_insta_posting_successful(trade_id)
                    config.EVENT.wait(.5)
                    prune_completed_trades()
                    config.EVENT.wait(2)
                else:
                    raise MatchingInNeverPosted

            except (MakeImageError, NoSuchElementException,
                    TimeoutException) as error:
                logger.fatal(f'{error}\n COULD NOT POST TO INSTA. ',
                             exc_info=True)
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
        elif 'force_trade' in full_message:
            try:
                image_path = full_message[-1]
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
                share_button.click()
                print("\nforce instagram posting completed")
                config.EVENT.wait(3)

            except (NoSuchElementException, TimeoutException) as error:
                logger.fatal(f'{error}\n COULD NOT FORCE POST TO INSTA. ',
                             exc_info=True)
                # caption_field = WebDriverWait(driver, 5).until(
                # EC.presence_of_element_located((By.XPATH, "//textarea")))

            finally:
                end = timer()
                print(f"\n{end - start}")
                config.new_trades.task_done()


def delayed_consumer(driver):
    if len(config.cooking_trades) > 0:
        for trade in config.cooking_trades:
            if minutes_difference(trade[0]) > 5:
                image_path = trade[1]
                config.cooking_trades.remove(trade)
                if config.RANDOM_TAG_COUNTER >= 4:
                    config.new_delayed_trades.task_done()
                else:
                    try:
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
                        if config.RANDOM_TAG_COUNTER < 4:
                            try:
                                form_field_description = WebDriverWait(
                                    driver, 8
                                ).until(
                                    EC.presence_of_all_elements_located((
                                        By.XPATH,
                                        "//*[@id='react-root']/section/div[2]/section[1]/div[1]/textarea"
                                    )))

                                form_field_description[0].send_keys(
                                    f"\n.\n.\n.\n.\n{random.choice(NICHE_TAGS)} #flowalerts {random.choice(AVERAGE_TAGS)} {random.choice(FREQUENT_TAGS)} {random.choice(FREQUENT_TAGS)}"
                                )
                                config.RANDOM_TAG_COUNTER += 1
                            except TimeoutException:
                                pass
                        share_button = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//button[text()='Share']")))
                        share_button.click()
                        EVENT.wait(5)

                    except (MakeImageError, NoSuchElementException,
                            TimeoutException) as error:
                        logger.fatal(f'{error}\n COULD NOT POST TO INSTA. ',
                                     exc_info=True)
                        # caption_field = WebDriverWait(driver, 5).until(
                        # EC.presence_of_element_located((By.XPATH, "//textarea")))
                        continue

                    except MatchingInNeverPosted:
                        logger.fatal(
                            "The matching in for this trade had an error while being posted to insta.  This trade will not post."
                        )

                    finally:
                        config.new_delayed_trades.task_done()
            else:
                EVENT.wait(3)
    elif config.has_delayed_trade.acquire(blocking=False) is True:
        delayed_trade_image_path = config.new_delayed_trades.get()
        config.cooking_trades.append(delayed_trade_image_path)
        EVENT.wait(1)
    else:
        EVENT.wait(1)