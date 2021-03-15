import sqlite3
import os
import re
import random
import math

import pandas as pd
import config
from exceptions import DuplicateTrade, TradeAlreadyOut, IsAInTrade, DatabaseEmpty, MultipleMatchingIn, IgnoreTrade, DateConversionError
from main_logger import logger
from datetime import datetime

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')
DEBUG = config.DEBUG


def db_connect(db_path=DEFAULT_PATH):
    """Takes the default path of the SQL trade database, creates
    a connection, and returns the connection object"""

    con = sqlite3.connect(db_path)
    return con


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
    """
    This checks if newly scraped trade is in the database already.

    'database_trades': contains all trades inside the SQL database
    'new_trade': the newly scraped trade

    Runs a RegEx findall match on 'database_trades' with 'new_trade' as the
     pattern and returns a boolean if the trade is already recorded in the database.
    """

    is_duplicate = True
    if database_trades == []:
        is_duplicate = False
        return is_duplicate
    try:
        in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, trader, expiration, color, date, time = new_trade
        matched_trades = re.findall(
            rf'\(((?:\'{in_or_out}\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{trader}\'), (\'{expiration}\'), (\'{date}\'))\)',
            str(database_trades))
        if matched_trades == []:
            is_duplicate = False

    except (KeyError, ValueError, IndexError) as error:
        logger.warning(f"{error} during duplicate trade check!")
        is_duplicate = True

    finally:
        return is_duplicate


def has_trade_match(database_trades: list, new_trade: tuple) -> bool, str:
    """
    This checks if a new trade has a matching trade recorded in the database
    with the 'in_or_out' variable equal to 'IN' and returns a bool and that 
    trades color.

    'trade_color': Set if a trade match is found. Equal to 'color' variable in 
    matching database trade.
    

    """
    match_exists = False
    trade_color = 'error_in_has_trade_match'
    try:
        if database_trades == []:
            raise DatabaseEmpty

        in_or_out, ticker, date_time, strike_price, call_or_put, buy_price, user_name, expiration, color, date, time = new_trade
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
        logger.info(
            f"db_utils | has_trade_match function | {new_trade} | {match_exists} | {trade_color}"
        )
        return match_exists, trade_color


def trade_currently_open(database_trades: list, new_trade: tuple) -> bool:
    '''
    Checks if a trade with the same ticker and expiration has a IN
    in the database and does not have a matching out yet
    '''
    try:
        currently_open = True
        if database_trades == []:
            raise DatabaseEmpty
        in_or_out, ticker, date_time, strike_price, call_or_put, buy_price, user_name, expiration, color, date, time = new_trade
        ticker = ticker.lower()
        matched_trades = re.findall(
            rf'\(((\'\w+\'), (\'{ticker}\'), (\'\d+\'), (\'\w+\'), (\'\w+\'), (\'{expiration}\'), \'([\d]+-[\d]+-[\d]+)\')\)',
            str(database_trades))

        if len(matched_trades) == 0:
            currently_open = False

    except DatabaseEmpty as info_error:
        logger.info(info_error)

    finally:
        return currently_open


def is_posted_to_insta(new_trade: tuple) -> str:
    '''
    Called during insta posting phase on out trades. Checks if
    the matching IN trade was posted.
    '''
    try:
        insta_posted = "false"
        con = db_connect()
        cur = con.cursor()
        database_search_parameters = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration, insta_posted from trades"
        in_or_out, ticker, date_time, strike_price, call_or_put, buy_price, user_name, expiration, color, date, time = new_trade
        cur.execute(database_search_parameters)
        filtered_trades = cur.fetchall()
        #matched_trades = re.findall(
        #    rf'\((\'(in)\', \'({ticker})\', \'([\d]{{4}}-[\d]{{2}}-[\d]{{2}}\s[\d]{{2}}:[\d]{{2}}:[\d]{{2}}.[\d]+)\', \'({strike_price})\', \'({call_or_put})\', \'([\d]*.[\d]*)\', \'({user_name})\', \'({expiration})\', \'(\w+)\', \'(true)\', \'([\d]+-[\d]+-[\d]+)\', \'([\d]+:[\d]+:[\d]+)\')\)',
        #    str(filtered_trades))
        #matched_trades = re.findall(
        #    rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'{expiration}\'), (\'\true\'))\)',
        #    str(filtered_trades))
        search_criteria = ("in", ticker, strike_price, call_or_put, user_name,
                           expiration, "true")
        if str(search_criteria) in str(filtered_trades):
            insta_posted = "true"

    except DatabaseEmpty as info_error:
        logger.info(info_error)

    finally:
        if (con):
            con.close()
        return insta_posted


