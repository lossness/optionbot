import pathlib
import time
import os
import re
import random
import config
import yfinance as yf
import pandas as pd
import math
import yahoo_fin.stock_info as si

from datetime import datetime
from make_image import text_on_img
from db_utils import update_table, verify_trade, update_error_table, convert_date, convert_date_to_text
from timeit import default_timer as timer
from main_logger import logger
from second_level_checks import ErrorChecker
from decimal import *
from collections import namedtuple
from exceptions import LiveBuyPriceError, LiveStrikePriceError, ReleaseTradeError, TimeoutException, TickerError
from time_utils import get_date_and_time, standard_datetime
from math_utils import percent_difference

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# include parent directory in path
PATH = pathlib.Path.cwd()
DEBUG = config.DEBUG
EVENT = config.EVENT
#TRADERS = [
#    "Eric68", "MariaC82", "ThuhKang", "Jen♡♡crypto", "joel", "Treefidey",
#    "Etwit"
#]
TRADERS = ["MariaC82", "joel", "Treefidey", "Etwit", "Jen♡♡crypto"]
LAST_MESSAGE = "None"
LAST_FIXED_MESSAGE = "None"
LAST_ETWIT_MESSAGE = "None"
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


def initiate_bbs_driver():
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
    if DEBUG == 'dev':
        #channel = 'bot-dev-talk (channel)'
        #child_element = 'Messages in bot-dev-talk'
        try:
            last_element = discord_driver.find_elements_by_xpath(
                "//*[@aria-label='bot-dev-talk (channel)']//div[@aria-label='Messages in bot-dev-talk']/child::div/child::div[@role='document']"
            )[-1]
            last_element.location_once_scrolled_into_view
        except (NoSuchElementException, TimeoutError, IndexError) as error:
            logger.fatal(f'{error}\n COULD NOT FIND LAST MESSAGE')
        finally:
            return discord_driver

    if DEBUG == 'bbs' or DEBUG is False:
        #channel = 'all-mod-plays-text (channel)'
        #child_element = 'Messages in all-mod-plays-text'
        try:
            last_element = discord_driver.find_elements_by_xpath(
                "//div[contains(@data-list-item-id, 'chat-messages___chat-messages')]//div[starts-with(@class, 'container')]//div[starts-with(@class, 'embedWrapper')]//div[starts-with(@class, 'grid')]"
            )[-1]
            last_element.location_once_scrolled_into_view

        except (NoSuchElementException, TimeoutError, IndexError) as error:
            logger.fatal(f'{error}\n COULD NOT FIND LAST MESSAGE')
        finally:
            return discord_driver


def initiate_etwitter_driver():
    chrome_options = Options()
    chrome_options.debugger_address = '127.0.0.1:9224'
    etwitter_driver = webdriver.Chrome(executable_path=DISCORD_DRIVER_PATH,
                                       options=chrome_options)
    try:
        etwitter_driver.find_elements_by_xpath(
            "//*[@class='js-chirp-container chirp-container']")
    except (NoSuchElementException, TimeoutError) as error:
        logger.fatal(f'{error}\n COULD NOT FIND LAST ETWEET')
    finally:
        return etwitter_driver


