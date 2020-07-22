import pathlib
import time
import os
import re
import random
import config
import yfinance as yf

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
from exceptions import IsOldMessage, TickerError, LiveStrikePriceError, DuplicateTrade, IsAInTrade
from timeit import default_timer as timer
from tqdm import tqdm
from main_logger import logger
from second_level_checks import ErrorChecker
# include parent directory in path
PATH = pathlib.Path.cwd()
TRADERS = ["Eric68", "MariaC82", "ThuhKang", "Jen ❤crypto"]


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


def get_trade_expiration(split_message_list: list):
    expiration_date = []
    try:
        expiration_date = re.findall(
            r"\s(0?[1-9]|1[0-2])(|/|\\|-)(0?[1-9]|[12][0-9]|3[01])\s",
            str(split_message_list))

        if expiration_date:
            expiration_date = ''.join(expiration_date[0])
            split_message_list.remove(' ' + expiration_date + ' ')

        if expiration_date == []:
            raise KeyError("Could not determine expiration of trade!")

    except KeyError as e:
        logger.warning(f'{e} : message : {split_message_list}')
        expiration_date = 'error'

    finally:
        return expiration_date, split_message_list


def three_feet(split_message_list: list, ticker_func):
    '''
    returns three values in ONE! 
    1. If the trade is call or put
    2. The strike price of the trade
    3. The ticker for the trade
    '''
    try:
        call_or_put = 'error'
        strike_price = 'error'
        ticker, split_message_list = ticker_func(split_message_list)
        match = re.findall(
            r"[-+]?\d*\.\d+(?:[c, C, call, CALL]|[p, P, PUT, put])+|\d+(?:[c, C, call, CALL]|[p, P, PUT, put])+",
            str(split_message_list))

        if match == [] or False:
            raise KeyError(
                "Could not determine if trade is call or put! Could not get strike price!"
            )

        for item in match:
            if 'c' in str(item).lower():
                strike_price = re.findall(r'[-+]?\d*\.\d+|\d+', str(item))
                strike_price = strike_price[0]
                try:
                    ticker_data = yf.Ticker(ticker)
                    call_or_put = 'call'
                    live_price = ticker_data.info['open']
                    if float(((live_price - float(strike_price)) * 100) /
                             float(strike_price)) > 15:
                        raise LiveStrikePriceError
                    split_message_list.remove(' ' + item)
                    break

                except LiveStrikePriceError as error:
                    logger.error(
                        f'{error} : {split_message_list} Live price : {live_price} Strike price : {strike_price}'
                    )
                    strike_price = 'error'

            if 'p' in str(item).lower():
                strike_price = re.findall(r'[-+]?\d*\.\d+|\d+', str(item))
                strike_price = strike_price[0]
                try:
                    ticker_data = yf.Ticker(ticker)
                    call_or_put = 'put'
                    live_price = ticker_data.info['open']
                    if float(((live_price - float(strike_price)) * 100) /
                             float(strike_price)) > 15:
                        raise LiveStrikePriceError
                    split_message_list.remove(' ' + item)
                    break

                except LiveStrikePriceError as error:
                    logger.error(
                        f'{error} : {split_message_list} Live price : {live_price} Strike price : {strike_price}'
                    )
                    strike_price = 'error'

    except KeyError as e:
        logger.warning(f'{e} : {split_message_list}')
        call_or_put = 'error'
        strike_price = 'error'

    finally:
        results = (call_or_put, strike_price, ticker, split_message_list)
        return results


def get_in_or_out(split_message_list: list):
    try:
        in_or_out = 'error'
        matches = 0
        for split in split_message_list:
            if str(split.lower()).replace(' ', '') in ('in', 'buy'):
                split_message_list.remove(split)
                in_or_out = 'in'
                matches += 1

            if str(split.lower()).replace(' ', '') in ('out', 'sell'):
                split_message_list.remove(split)
                in_or_out = 'out'
                matches += 1

        if in_or_out is None:
            raise KeyError(
                "Could not determine if the trade is in or out! Level 1.")

        if matches > 1:
            raise ValueError(
                "Mulitple matches detected for in or out! Level 1.")

    except (KeyError, ValueError) as e:
        logger.error(f'{e} : {split_message_list}')
        in_or_out = 'error'

    finally:
        return in_or_out, split_message_list


def get_stock_ticker(split_message_list):
    lines = []
    result = 'error'
    ticker_matches = 0
    with open('NASDAQandNYSE.txt', 'rt') as file:
        for line in file:
            lines.append(line.rstrip('\n'))
        try:
            for split in split_message_list:
                potential_ticker = split.replace('\n', '')
                potential_ticker = split.replace(' ', '')
                potential_ticker = potential_ticker.upper()
                if potential_ticker == 'SPY':
                    result = potential_ticker
                    ticker_matches += 1
                    split_message_list.remove(split)
                    break

                if potential_ticker in lines and potential_ticker != 'OUT':
                    result = potential_ticker
                    ticker_matches += 1
                    split_message_list.remove(split)

            if ticker_matches != 1:
                result = 'error'
                raise TickerError

        except TickerError as e:
            logger.error(
                f'{e} : Ticker matches : {ticker_matches} trade : {split_message_list}'
            )

        finally:
            file.close()
            return result, split_message_list


