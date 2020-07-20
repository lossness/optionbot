import sqlite3
import os
import re
import random

import pandas as pd
from make_image import text_on_img
from exceptions import DuplicateTrade, TradeAlreadyOut, IsAInTrade, DatabaseEmpty, MultipleMatchingIn
from main_logger import logger

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
    is_out = True
    try:
        if database_trades == []:
            is_out = False
            raise DatabaseEmpty

        search_criteria = (
            'out', ) + new_trade[1:2] + new_trade[3:4] + new_trade[6:8]
        for row in database_trades:
            if row == search_criteria:
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
        common_trade_features_tup = new_trade[:2] + new_trade[3:5] + new_trade[
            6:]
        in_or_out, ticker, strike_price, call_or_put, trader, expiration = common_trade_features_tup
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
    try:
        if database_trades == []:
            raise DatabaseEmpty

        in_or_out, ticker, date_time, strike_price, call_or_put, buy_price, user_name, expiration = new_trade
        ticker = ticker.lower()
        matched_trades = re.findall(
            rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'), (\'\w+\'))\)',
            str(database_trades))

        if len(matched_trades) == 1:
            match_exists = True

        elif len(matched_trades) > 1:
            raise MultipleMatchingIn

    except DatabaseEmpty as info_error:
        logger.info(info_error)
        pass

    except MultipleMatchingIn as error:
        logger.error(error)
        match_exists = True

    finally:
        return match_exists


def ignore_out_trade(database_trades: list, new_trade: tuple) -> bool:
    in_trade_exists = True
    try:
        if database_trades == []:
            raise DatabaseEmpty

        in_or_out, ticker, date_time, strike_price, call_or_put, buy_price, user_name, expiration = new_trade
        ticker = ticker.lower()
        matched_trades = re.findall(
            rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'), (\'\w+\'))\)',
            str(database_trades))

        if matched_trades == []:
            in_trade_exists = False

    except DatabaseEmpty as info_error:
        in_trade_exists = False

    finally:
        return in_trade_exists


def verify_trade(parsed_trade: tuple):
    try:
        is_out = False
        is_duplicate = False
        has_matching_in = None
        trade_color = None
        ignore_trade = False
        con = db_connect()
        cur = con.cursor()
        filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration, color from trades"
        filtered_trades_no_color_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration from trades"
        cur.execute(filtered_trades_sql)
        filtered_trades = cur.fetchall()
        cur.execute(filtered_trades_no_color_sql)
        filtered_trades_no_color = cur.fetchall()

        is_out = is_trade_already_out(filtered_trades_no_color,
                                      tuple(parsed_trade))

        is_duplicate = duplicate_check(filtered_trades_no_color,
                                       tuple(parsed_trade))

        has_matching_in = has_trade_match(filtered_trades, tuple(parsed_trade))

        if 'out' in parsed_tuple[0]:
            ignore_trade = ignore_out_trade(filtered_trades_no_color,
                                            tuple(parsed_trade))

        if has_matching_in is False:
            colors = [
                'red', 'blue', 'green', 'yellow', 'orange', 'white', 'purple',
                'pink'
            ]
            trade_color = random.choice(colors)

    except sqlite3.Error as error:
        logger.warning(error)
        verification_tuple = ('error', 'error', 'error', 'error')
        return verification_tuple

    finally:
        if (con):
            con.close()
        verification_tuple = (is_duplicate, is_out, has_matching_in,
                              trade_color, ignore_trade)
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