class TradeGrabber:
    def __init__(self):
        self.bbs_driver = initiate_bbs_driver()
        self.etwitter_driver = initiate_etwitter_driver()
        self.LAST_MESSAGE = LAST_MESSAGE
        self.LAST_FIXED_MESSAGE = LAST_FIXED_MESSAGE
        self.LAST_ETWIT_MESSAGE = LAST_ETWIT_MESSAGE
        self.check = ErrorChecker()

    def match_trader(self, split_message_list: list):
        for split in split_message_list:
            if split in TRADERS:
                trade_author = split
                if "Jen" in trade_author:
                    trade_author = "Jen"
                return trade_author

    def get_trade_expiration(self, split_message_list: list):
        expiration_date = []
        possible_expiration_date = []
        try:
            expiration_date = re.findall(
                r"\s'(0?[1-9]|1[0-2])(|/|\\|-)(0?[1-9]|[12][0-9]|3[01])'",
                str(split_message_list))

            if expiration_date:
                expiration_date = ''.join(expiration_date[0])
                if '-' in expiration_date:
                    expiration_date = expiration_date.replace('-', '/')
                split_message_list.remove(expiration_date)

            if expiration_date == []:
                possible_expiration_date = re.findall(
                    r"\s(0?[1-9]|1[0-2])(.)(0?[1-9]|[12][0-9]|3[01])\s",
                    str(split_message_list))
                if len(possible_expiration_date) == 1:
                    expiration_date = possible_expiration_date
                    expiration_date = ''.join(expiration_date[0])
                    expiration_date = expiration_date.replace('.', '/')
                    split_message_list.remove(expiration_date)
            if possible_expiration_date == []:
                possible_expiration_date = re.findall(
                    r"\s'(0?[1-9]|1[0-2])(|/|\\|-)(0?[1-9]|[12][0-9]|3[01])(|/|\\|-)(2?[0-1]|202[0-1])'",
                    str(split_message_list))
                if len(possible_expiration_date) == 1:
                    expiration_date = possible_expiration_date
                    expiration_date = ''.join(expiration_date[0])
                    expiration_date = expiration_date.replace('.', '/')
                    split_message_list.remove(expiration_date)
                    expiration_date = expiration_date.split('/')
                    expiration_date = f"{expiration_date[0]}/{expiration_date[1]}"
                else:
                    raise KeyError("Could not determine expiration of trade!")

        except KeyError as e:
            logger.error(
                f'{e} : GRABBER - GET_TRADE_EXPIRATION FUNC : {split_message_list}',
                exc_info=True)
            expiration_date = 'error'

        finally:
            return expiration_date, split_message_list

    def get_trade_expiration_from_shit_jen(self, split_message_list):
        new_expiration = 'error'
        for item in split_message_list[:3]:
            try:
                if '/' in item and item.replace('/', '').isdigit():
                    new_expiration = item
                    split_message_list.remove(item)
                else:
                    new_expiration = float(item)
                    if item[-1] == '0':
                        new_expiration = str(new_expiration).replace('.',
                                                                     '/') + '0'
                    else:
                        new_expiration = str(new_expiration).replace('.', '/')
                    split_message_list.remove(item)

            except ValueError:
                continue

            if new_expiration == 'error':
                logger.fatal(
                    "Jens special expiration function failed to detect her shit :("
                )
            return str(new_expiration), split_message_list

    def three_feet(self, split_message_list: list, ticker_func):
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
                    if strike_price[-1] == '0' and '.' in strike_price:
                        strike_price = strike_price[:-1]
                    try:
                        ticker_data = yf.Ticker(ticker)
                        call_or_put = 'call'
                        live_price = ticker_data.info['open']
                        price_difference = percent_difference(
                            float(live_price), float(strike_price))
                        if price_difference > 35:
                            raise LiveStrikePriceError
                        split_message_list.remove(item)
                        break

                    except LiveStrikePriceError as error:
                        logger.fatal(
                            f'{error} Live price:{live_price} Strike price:{strike_price}\nMessage with LiveStrikePriceError:{split_message_list}'
                        )
                        strike_price = 'error'

                if 'p' in str(item).lower():
                    strike_price = re.findall(r'[-+]?\d*\.\d+|\d+', str(item))
                    strike_price = strike_price[0]
                    if strike_price[-1] == '0' and '.' in strike_price:
                        strike_price = strike_price[:-1]
                    try:
                        ticker_data = yf.Ticker(ticker)
                        call_or_put = 'put'
                        live_price = ticker_data.info['open']
                        price_difference = percent_difference(
                            float(live_price), float(strike_price))
                        if price_difference > 35:
                            raise LiveStrikePriceError
                        split_message_list.remove(item)
                        break

                    except LiveStrikePriceError as error:
                        logger.fatal(
                            f'{error} Live price:{live_price} Strike price:{strike_price}\nMessage with LiveStrikePriceError:{split_message_list}'
                        )
                        strike_price = 'error'

        except KeyError as e:
            logger.warning(f'{e} : {split_message_list}')
            call_or_put = 'error'
            strike_price = 'error'

        finally:
            results = (call_or_put, strike_price, ticker, split_message_list)
            return results

    def get_in_or_out(self, split_message_list: list):
        try:
            in_or_out = 'error'
            matches = 0
            if '#ALERT' in split_message_list and 'OUT' in split_message_list:
                split_message_list.remove('OUT')
            for split in split_message_list:
                if str(split.lower()).replace(' ', '') in (
                        'in', 'buy') or '#ALERT' in split_message_list and str(
                            split.lower()).replace(
                                ' ', '') in ('in', 'buy', 'bought'):
                    split_message_list.remove(split)
                    in_or_out = 'in'
                    matches += 1

                if str(split.lower()).replace(' ', '') in (
                        'out',
                        'sell') or '#ALERT' in split_message_list and str(
                            split.lower()).replace(
                                ' ', '') in ('out', 'sell', 'sold'):
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

    def get_stock_ticker(self, split_message_list):
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

                    if potential_ticker in lines and potential_ticker not in [
                            'OUT', 'ALL', 'FAST'
                    ]:
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

    def get_buy_price(self, split_message_list):
        try:
            filtered_list = []
            for split in split_message_list:
                split.replace('$', '')
                if len(split) > 2 and any(char.isalpha()
                                          for char in split) is False:
                    filtered_list.append(split)
            buy_price = re.findall(r'([-+]?\d*)(\.)(\d+|\d+)',
                                   str(filtered_list))
            if buy_price == [] or len(buy_price) > 1:
                raise KeyError("Could not determine buy price!")
            if buy_price:
                buy_price = ''.join(buy_price[0])
                split_message_list.remove(buy_price)
        except KeyError as e:
            logger.warning(f'{e} : {split_message_list}')
            buy_price = 'error'

        finally:
            return buy_price, split_message_list

    # def compare_live_buy_price(self, new_trade):
    #     live_price = "error"
    #     try:
    #         in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade
    #         live_price = self.check.live_buy_price(ticker, strike_price,
    #                                                expiration, call_or_put)
    #         print(live_price)
    #     except:
    #         pass

    def filter_message(self, variable):
        noise_words = [
            'BOT', r'BBS-TRADE-BOT\nBOT', 'BBS-TRADE-BOT', 'joel', 'Treefidey'
        ]
        if (variable in noise_words):
            return False
        else:
            return True

    def filter_trader(self, variable):
        if ' ' in variable:
            variable = variable.replace(' ', '')
        if (variable in TRADERS):
            return True
        else:
            return False

    def remove_trader(self, variable):
        if variable:
            return True
        else:
            return False

    def mask_buy_price(self, price: str) -> str:
        '''
        Pads the buy price depending on value
        for added safety.
        '''
        # Set decimal rounding to .xx
        getcontext().prec = 3
        getcontext().rounding = ROUND_UP
        try:
            # First round of if's will check if the value to
            # the left of the decimal (if there is one) within
            # 2 different price brackets.
            if '.' in price:
                first_split_price = price.split('.')
                if first_split_price[0] == '':
                    # if the price is less than a dollar (.x or .xx)
                    # position [0] in the split will be empty.
                    # the following logic deals with the various
                    # mathematical situations that arise from this
                    # price range.
                    # all trades under a dollar gets padded with
                    # .01 to .03 cents
                    random_int = random.randint(1, 3)
                    if len(first_split_price[1]) == 2:
                        price = int(first_split_price[1]) + random_int
                        price = str(price)
                        if len(price) == 3:
                            second_split_price = list(price)
                            second_split_price.insert(1, '.')
                            price = ''.join(second_split_price)
                        elif len(price) == 2:
                            price = '.' + str(price)

                    elif len(first_split_price[1]) == 1:
                        price = '.' + first_split_price[1] + str(random_int)

                elif 3 <= int(first_split_price[0]) <= 5:
                    price = Decimal(float(price)) + Decimal(.01)

                elif 6 <= int(first_split_price[0]) <= 11:
                    price = Decimal(float(price)) + Decimal(.06)

                elif 12 <= int(first_split_price[0]) <= 21:
                    price = Decimal(float(price)) + Decimal(.11)

                price = str(price)
                if '.' in price and first_split_price[0] != '':
                    split_price = price.split('.')
                    # If price has one decimal point (x.x or xx.x) add a second spot x.x5
                    if len(split_price[1]) == 1:
                        split_price[1] = split_price[1] + '5'
                        price = '.'.join(split_price)

                    # If price has two decimal spots there are multiple techniques required.
                    if len(split_price[1]) == 2:
                        # If the second decimal spot is less than 5, round up to 5.
                        if int(split_price[1][1]) < 5:
                            price = split_price[0] + '.' + split_price[1][
                                0] + '5'

                        # If the second integer to the right of decimal
                        # is more than 5, and the first integer is 9
                        # add one to the number to the left of the decimal
                        if int(split_price[1]
                               [1]) >= 5 and split_price[1][0] == '9':
                            if split_price[0] == '':
                                price = '1'
                            else:
                                price = int(split_price[0]) + 1
                                price = str(price)

                        # if the second decimal spot is more than 5, and the first spot is less
                        # than 9, add 1 to the first spot, and make the second spot a 0.
                        if int(split_price[1][1]) >= 5 and int(
                                split_price[1][0]) < 9:
                            modified_int = int(split_price[1][0]) + 1
                            price = split_price[0] + '.' + str(
                                modified_int) + '0'

            elif '.' not in price:
                if len(price) == 3:
                    price = price + '.5'
                if len(price) < 3:
                    price = price + '.05'

        except ValueError as error:
            logger.error(f'{error} BUY PRICE MASKING VALUE ERROR',
                         exc_info=True)

        finally:
            return str(price)

    def mask_sell_price(self, price):
        try:
            if '.' in price:
                split_price = price.split('.')
                # If price has one decimal point (x.x or xx.x) add a second spot x.x5
                if len(split_price[1]) == 1:
                    split_price[1] = split_price[1] + '5'
                    price = '.'.join(split_price)

                # If price has two decimal spots there are multiple techniques required.
                if len(split_price[1]) == 2:
                    # If the second decimal spot is less than 5, round up to 5.
                    if int(split_price[1][1]) < 5:
                        price = split_price[0] + '.' + split_price[1][0] + '5'

                    # If the second integer to the right of decimal
                    # is more than 5, and the first integer is 9
                    # add one to the number to the left of the decimal
                    if int(split_price[1]
                           [1]) >= 5 and split_price[1][0] == '9':
                        if split_price[0] == '':
                            price = '1'
                        else:
                            price = int(split_price[0]) + 1
                            price = str(price)

                    # if the second decimal spot is more than 5, and the first spot is less
                    # than 9, add 1 to the first spot, and make the second spot a 0.
                    if int(split_price[1][1]) >= 5 and int(
                            split_price[1][0]) < 9:
                        modified_int = int(split_price[1][0]) + 1
                        price = split_price[0] + '.' + str(modified_int) + '0'

            elif '.' not in price:
                if len(price) == 3:
                    price = price + '.5'
                if len(price) < 3:
                    price = price + '.05'
        except ValueError as error:
            logger.error(f'{error} SELL PRICE MASKING VALUE ERROR',
                         exc_info=True)

        finally:
            return str(price)

    def release_trade(self, ticker, strike, expiration, call_or_put):
        '''
        1. Pads IN trades option price depending
        on value.
        2. Keeps trade in queue until live price
        hits padded price, then releases to post.
        '''
        try:
            converted_expiration = convert_date(expiration)
            if 'error' in (ticker, strike, expiration,
                           call_or_put) or converted_expiration == 'error':
                raise ReleaseTradeError

            if call_or_put == 'call':
                pass

        except:
            pass

    def bbs_discord_producer(self):
        try:
            global LAST_MESSAGE
            if DEBUG == 'dev' or 'dev_live':
                new_message = self.bbs_driver.find_elements_by_xpath(
                    "//*[@aria-label='bot-dev-talk (channel)']//div[@aria-label='Messages in bot-dev-talk']/child::div/child::div[@role='document']"
                )[-1].text
                # if len(new_message) < 3 or new_message.isdigit():
                #     new_message = driver.find_elements_by_xpath(
                #         "//*[@role='group']")[-2].text
            if DEBUG == 'bbs' or DEBUG is False:
                new_message = self.bbs_driver.find_elements_by_xpath(
                    "//div[contains(@data-list-item-id, 'chat-messages___chat-messages')]//div[starts-with(@class, 'container')]//div[starts-with(@class, 'embedWrapper')]//div[starts-with(@class, 'grid')]"
                )[-1].text
            if new_message != LAST_MESSAGE:
                config.new_unprocessed_trades.put(new_message)
                config.has_unprocessed_trade.release()
                EVENT.wait(.3)
                LAST_MESSAGE = new_message
            else:
                EVENT.wait(.3)
                return
        except TimeoutException as error:
            logger.fatal(
                f"{error}\n Message listener timed out while looking for latest message."
            )
            pass
        except (NoSuchElementException,
                StaleElementReferenceException) as error:
            logger.fatal(
                f"{error}\n Last message missing.  Probably received a reaction emoji"
            )
            pass
        except IndexError:
            pass

    def etwitter_producer(self):
        try:
            global LAST_ETWIT_MESSAGE
            new_etwit_message = self.etwitter_driver.find_elements_by_xpath(
                "//*[@class='js-chirp-container chirp-container']//p[@class='js-tweet-text tweet-text with-linebreaks ']"
            )[0].text
            if new_etwit_message != LAST_ETWIT_MESSAGE.replace("Etwit\n", ""):
                new_etwit_message = f"Etwit\n{new_etwit_message}"
                config.new_unprocessed_trades.put(new_etwit_message)
                config.has_unprocessed_trade.release()
                LAST_ETWIT_MESSAGE = new_etwit_message
            else:
                EVENT.wait(.2)
                return
        except TimeoutError as error:
            logger.fatal(f"TIMEOUT WHILE FINDING ETWIT MESSAGE XPATH",
                         exc_info=True)
            pass
        except (NoSuchElementException,
                StaleElementReferenceException) as error:
            logger.fatal(f"{error}\n Last etwit missing", exc_info=True)
            pass

    def etwit_standardizer(self, new_message):
        try:
            new_message = new_message[1].split(' ')
        except IndexError:
            new_message = new_message[0].split(' ')
            pass
        finally:
            return new_message

    def processor(self):
        while config.has_unprocessed_trade.acquire():
            new_message = config.new_unprocessed_trades.get()
            try:
                split_result = new_message.splitlines()
                # removes any empty strings from list
                split_result = list(filter(None, split_result))
                split_result = list(filter(self.filter_message, split_result))
                trade_author = list(filter(self.filter_trader, split_result))
                #testing reliability of this
                if trade_author == [] and '#ALERT' in split_result[0]:
                    trade_author = ['Etwit']
                trade_author_tup = trade_author[0]
                if trade_author_tup == "Etwit":
                    split_result = self.etwit_standardizer(split_result)
                if ' ' in trade_author_tup:
                    trade_author_tup = trade_author_tup.replace(' ', '')
                if "Jen" in trade_author_tup:
                    trade_author_tup = "Jen"
                # find the longest string left which is the message string
                if trade_author_tup != "Etwit":
                    longest_string = max(split_result, key=len)
                    double_split_result = longest_string.split(' - ')
                    double_split_result = list(
                        filter(None, double_split_result))
                    # gets a call or put status, and pops that matched entry out of the list
                    three_feet_results = self.three_feet(
                        double_split_result, self.get_stock_ticker)
                if trade_author_tup == "Etwit":
                    three_feet_results = self.three_feet(
                        split_result, self.get_stock_ticker)
                call_or_put_tup, strike_price_tup, stock_ticker_tup, double_split_result = three_feet_results

                if 'jen' in trade_author_tup.lower():
                    trade_expiration_tup, double_split_result = self.get_trade_expiration_from_shit_jen(
                        double_split_result)

                if not 'jen' in trade_author_tup.lower():
                    trade_expiration_tup, double_split_result = self.get_trade_expiration(
                        double_split_result)
                if trade_author_tup == 'Etwit' and trade_expiration_tup == 'error':
                    trade_expiration_tup = self.check.fetch_closest_expiration(
                        stock_ticker_tup)

                buy_price_tup, double_split_result = self.get_buy_price(
                    double_split_result)

                in_or_out_tup, double_split_result = self.get_in_or_out(
                    double_split_result)

                date_tup, time_tup = get_date_and_time()
                datetime_tup = standard_datetime()
                stock_ticker_tup = stock_ticker_tup.lower()
                color_tup = 'error_check'

                #check = ErrorChecker()

                error_tuple = (in_or_out_tup, stock_ticker_tup, datetime_tup,
                               strike_price_tup, call_or_put_tup,
                               buy_price_tup, trade_author_tup,
                               trade_expiration_tup, color_tup, date_tup,
                               time_tup)

                if buy_price_tup == strike_price_tup:
                    strike_price_tup, call_or_put_tup = self.check.strike_price_fixer(
                        double_split_result, error_tuple)

                    buy_price_tup, double_split_result = self.check.buy_price_fixer(
                        double_split_result, new_message)

                if 'error' in error_tuple:
                    if buy_price_tup == 'error':
                        buy_price_tup, double_split_result = self.check.buy_price_fixer(
                            double_split_result, new_message)

                    if strike_price_tup == 'error':
                        strike_price_tup, call_or_put_tup = self.check.strike_price_fixer(
                            double_split_result, error_tuple)

                    if trade_expiration_tup == 'error':
                        trade_expiration_tup = self.check.expiration_fixer(
                            double_split_result, error_tuple)

                    if call_or_put_tup == 'error':
                        call_or_put_tup = self.check.call_or_put_fixer(
                            double_split_result, error_tuple)

                    if in_or_out_tup == 'error':
                        print(f'ERROR IN_OR_OUT {in_or_out_tup}')

                live_buy_price = 'error'
                if 'error' not in (strike_price_tup, stock_ticker_tup,
                                   trade_expiration_tup, call_or_put_tup
                                   ) and 'error' in buy_price_tup:
                    buy_price_tup = self.check.live_buy_price(
                        stock_ticker_tup, strike_price_tup,
                        trade_expiration_tup, call_or_put_tup)
                if not 'error' in (strike_price_tup, stock_ticker_tup,
                                   trade_expiration_tup, call_or_put_tup):
                    live_buy_price = self.check.live_buy_price(
                        stock_ticker_tup, strike_price_tup,
                        trade_expiration_tup, call_or_put_tup)
                    logger.info(f"{live_buy_price} LIVE PRICE")
                    logger.info(f"{buy_price_tup} TRADE PRICE")
                # checks if the expiration is valid given the ticker, strike, expiration and call_or_put
                # values are not 'error'.
                if not 'error' in (stock_ticker_tup, strike_price_tup,
                                   trade_expiration_tup, call_or_put_tup):
                    trade_expiration_tup = self.check.live_expiration(
                        stock_ticker_tup, strike_price_tup,
                        trade_expiration_tup, call_or_put_tup)
                if buy_price_tup.isalpha() is False and live_buy_price.isalpha(
                ) is False:
                    price_difference = percent_difference(
                        float(live_buy_price), float(buy_price_tup))

                    if price_difference > 200 and in_or_out_tup == 'out':
                        buy_price_tup = live_buy_price
                        logger.error(
                            r"Last option price differs more than 25% from traders price! Using live.."
                        )
                    elif price_difference > 200 and in_or_out_tup == 'in':
                        buy_price_tup = 'error'
                        logger.error(
                            r"Last option price differs more than 25% from traders price! Ignoring trade.."
                        )

                #trade_expiration_tup = self.check.

                trade_tuple = (in_or_out_tup, stock_ticker_tup, datetime_tup,
                               strike_price_tup, call_or_put_tup,
                               buy_price_tup, trade_author_tup,
                               trade_expiration_tup, color_tup, date_tup,
                               time_tup)

                if 'error' in trade_tuple:
                    error_tuple = (in_or_out_tup, stock_ticker_tup,
                                   datetime_tup, strike_price_tup,
                                   call_or_put_tup, buy_price_tup,
                                   trade_author_tup, trade_expiration_tup,
                                   color_tup, 'false', date_tup, time_tup)
                    logger.error(
                        f'This trade contains error(s)! : {error_tuple}')
                    update_error_table(error_tuple)

                elif 'error' not in trade_tuple:
                    ignore_trade, trade_color_choice = verify_trade(
                        list(trade_tuple))
                    if ignore_trade:
                        return

                    elif ignore_trade is False:
                        if in_or_out_tup == 'in':
                            buy_price_tup = self.mask_buy_price(buy_price_tup)
                        if in_or_out_tup == 'out':
                            buy_price_tup = self.mask_sell_price(buy_price_tup)
                        valid_trade = (in_or_out_tup, stock_ticker_tup,
                                       datetime_tup, strike_price_tup,
                                       call_or_put_tup, buy_price_tup,
                                       trade_author_tup, trade_expiration_tup,
                                       trade_color_choice, date_tup, time_tup)
                        logger.info(
                            f"Producer received a fresh trade : {valid_trade}")
                        trade_id = update_table(valid_trade)
                        message = (trade_id, valid_trade)
                        config.new_trades.put(message)
                        config.has_trade.release()
                        config.new_discord_trades.put(message)
                        config.has_new_discord_trade.release()

            except (KeyError, ValueError) as error:
                print(f"\n{error}")
                pass

            except IndexError:
                pass
