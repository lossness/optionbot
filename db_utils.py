import sqlite3
import os
import re
import random
import math

import pandas as pd
from make_image import text_on_img
from exceptions import DuplicateTrade, TradeAlreadyOut, IsAInTrade, DatabaseEmpty, MultipleMatchingIn, IgnoreTrade, DateConversionError
from main_logger import logger
from datetime import datetime

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')


def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con


def create_table():
    con = db_connect()
    cur = con.cursor()

    traders_sql = """
    CREATE TABLE traders (
        id integer PRIMARY KEY,
        user_name text NOT NULL)"""

    cur.execute(traders_sql)

    trades_sql = """
    CREATE TABLE trades (
        id integer PRIMARY KEY,
        in_or_out text NOT NULL,
        ticker text NOT NULL,
        datetime text NOT NULL,
        option_price text NOT NULL,
        call_or_put text NOT NULL,
        buy_price text NOT NULL,
        user_name text NOT NULL,
        color text NOT NULL,
        FOREIGN KEY (user_name) REFERENCES traders (id))"""

    cur.execute(trades_sql)


def is_trade_already_out(database_trades: list, new_trade: tuple) -> bool:
    '''
    This checks if the trade already has one IN and one OUT
    trade. Returns True or False.
    '''
    is_out = False
    try:
        if database_trades == []:
            is_out = False
            raise DatabaseEmpty

        search_criteria = (
            'out', ) + new_trade[1:2] + new_trade[3:5] + new_trade[6:]
        if search_criteria in database_trades:
            is_out = True
            raise TradeAlreadyOut

    except (DatabaseEmpty, TradeAlreadyOut) as info_error:
        logger.info(info_error)

    finally:
        return is_out


def duplicate_check(database_trades: list, new_trade: tuple) -> bool:
    '''
    This will check if the trade is in the database already.
    returns True or False.
    '''
    is_duplicate = True
    if database_trades == []:
        is_duplicate = False
        return is_duplicate
    try:
        in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, trader, expiration, color = new_trade
        matched_trades = re.findall(
            rf'\(((?:\'{in_or_out}\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{trader}\'), (\'{expiration}\'))\)',
            str(database_trades))
        if matched_trades == []:
            is_duplicate = False

    except (KeyError, ValueError, IndexError) as error:
        logger.warning(f"{error} during duplicate trade check!")
        is_duplicate = True

    finally:
        return is_duplicate


def has_trade_match(database_trades: list, new_trade: tuple) -> bool:
    '''
    This will check the database for a matching IN trade and return
    True or False depending if matched.
    '''
    match_exists = False
    trade_color = 'error_in_has_trade_match'
    try:
        if database_trades == []:
            raise DatabaseEmpty

        in_or_out, ticker, date_time, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade
        ticker = ticker.lower()
        matched_trades = re.findall(
            rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'{expiration}\'), (\'\w+\'))\)',
            str(database_trades))

        if len(matched_trades) == 1:
            existing_color = matched_trades[0][7]
            trade_color = existing_color.replace("'", "")
            match_exists = True

        elif len(matched_trades) > 1:
            raise MultipleMatchingIn

    except DatabaseEmpty as info_error:
        logger.info(info_error)

    except MultipleMatchingIn as error:
        logger.error(error)
        match_exists = False

    finally:
        return match_exists, trade_color


def verify_trade(parsed_trade: tuple):
    try:
        is_out = False
        is_duplicate = False
        has_matching_in = False
        trade_color = 'filler'
        ignore_trade = False
        con = db_connect()
        cur = con.cursor()
        filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration, color from trades"
        filtered_trades_no_color_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration from trades"
        cur.execute(filtered_trades_sql)
        filtered_trades = cur.fetchall()
        cur.execute(filtered_trades_no_color_sql)
        filtered_trades_no_color = cur.fetchall()

        is_duplicate = duplicate_check(filtered_trades_no_color,
                                       tuple(parsed_trade))

        if is_duplicate:
            ignore_trade = True
            raise DuplicateTrade

        is_out = is_trade_already_out(filtered_trades_no_color,
                                      tuple(parsed_trade))

        if is_out is True:
            raise TradeAlreadyOut

        if is_out is False and 'out' in parsed_trade[0]:
            has_matching_in, trade_color = has_trade_match(
                filtered_trades, tuple(parsed_trade))
            if has_matching_in is False:
                raise IgnoreTrade

        # for testing
        if filtered_trades == [] and 'in' in parsed_trade[0]:
            colors = [
                'MK1', 'MK2', 'MK3', 'MK4', 'MK5', 'MK6', 'MK7', 'MK8', 'MK9',
                'MK10', 'MK11', 'MK12'
            ]
            trade_color = random.choice(colors)
            ignore_trade = False

        if has_matching_in is False:
            colors = [
                'MK1', 'MK2', 'MK3', 'MK4', 'MK5', 'MK6', 'MK7', 'MK8', 'MK9',
                'MK10', 'MK11', 'MK12'
            ]
            trade_color = random.choice(colors)

    except sqlite3.Error as error:
        logger.warning(error)
        is_out = 'error'
        is_duplicate = 'error'
        has_matching_in = 'error'
        trade_color = 'error'
        ignore_trade = True

    except (DuplicateTrade, TradeAlreadyOut, IgnoreTrade):
        is_out = 'ignore'
        is_duplicate = True
        has_matching_in = 'ignore'
        trade_color = 'ignore'
        ignore_trade = True

    finally:
        if (con):
            con.close()
        verification_tuple = (ignore_trade, trade_color)
        return verification_tuple