def db_insta_posting_successful(trade_id: str):
    try:
        con = db_connect()
        cur = con.cursor()
        update_sql = ''' UPDATE trades SET insta_posted = ? WHERE id = ? '''
        data = ("true", trade_id)
        cur.execute(update_sql, data)
        con.commit()

    except sqlite3.Error as error:
        logger.error(f"{error}", exc_info=True)

    except KeyError as error:
        logger.error("Trader already in database", exc_info=True)

    finally:
        if (con):
            con.close()


def prune_completed_trades():
    '''
    1. Queries all trades by the following parameters,
    ticker, strike_price, call_or_put, user_name, expiration
    2. Adds all trades with these parameters that have 2 entries.
    3. Inserts the trades into the completed_trades table and removes
    them from the 'trades' table. 
    '''
    try:
        con = db_connect()
        cur = con.cursor()
        sql_filter = "SELECT ticker, strike_price, call_or_put, user_name, expiration from trades"
        cur.execute(sql_filter)
        all_trades = cur.fetchall()
        duplicate_list = []
        for item in all_trades:
            if all_trades.count(item) >= 2:
                duplicate_list.append(item)

        retreive_all_trades_sql = "SELECT in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, insta_posted, date, time from trades"
        cur.execute(retreive_all_trades_sql)
        all_trades = cur.fetchall()
        completed_trades = []
        for trade in duplicate_list:
            ticker, strike_price, call_or_put, user_name, expiration = trade
            matched_trades = re.findall(
                rf'\((\'(\w+)\', \'({ticker})\', \'([\d]{{4}}-[\d]{{2}}-[\d]{{2}}\s[\d]{{2}}:[\d]{{2}}:[\d]{{2}}.[\d]+)\', \'({strike_price})\', \'({call_or_put})\', \'([\d]*.[\d]*)\', \'({user_name})\', \'({expiration})\', \'(\w+)\', \'(\w+)\', \'([\d]+-[\d]+-[\d]+)\', \'([\d]+:[\d]+:[\d]+)\')\)',
                str(all_trades))
            if len(matched_trades) > 0:
                for trade in matched_trades:
                    completed_trades.append(tuple(trade))
        completed_trades = list(set(completed_trades))
        if DEBUG == False:
            for completed_trade in completed_trades:
                update_completed_table(tuple(completed_trade[1:]))
                logger.info(
                    f"{completed_trade} added to completed_trades table")
                delete_from_open_trades(tuple(completed_trade[1:]))
                logger.info(f"{completed_trade} deleted from live table")
        else:
            for completed_trade in completed_trades:
                delete_from_open_trades(tuple(completed_trade[1:]))
                print(f"{completed_trade} deleted from live table")

    except sqlite3.Error as error:
        logger.error(f"{error}", exc_info=True)
    finally:
        if (con):
            con.close()


def get_open_trades() -> tuple:
    '''
    Queries open trade sql database and returns
    a tuple of trades that have not been exited 
    yet.
    '''
    try:
        con = db_connect()
        cur = con.cursor()
        open_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, expiration from trades"
        cur.execute(open_trades_sql)
        open_trades = cur.fetchall()
    except sqlite3.Error as error:
        logger.fatal(f"{error}", exc_info=True)
    finally:
        return tuple(open_trades)


