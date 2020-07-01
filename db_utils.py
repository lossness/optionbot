import sqlite3
import os
import re
import logging

import pandas as pd
from make_image import text_on_img

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
        option_price real NOT NULL,
        call_or_put text NOT NULL,
        buy_price real NOT NULL,
        user_name text,
        FOREIGN KEY (user_name) REFERENCES traders (id))"""

    cur.execute(trades_sql)


def is_trade_already_out(trade_table, parsed_trade) -> bool:
    try:
        already_out_trade = False
        if trade_table == []:
            print("DATABASE EMPTY LOL")
            return False
        out_trade_filtered = (
            'out',
        ) + parsed_trade[1:2] + parsed_trade[3:4] + parsed_trade[6:8]
        for row in trade_table:
            if row == out_trade_filtered:
                raise KeyError("Trade already exited!")
        return already_out_trade

    except KeyError as e:
        pass
        already_out_trade = True
        return already_out_trade


def is_duplicate(trade_table, parsed_trade) -> bool:
    try:
        is_duplicate_trade = False
        if trade_table == []:
            print("DATABASE EMPTY LOL")
            return False
        n = 2
        parsed_trade_without_datetime = parsed_trade[:n] + parsed_trade[n + 1:]
        for row in trade_table:
            if row == parsed_trade_without_datetime:
                is_duplicate_trade = True
    finally:
        pass


def out_and_duplicate_check(parsed_trade: tuple) -> bool:
    try:
        con = db_connect()
        cur = con.cursor()
        load_filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration from trades"
        cur.execute(load_filtered_trades_sql)
        filtered_trades = cur.fetchall()
        trade_already_exited = is_trade_already_out(filtered_trades,
                                                    parsed_trade)
        load_trades_table_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, buy_price, user_name, expiration from trades"
        cur.execute(load_trades_table_sql)
        full_trades = cur.fetchall()
        if trade_already_exited:
            return True
        is_duplicate = False
        n = 2
        trade_tuple_without_datetime = parsed_trade[:n] + parsed_trade[n + 1:]
        for row in full_trades:
            if row == trade_tuple_without_datetime:
                is_duplicate = True
                return is_duplicate
        if is_duplicate is False and trade_already_exited is False:
            return False
    except sqlite3.Error as error:
        logging.warning(error)
    finally:
        if (con):
            con.close()


def update_table(parsed_trade: tuple):
    try:
        con = db_connect()
        cur = con.cursor()
        load_filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration from trades"
        cur.execute(load_filtered_trades_sql)
        filtered_trades = cur.fetchall()
        trade_already_exited = is_trade_already_out(filtered_trades,
                                                    parsed_trade)
        load_trades_table_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, buy_price, user_name, expiration from trades"
        cur.execute(load_trades_table_sql)
        full_trades = cur.fetchall()
        is_duplicate = False
        n = 2
        trade_tuple_without_datetime = parsed_trade[:n] + parsed_trade[n + 1:]
        for row in full_trades:
            if row == trade_tuple_without_datetime:
                is_duplicate = True
                raise KeyError("Duplicate trade detected!")

        if is_duplicate is False and trade_already_exited is False:
            trade_sql = "INSERT INTO trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(trade_sql,
                        (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                         parsed_trade[3], parsed_trade[4], parsed_trade[5],
                         parsed_trade[6], parsed_trade[7]))
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