def update_table(parsed_trade: tuple):
    try:
        con = db_connect()
        cur = con.cursor()
        trade_sql = "INSERT INTO trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(trade_sql,
                    (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                     parsed_trade[3], parsed_trade[4], parsed_trade[5],
                     parsed_trade[6], parsed_trade[7], parsed_trade[8]))
        con.commit()
        print("Trade added to the database ")
        print(parsed_trade)
        cur.close()
    except sqlite3.Error as error:
        print("Failed to update trade in sqlite table", error)
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()
            # print("the sqlite connection is closed")


def update_error_table(parsed_trade: tuple):
    try:
        con = db_connect()
        cur = con.cursor()
        trade_sql = "INSERT INTO error_trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(trade_sql,
                    (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                     parsed_trade[3], parsed_trade[4], parsed_trade[5],
                     parsed_trade[6], parsed_trade[7], parsed_trade[8]))
        con.commit()
        print("Trade added to the database ")
        print(parsed_trade)
        cur.close()
    except sqlite3.Error as error:
        print("Failed to update trade in sqlite table", error)
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()
            # print("the sqlite connection is closed")


def create_trader(trader: str):
    try:
        con = db_connect()
        cur = con.cursor()
        # Check if trader is already in database
        check_trader_sql = ''' SELECT user_name FROM traders WHERE user_name=? '''
        cur.execute(check_trader_sql, [trader])
        trader_exists = cur.fetchone()
        if trader_exists:
            raise KeyError("Trader already exists")

        # Trader not in database, adds trader
        else:
            add_trader_sql = ''' INSERT INTO traders (user_name) VALUES (?) '''
            cur.execute(add_trader_sql, [trader])
            con.commit()
            print("Trader added successfully ")
            cur.close()

    except sqlite3.Error as error:
        print("Failed to add trader to sqlite table", error)

    except KeyError as error:
        print("Trader already in database", error)

    finally:
        if (con):
            con.close()
            print("the sqlite connection is closed")


def check_expration(error_trades: list, all_trades: list):
    pass


def check_call_or_put(error_trades: list, all_trades: list):
    for trade in error_trades:
        (in_or_out, ticker, strike_price, call_or_put, buy_price, user_name,
         expiration) = trade
        if 'error' in (strike_price, call_or_put):
            try:
                ticker = ticker.lower()
                matched_trades = re.findall(
                    rf'\(((?:[\'in\', \'out\'])+, (\'{ticker}\'), (\'{user_name}\'), (\'{expiration}\'))\)',
                    str(all_trades))

            finally:
                pass


def check_strike_price(trades: list, all_trades: list):
    pass


def check_ticker(trades: list, all_trades: list):
    pass


def error_checker():
    try:
        con = db_connect()
        cur = con.cursor()
        load_trades_table_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, buy_price, user_name, expiration from trades"
        cur.execute(load_trades_table_sql)
        full_trades = cur.fetchall()
        trades_with_errors = []
        for row in full_trades:
            if 'error' in row:
                trades_with_errors.append(row)
        print(trades_with_errors)
        check_call_or_put(trades_with_errors, full_trades)

    finally:
        if (con):
            con.close()
            print("Error check completed.")


def convert_date(date):
    try:
        split_date = date.split('/')
        month = split_date[0]
        day = split_date[1]
        if len(split_date) == 3:
            year = split_date[2]
        else:
            year = '2020'
        if len(year) == 2:
            year = '20' + year
        if len(day) == 1:
            day = '0' + day
        if len(month) == 1:
            month = '0' + month
        converted_date = f"{month}/{day}/{year}"

    except (TypeError, ValueError, KeyError) as error:
        logger.error(f"{error}", exc_info=True)
        converted_date = 'error'

    finally:
        return converted_date


def convert_date_to_text(date):
    try:
        split_date = date.split('/')
        month = split_date[0]
        day = split_date[1]
        if len(split_date) == 3:
            year = split_date[2]
        else:
            year = '2020'
        if len(year) == 2:
            year = '20' + year
        if len(day) == 1:
            day = '0' + day
        if len(month) == 1:
            month = '0' + month
        date = f"{month}-{day}-{year}"
        date_object = datetime.strptime(date, "%m-%d-%Y")
        converted_date = date_object.strftime("%B %d, %Y")

    except (TypeError, ValueError, KeyError) as error:
        logger.error(f"{error}", exc_info=True)
        converted_date = 'error'

    finally:
        return converted_date


def mask_buy_price(price):
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
                if int(split_price[1][1]) >= 5 and split_price[1][0] == '9':
                    if split_price[0] == '':
                        price = '1'
                    else:
                        price = int(split_price[0]) + 1
                        price = str(price)

                # if the second decimal spot is more than 5, and the first spot is less
                # than 9, add 1 to the first spot, and make the second spot a 0.
                if int(split_price[1][1]) >= 5 and int(split_price[1][0]) < 9:
                    modified_int = int(split_price[1][0]) + 1
                    price = split_price[0] + '.' + str(modified_int) + '0'

        elif '.' not in price:
            if len(price) == 3:
                price = price + '.5'
            if len(price) < 3:
                price = price + '.05'

    except ValueError as error:
        logger.fatal(f'{error} BUY PRICE MASKING VALUE ERROR', exc_info=True)

    finally:
        return price
