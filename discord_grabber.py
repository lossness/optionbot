import pathlib
import time
import os
import re
import random
import logging
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
from make_image import text_on_img
from db_utils import update_table, error_checker, verify_trade, update_error_table
from dotenv import load_dotenv
from exceptions import IsOldMessage
from timeit import default_timer as timer
from tqdm import tqdm

# include parent directory in path
PATH = pathlib.Path.cwd()
TRADERS = ["Eric68", "MariaC82", "ThuhKang", "Jen ❤crypto"]
logging.basicConfig(filename='discord.log',
                    filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')


def find_new_messages(driver) -> list:
    '''
    Scrapes new messages from discord and returns them in a list
    '''
    message_list = []
    messages = driver.find_elements_by_xpath("//*[@role='group']")
    for message in messages:
        for trader in TRADERS:
            if trader in message.text:
                message_list += [message.text]
    return message_list


def match_trader(split_message_list: list):
    for split in split_message_list:
        if split in TRADERS:
            trade_author = split
            return trade_author


def get_trade_expiration(split_message_list: list, unsplit_message_list: list):
    expiration_date = []
    try:
        for split in split_message_list:
            expiration_date = re.findall(
                r"^(0?[1-9]|1[0-2])(.|/|\\|-)(0?[1-9]|[12][0-9]|3[01])$",
                split.replace(' ', ''))

            if expiration_date:
                expiration_date = ''.join(expiration_date[0])
                split_message_list.remove(split)
                return expiration_date, split_message_list

            if expiration_date == []:
                split_list = unsplit_message_list.split(" - ")
                for split in split_list:
                    expiration_date = re.findall(
                        r"^(0?[1-9]|1[0-2])(.|/|\\|-)(0?[1-9]|[12][0-9]|3[01])$",
                        split.replace(' ', ''))

                    if expiration_date:
                        expiration_date = ''.join(expiration_date[0])
                        split_list.remove(split)
                        return expiration_date, split_list

        if expiration_date == []:
            raise KeyError("Could not determine expiration of trade!")

    except KeyError as e:
        logging.warning(e)
        return 'error', split_message_list


def get_call_or_put_and_strike_price(split_message_list: list,
                                     split_result: list):
    try:
        call_or_put = None
        for split in split_message_list:
            match = re.findall(
                r"[-+]?\d*\.\d+(?:[c, C, call, CALL]|[p, P, PUT, put])+|\d+(?:[c, C, call, CALL]|[p, P, PUT, put])+",
                split)
            if 'c' in str(match).lower():
                split_message_list.remove(split)
                strike_price = re.findall(r'[-+]?\d*\.\d+|\d+', str(match))
                call_or_put = 'call'
                return call_or_put, strike_price[0], split_message_list
            if 'p' in str(match).lower():
                split_message_list.remove(split)
                strike_price = re.findall(r'[-+]?\d*\.\d+|\d+', str(match))
                call_or_put = 'put'
                return call_or_put, strike_price[0], split_message_list
        if match == [] or None:
            raise KeyError(
                "Could not determine if trade is call or put! Could not get strike price!"
            )
        # if call_or_put == None:
        #     raise KeyError("Could not determine if trade is call or put!")
        #     return 'error', 'error', split_message_list
    except KeyError as e:
        logging.warning(e)
        return 'error', 'error', split_message_list


def get_in_or_out(split_message_list: list):
    try:
        in_or_out_tup = None
        for split in split_message_list:
            if str(split.lower()).replace(' ', '') in ('in', 'buy'):
                split_message_list.remove(split)
                in_or_out_tup = 'in'
                return in_or_out_tup, split_message_list
            if str(split.lower()).replace(' ', '') in ('out', 'sell'):
                split_message_list.remove(split)
                in_or_out_tup = 'out'
                return in_or_out_tup, split_message_list
        if in_or_out_tup is None:
            raise KeyError("Could not determine if the trade is in or out!")
    except KeyError as e:
        logging.warning(e)


def get_buy_price(split_message_list):
    for split in split_message_list:
        split.replace('$', '')
        try:
            if len(split) and any(char.isdigit() for char in split):
                buy_price = re.findall(r'[-+]?\d*\.\d+|\d+', str(split))
                split_message_list.remove(split)
                return buy_price[0], split_message_list
        except ValueError as e:
            continue


def get_stock_ticker(split_message_list):
    lines = []
    with open('NASDAQandNYSE.txt', 'rt') as file:
        for line in file:
            lines.append(line.rstrip('\n'))
        try:
            stock_ticker = split_message_list[0].replace('\n', '')
            stock_ticker = stock_ticker.replace(' ', '')
            if stock_ticker.upper() in lines or 'SPY':
                split_message_list.pop(0)
                file.close()
                return str(stock_ticker), split_message_list
            else:
                file.close()
                raise KeyError("Stock ticker could not be matched!")
        except KeyError as e:
            logging.warning(e)


def message_listener(driver) -> list:
    try:
        newest_message = []
        newest_message.append(
            driver.find_element_by_xpath("//*[@id='messages-51']").text)
        return list(newest_message)
    except NoSuchElementException('ERROR FINDING NEWEST MESSAGE') as e:
        logging.warning(e)


def filter_message(variable):
    noise_words = ['BOT', r'BBS-TRADE-BOT\nBOT', 'BBS-TRADE-BOT', 'joel']
    if (variable in noise_words):
        return False
    else:
        return True


def filter_trader(variable):
    if (variable in TRADERS):
        return True
    else:
        return False


def remove_trader(variable):
    if variable:
        return True
    else:
        return False


LAST_MESSAGE = "None"


def producer(driver):
    # loop over single discord posts in all matched posts in main channel
    try:
        global LAST_MESSAGE
        new_message = driver.find_elements_by_xpath(
            "//*[@role='group']")[-1].text
        if new_message != LAST_MESSAGE:
            try:
                split_result = new_message.splitlines()
                # removes any empty strings from list
                split_result = list(filter(None, split_result))
                split_result = list(filter(filter_message, split_result))
                trade_author = list(filter(filter_trader, split_result))
                trade_author_tup = trade_author[0]
                # find the longest string left which is the message string
                longest_string = max(split_result, key=len)
                double_split_result = longest_string.split('-')
                double_split_result = list(filter(None, double_split_result))
                # gets a call or put status, and pops that matched entry out of the list
                call_or_put_tup, strike_price_tup, double_split_result = get_call_or_put_and_strike_price(
                    double_split_result, split_result)
                trade_expiration_tup, double_split_result = get_trade_expiration(
                    double_split_result, longest_string)
                in_or_out_tup, double_split_result = get_in_or_out(
                    double_split_result)
                buy_price_tup, double_split_result = get_buy_price(
                    double_split_result)
                stock_ticker_tup, double_split_result = get_stock_ticker(
                    double_split_result)
                datetime_tup = str(datetime.now())
                stock_ticker_tup = stock_ticker_tup.lower()

                trade_tuple = (
                    in_or_out_tup,
                    stock_ticker_tup,
                    datetime_tup,
                    strike_price_tup,
                    call_or_put_tup,
                    buy_price_tup,
                    trade_author_tup,
                    trade_expiration_tup,
                )

                is_duplicate, is_out, has_matching_in, trade_color = verify_trade(
                    list(trade_tuple))

                if is_duplicate:
                    return

                if is_duplicate is False and is_out is False and has_matching_in is False or True:
                    print("updating table")
                    trade_tuple = (
                        in_or_out_tup,
                        stock_ticker_tup,
                        datetime_tup,
                        strike_price_tup,
                        call_or_put_tup,
                        buy_price_tup,
                        trade_author_tup,
                        trade_expiration_tup,
                        trade_color,
                    )
                    message = trade_tuple
                    logging.info(f"Producer got message: {message}")
                    config.new_trades.put(message)
                    config.has_trade.release()
                    update_table(trade_tuple)

            except TypeError:
                pass

            except IndexError:
                pass

            finally:
                LAST_MESSAGE = new_message
        else:
            time.sleep(.1)
            return
    except (TimeoutException, NoSuchElementException) as error:
        logging.warning(
            f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
        pass


def prep_message_for_algos(message: str) -> list:
    '''
    Removes various unneeded text in the message string
    for easier processing.
    '''
    try:
        message = re.sub(r'BOT', '', message)
        message = re.sub(r'BBS-TRADE-', '', message)
        message = re.sub(r'\n', '@', message)
        message = message.split('-')
    except:
        pass
    finally:
        return message


def get_trader(split_message: list) -> str:
    '''
    Finds the trade author of the message
    and then removes it from the message
    '''
    match = False
    for trader in TRADERS:
        for split in split_message:
            if trader in split:
                match = (trader, split)
                return match


def error_producer_beta(driver):
    # loop over single discord posts in all matched posts in main channel
    try:
        counter = 1
        message_list = find_new_messages(driver)
        for message in tqdm(message_list):
            try:
                split_result = prep_message_for_algos(message)
                trade_author, corresponding_slice = get_trader(split_result)
                split_result = str(split_result).replace(
                    str(corresponding_slice), '')
                split_result = split_result.split('-')
                trade_author_tup = tuple(trade_author)
                # find the longest string left which is the message string
                longest_string = max(split_result, key=len)
                double_split_result = longest_string.split('-')
                double_split_result = list(filter(None, double_split_result))
                # gets a call or put status, and pops that matched entry out of the list
                call_or_put_tup, strike_price_tup, double_split_result = get_call_or_put_and_strike_price(
                    double_split_result, split_result)
                trade_expiration_tup, double_split_result = get_trade_expiration(
                    double_split_result, longest_string)
                in_or_out_tup, double_split_result = get_in_or_out(
                    double_split_result)
                buy_price_tup, double_split_result = get_buy_price(
                    double_split_result)
                stock_ticker_tup, double_split_result = get_stock_ticker(
                    double_split_result)
                datetime_tup = str(datetime.now())
                stock_ticker_tup = stock_ticker_tup.lower()

                trade_tuple = (
                    in_or_out_tup,
                    stock_ticker_tup,
                    datetime_tup,
                    strike_price_tup,
                    call_or_put_tup,
                    buy_price_tup,
                    trade_author_tup,
                    trade_expiration_tup,
                )

                if 'error' or 'ERROR' in trade_tuple:
                    update_error_table(trade_tuple)
                    print(counter)
                    counter += 1

            except (KeyError, IndexError, ValueError) as error:
                print(f"{error}")
    except (TimeoutException, NoSuchElementException) as error:
        logging.warning(
            f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
        pass


# message_test = 'BOT\nBBS-TRADE-BOT\nJen ❤crypto\nBuy - Amd - 6\n26 - 52p - 64 - Scalp - Have a stop'

# split_message_test = prep_message_for_algos(message_test)


# get_trader(split_message_test)
def error_producer_classic(driver):
    # loop over single discord posts in all matched posts in main channel
    try:
        counter = 1
        message_list = find_new_messages(driver)
        for new_message in tqdm(message_list):
            try:
                split_result = new_message.splitlines()
                # removes any empty strings from list
                split_result = list(filter(None, split_result))
                split_result = list(filter(filter_message, split_result))
                trade_author = list(filter(filter_trader, split_result))
                trade_author_tup = trade_author[0]
                # find the longest string left which is the message string
                longest_string = max(split_result, key=len)
                double_split_result = longest_string.split('-')
                double_split_result = list(filter(None, double_split_result))
                # gets a call or put status, and pops that matched entry out of the list
                call_or_put_tup, strike_price_tup, double_split_result = get_call_or_put_and_strike_price(
                    double_split_result, split_result)
                trade_expiration_tup, double_split_result = get_trade_expiration(
                    double_split_result, longest_string)
                in_or_out_tup, double_split_result = get_in_or_out(
                    double_split_result)
                buy_price_tup, double_split_result = get_buy_price(
                    double_split_result)
                stock_ticker_tup, double_split_result = get_stock_ticker(
                    double_split_result)
                datetime_tup = str(datetime.now())
                stock_ticker_tup = stock_ticker_tup.lower()
                color = 'red'

                trade_tuple = (
                    in_or_out_tup,
                    stock_ticker_tup,
                    datetime_tup,
                    strike_price_tup,
                    call_or_put_tup,
                    buy_price_tup,
                    trade_author_tup,
                    trade_expiration_tup,
                    color,
                )
                if 'error' or 'ERROR' in trade_tuple:
                    update_error_table(trade_tuple)
                    print(counter)
                    counter += 1

            except (KeyError, IndexError, ValueError) as error:
                print(f"{error}")
    except (TimeoutException, NoSuchElementException) as error:
        logging.warning(
            f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
        pass
