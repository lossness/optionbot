import re
import logging

from selenium.common.exceptions import NoSuchElementException


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