def get_buy_price(split_message_list):
    try:
        filtered_list = []
        for split in split_message_list:
            split.replace('$', '')
            if len(split) > 2 and any(char.isalpha()
                                      for char in split) is False:
                filtered_list.append(split)
        buy_price = re.findall(r'\s([-+]?\d*)(\.)(\d+|\d+)\s',
                               str(filtered_list))

        if buy_price == [] or len(buy_price) > 1:
            raise KeyError("Could not determine buy price!")

        if buy_price:
            buy_price = ''.join(buy_price[0])
            split_message_list.remove(' ' + buy_price + ' ')

    except KeyError as e:
        logger.error(f'{e} : {split_message_list}')
        buy_price = 'error'

    finally:
        return buy_price, split_message_list


def message_listener(driver) -> list:
    try:
        newest_message = []
        newest_message.append(
            driver.find_element_by_xpath("//*[@id='messages-51']").text)
        return list(newest_message)
    except NoSuchElementException('ERROR FINDING NEWEST MESSAGE') as e:
        logger.warning(e)


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
            processor(new_message)
            LAST_MESSAGE = new_message
        else:
            time.sleep(.1)
            return
    except (TimeoutException, NoSuchElementException) as error:
        logger.warning(
            f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
        pass


def processor(new_message):
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
        call_or_put_tup, strike_price_tup, double_split_result = three_feet(
            double_split_result)

        trade_expiration_tup, double_split_result = get_trade_expiration(
            double_split_result)

        stock_ticker_tup, double_split_result = get_stock_ticker(
            double_split_result)

        buy_price_tup, double_split_result = get_buy_price(double_split_result)

        in_or_out_tup, double_split_result = get_in_or_out(double_split_result)

        datetime_tup = str(datetime.now())
        stock_ticker_tup = stock_ticker_tup.lower()

        if strike_price_tup == buy_price_tup:
            strike_price_tup = 'error'
            buy_price_tup = 'error'

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

        duplicate_check, out_check, matching_in_check, trade_color_choice, trade_ignored = verify_trade(
            list(trade_tuple))

        if duplicate_check:
            return

        if trade_ignored:
            return

        if duplicate_check is False and out_check is False and matching_in_check is False or True and trade_ignored is False:
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
                trade_color_choice,
            )
            message = trade_tuple
            logger.info(f"Producer got message: {message}")
            config.new_trades.put(message)
            config.has_trade.release()
            update_table(trade_tuple)

    except TypeError:
        pass

    except IndexError:
        pass


### ERROR CHECKING FUNCTIONS BELOW


def error_producer_classic(driver):
    # loop over single discord posts in all matched posts in main channel
    try:
        counter = 0
        error_counter = 0
        message_list = find_new_messages(driver)
        try:
            for new_message in tqdm(message_list):
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
                three_feet_results = three_feet(double_split_result,
                                                get_stock_ticker)

                call_or_put_tup, strike_price_tup, stock_ticker_tup, double_split_result = three_feet_results

                trade_expiration_tup, double_split_result = get_trade_expiration(
                    double_split_result)

                buy_price_tup, double_split_result = get_buy_price(
                    double_split_result)

                in_or_out_tup, double_split_result = get_in_or_out(
                    double_split_result)

                datetime_tup = str(datetime.now())
                stock_ticker_tup = stock_ticker_tup.lower()
                color_tup = 'error_check'

                if buy_price_tup == strike_price_tup:
                    buy_price_tup = 'error'
                    strike_price_tup = 'error'

                trade_tuple = (
                    in_or_out_tup,
                    stock_ticker_tup,
                    datetime_tup,
                    strike_price_tup,
                    call_or_put_tup,
                    buy_price_tup,
                    trade_author_tup,
                    trade_expiration_tup,
                    color_tup,
                )

                if 'error' in trade_tuple:
                    logger.error(
                        f'This trade contains error(s)! : {new_message}')
                    update_error_table(trade_tuple)
                    error_counter += 1

                elif 'error' not in trade_tuple:
                    ignore_trade, trade_color_choice = verify_trade(
                        list(trade_tuple))
                    if ignore_trade is False:
                        update_table(trade_tuple)
                        counter += 1

        except (KeyError, IndexError, ValueError) as error:
            print(f"{error}")
            pass

    except (TimeoutException, NoSuchElementException) as error:
        logger.warning(
            f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
        pass

    finally:
        print(counter)