def verify_trade(parsed_trade: tuple, trade_comments):
    ''
    try:
        is_out = False
        is_duplicate = False
        has_matching_in = False
        trade_color = 'filler'
        ignore_trade = False
        con = db_connect()
        cur = con.cursor()
        filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration, color from trades"
        filtered_trades_no_color_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration, date from trades"
        cur.execute(filtered_trades_sql)
        filtered_trades = cur.fetchall()
        cur.execute(filtered_trades_no_color_sql)
        filtered_trades_no_color = cur.fetchall()

        if 'in' in parsed_trade[0]:
            is_currently_open = trade_currently_open(filtered_trades_no_color,
                                                     tuple(parsed_trade))
            if is_currently_open and 'Etwit' not in parsed_trade:
                ignore_trade = True
                raise IgnoreTrade

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

        #if 'in' in parsed_trade[0] and 'jen' in parsed_trade[6].lower(
        #) and 'risk' in trade_comments.lower():
        #    raise IgnoreTrade
        if 'in' in parsed_trade[0] and 'jen' in parsed_trade[6].lower():
            raise IgnoreTrade
        # for testing
        if 'in' in parsed_trade[0] and 'kang' in parsed_trade[6].lower():
            raise IgnoreTrade
        if 'in' in parsed_trade[0] and 'maria' in parsed_trade[6].lower():
            raise IgnoreTrade

        if filtered_trades == [] and 'in' in parsed_trade[0]:
            colors = [
                'FA1', 'FA2', 'FA3', 'FA4', 'FA5', 'FA6', 'FA7', 'FA8', 'FA9',
                'FA10', 'FA11', 'FA12', 'FA13', 'FA14'
            ]
            trade_color = random.choice(colors)
            ignore_trade = False

        if has_matching_in is False:
            colors = [
                'FA1', 'FA2', 'FA3', 'FA4', 'FA5', 'FA6', 'FA7', 'FA8', 'FA9',
                'FA10', 'FA11', 'FA12', 'FA13', 'FA14'
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


def update_table(parsed_trade: tuple) -> str:
    '''
    Updates the database with a trade.

    Returns: the trades unique ID in database.
    '''
    try:
        trade_id = ''
        con = db_connect()
        cur = con.cursor()
        trade_sql = "INSERT INTO trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, date, time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(trade_sql,
                    (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                     parsed_trade[3], parsed_trade[4], parsed_trade[5],
                     parsed_trade[6], parsed_trade[7], parsed_trade[8],
                     parsed_trade[9], parsed_trade[10]))
        con.commit()
        logger.info(f"Trade added to database!\n{parsed_trade}")
        trade_id = str(cur.lastrowid)
        cur.close()
    except sqlite3.Error as error:
        logger.fatal(f"Failed to update trade in sqlite table\n{error}")
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()
            return trade_id
            # print("the sqlite connection is closed")


def delete_from_open_trades(parsed_trade: tuple):
    '''
    Deletes a given trade from the live table named 'trades'
    '''
    try:
        con = db_connect()
        cur = con.cursor()
        trade_sql = "DELETE FROM trades where (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, insta_posted, date, time) = (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(trade_sql,
                    (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                     parsed_trade[3], parsed_trade[4], parsed_trade[5],
                     parsed_trade[6], parsed_trade[7], parsed_trade[8],
                     parsed_trade[9], parsed_trade[10], parsed_trade[11]))
        con.commit()
        logger.info(f"{parsed_trade} deleted from live table trades")
        cur.close()
    except sqlite3.Error as error:
        logger.fatal(f"{error}")
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()


def update_error_table(parsed_trade: tuple):
    try:
        con = db_connect()
        cur = con.cursor()
        trade_sql = "INSERT INTO error_trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, insta_posted, date, time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(trade_sql,
                    (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                     parsed_trade[3], parsed_trade[4], parsed_trade[5],
                     parsed_trade[6], parsed_trade[7], parsed_trade[8],
                     parsed_trade[9], parsed_trade[10], parsed_trade[11]))
        con.commit()
        logger.error(f"ERROR_TABLE: Trade added {parsed_trade}")
        cur.close()
    except sqlite3.Error as error:
        logger.fatal(f"{error}")
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()
            # print("the sqlite connection is closed")


def update_completed_table(parsed_trade: tuple):
    try:
        con = db_connect()
        cur = con.cursor()
        trade_sql = "INSERT INTO completed_trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, insta_posted, date, time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(trade_sql,
                    (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                     parsed_trade[3], parsed_trade[4], parsed_trade[5],
                     parsed_trade[6], parsed_trade[7], parsed_trade[8],
                     parsed_trade[9], parsed_trade[10], parsed_trade[11]))
        con.commit()
        cur.close()
        logger.info(f"COMPLETED TRADE TABLE: Trade added: {parsed_trade}")
    except sqlite3.Error as error:
        logger.fatal(f"{error}")
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()


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


def convert_date(date) -> str:
    '''
    Converts an expiration date like 10/23 to the format
    10/23/2020.
    '''
    try:
        split_date = date.split('/')
        month = split_date[0]
        day = split_date[1]
        year = '2020'
        if len(split_date) == 3:
            year = split_date[2]
        if month.isalpha():
            if 'DEC' not in month.lower():
                year = '2021'
        if month.isdigit():
            if int(month) != 12:
                year = '2021'
        if len(year) == 2:
            year = '20' + year
        if len(day) == 1:
            day = '0' + day
        if len(month) == 1:
            month = '0' + month
        converted_date = f"{month}/{day}/{year}"

    except (TypeError, ValueError, KeyError, IndexError) as error:
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

    except (TypeError, ValueError, KeyError, IndexError) as error:
        logger.error(f"{error}", exc_info=True)
        converted_date = 'error'

    finally:
        return converted_date


#Dev functions / first time creation

def create_table():
    """Recreates both existing tables 'traders, trades'."""
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
        posted text NOT NULL,
        FOREIGN KEY (user_name) REFERENCES traders (id))"""

    cur.execute(trades_sql)