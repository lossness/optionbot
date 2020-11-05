import re
import sqlite3
import yfinance as yf
import requests
import os
import json

from datetime import datetime

from main_logger import logger
from db_utils import db_connect, convert_date
from time_utils import standard_datetime
from exceptions import *


class ErrorChecker:
    '''
    Level 2 checks for all values of a
    trade that did not pass initial processing.
    
    Attributes
    ----------
    processed_list : list
        The end result of the inital trade message
        after having all successful algorithms 
        remove required data.

    
    Methods
    -------
    strike_price(processed_list)
    call_or_put(processed_list)
    '''
    '''
    Parameters
    ----------
    processed_list : list
    The end result of the inital trade message
    after having all successful algorithms
    remove required data
    '''
    def __init__(self):
        self.processed_list = []
        self.new_trade_tuple = ()

    def fetch_database(self):
        '''
        Fetches all trades in the database minus the
        datetime column.
        Values: in_or_out, ticker, strike_price, call_or_put, user_name, expiration, color
        '''
        try:
            con = db_connect()
            cur = con.cursor()
            filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration, color from trades"
            cur.execute(filtered_trades_sql)
            filtered_trades = cur.fetchall()
        except sqlite3.Error as error:
            logger.fatal(f'Houston we have a fucking {error}!', exc_info=1)
        finally:
            if (con):
                con.close()
            return filtered_trades

    def fetch_matchable_in_trades(self, new_trade):
        '''
        Fetches all trades by the unique
        values that distinguishes one trade
        from another trade for matching purposes.
        '''
        try:
            con = db_connect()
            cur = con.cursor()
            filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration from trades"
            cur.execute(filtered_trades_sql)
            filtered_trades = cur.fetchall()
            in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade

            if filtered_trades == []:
                raise DatabaseEmpty

            matched_in_trade = re.findall(
                rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'{expiration}\'))',
                str(filtered_trades))

            if matched_in_trade == [] and len(matched_in_trade) > 1:
                matched_in_trade = 'error'

        except sqlite3.Error as error:
            logger.fatal(f'{error}', stack_info=True)

        except DatabaseEmpty as error:
            logger.warning(error, stack_info=True)

        finally:
            if (con):
                con.close()
            return matched_in_trade

    def fetch_matchable_trades(self):
        '''
        Fetches all trades by the unique
        values that distinguishes one trade
        from another trade for matching purposes.
        '''
        try:
            con = db_connect()
            cur = con.cursor()
            filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration from trades"
            cur.execute(filtered_trades_sql)
            filtered_trades = cur.fetchall()

            if filtered_trades == []:
                filtered_trades = 'error'
                raise DatabaseEmpty

        except sqlite3.Error as error:
            logger.fatal(error, stack_info=True)

        except DatabaseEmpty as error:
            logger.warning(error, stack_info=True)

        finally:
            if (con):
                con.close()
            return filtered_trades

    def strike_price_fixer(self, processed_list, new_trade) -> tuple:
        '''
        This runs when the first round of processing detects
        an error in the strike price value of the processed tuple.
        '''
        strike_price = 'error'
        in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade
        if 'out' in in_or_out:
            try:
                database_trades = self.fetch_matchable_trades()
                if database_trades == []:
                    raise DatabaseEmpty

                matched_trade = re.findall(
                    rf'\(((\'in\'), (\'{ticker}\'), (\'\d+\'), (\'\w+\'), (\'{user_name}\'), (\'{expiration}\'))',
                    str(database_trades))

                if len(matched_trade) == 1 and matched_trade != []:
                    strike_price = matched_trade[0][3].replace("'", "")
                    if 'error' in call_or_put:
                        call_or_put = matched_trade[0][4].replace("'", "")
                else:
                    raise StageTwoError

            except DatabaseEmpty as e:
                logger.warning(e, stack_info=True)

            except StageOneError as error:
                logger.error(f'{error}', stack_info=True)
                strike_price = 'error'

            finally:
                return strike_price, call_or_put

        elif 'in' in in_or_out:
            return strike_price, call_or_put

        else:
            return strike_price, call_or_put

    def call_or_put_fixer(self, processed_list, new_trade) -> str:
        '''
        This runs when the first round of processing detects
        errors in call_or_put values. processed_list contains
        the remaining values that didn't get trimmed from the 
        original split_result.
        '''
        is_call = False
        is_put = False
        result = 'error'
        try:
            for split in processed_list:
                if 'call' in split.lower():
                    is_call = 'call'
                if 'put' in split.lower():
                    is_put = 'put'

            if is_call and is_put:
                is_call = 'error'
                is_put = 'error'
                raise StageOneError

            elif is_call and not is_put:
                result = 'call'

            elif is_put and not is_call:
                result = 'put'

        except StageOneError as error:
            logger.warning(f'{error} | Processed list : {processed_list}')
            in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade
            if 'out' in in_or_out:
                try:
                    matched_trade = self.fetch_matchable_in_trades(new_trade)
                    if 'error' in matched_trade:
                        raise StageTwoError

                    if matched_trade == []:
                        raise DatabaseEmpty

                    if len(matched_trade
                           ) == 1 and 'error' not in matched_trade:
                        result = matched_trade[3]

                except StageTwoError as error:
                    logger.error(f'{error}', stack_info=True)

                except DatabaseEmpty as error:
                    logger.warning(f'{error}', stack_info=True)

        finally:
            return result
        # except (IndexError, ValueError) as error:
        #     print(f"{error} In call_or_put level 2 check!")
        #     logger.warning(f"{error} In call_or_put level 2 check!")
        #     result = 'error'

    def buy_price_fixer(self, processed_list, original_message) -> tuple:
        '''
        Runs when the first round of processing
        detects an error determing the buy price.
        Will return a integer / float if successful
        and 'error' if not.
        '''
        class buy_price_candidates:
            def __init__(self, possible_buy_price, original_list_value):
                self.possible_buy_price = possible_buy_price
                self.original_list_value = original_list_value

        try:
            possible_buy_prices = []
            duplicate_possibles = []
            for list_value in processed_list:
                possible_result = list_value.replace('$', '')
                possible_result = possible_result.replace(' ', '')

                if any(char.isalpha() for char in possible_result) is False:
                    if ',' in possible_result:
                        comma_split_values = possible_result.split(',')
                        for split_value in comma_split_values:
                            possible_buy_prices.append(
                                buy_price_candidates(split_value, list_value))
                    else:
                        possible_buy_prices.append(
                            buy_price_candidates(possible_result, list_value))

            if len(possible_buy_prices) == 1:
                buy_price = possible_buy_prices[0].possible_buy_price
                processed_list.remove(
                    possible_buy_prices[0].original_list_value)

            elif len(possible_buy_prices) > 1:
                list_of_possible_results = []
                for obj in possible_buy_prices:
                    list_of_possible_results.append(obj.possible_buy_price)

                for item in list_of_possible_results:
                    if list_of_possible_results.count(item) > 1:
                        duplicate_possibles.append(item)

                if len(duplicate_possibles) == 1 or len(
                        set(duplicate_possibles)) == 1:
                    for obj in possible_buy_prices:
                        if obj.possible_buy_price == duplicate_possibles[0]:
                            buy_price = obj.possible_buy_price
                            processed_list.remove(obj.original_list_value)
                            return

                elif duplicate_possibles == [] or len(duplicate_possibles) > 1:
                    raise StageOneError

            else:
                raise StageOneError

        except StageOneError as error:
            buy_price = 'error'
            logger.warning(
                f'{error} \n {processed_list} \n {original_message}')
            split_original_message = original_message.split('-')
            duplicates = [
                value for value in processed_list
                if value in split_original_message
            ]
            if duplicates == []:
                raise StageTwoError
            elif len(duplicates) == 1 and any(item.isdigit()
                                              for item in duplicates) is True:
                buy_price = duplicates[0]
                buy_price = buy_price.replace(' ', '')
            elif len(duplicates) > 1:
                duplicate_ints = []
                for item in duplicates:
                    try:
                        if ',' in item:
                            split_items = item.split(',')
                            duplicates.remove(item)
                            for split_item in split_items:
                                try:
                                    converted_split_item = float(split_item)
                                    duplicate_ints.append(converted_split_item)
                                except ValueError:
                                    pass
                                duplicates.append(split_item)
                        # Covers a rare edge case example. 'BOT\nBBS-TRADE-BOT\nMariaC82\nOUT - BABA - 8.28 - 250C - 16.50 - SWING - OUT OF 1/2: $16.5 FROM: 12.5'
                        if '$' in item:
                            split_item_money = item.split(' ')
                            for split_money in split_item_money:
                                if '$' in split_money:
                                    money_item = split_money.replace('$', '')
                                    duplicate_ints.append(float(money_item))
                        converted_item = float(item)
                        duplicate_ints.append(converted_item)
                    except ValueError:
                        pass
                if len(duplicate_ints) == 1:
                    buy_price = duplicate_ints[0]
                # testing to see if this stage catches many duplicates and quality of catches
                elif len(duplicate_ints) > 1:
                    possible_buy_prices = []
                    for dup_int in duplicate_ints:
                        if duplicate_ints.count(dup_int) > 1:
                            possible_buy_prices.append(dup_int)
                            if len(possible_buy_prices) == 1:
                                buy_price = possible_buy_prices[0]
                            elif len(possible_buy_prices
                                     ) == 2 and possible_buy_prices.count(
                                         possible_buy_prices[0]) == 2:
                                buy_price = possible_buy_prices[0]
                            else:
                                raise StageTwoError
                        else:
                            raise StageTwoError

                else:
                    logger.warning(
                        f'DEBUG INFO QUALITY CHECK -\nAmount of duplicate potential buy prices : {duplicate_ints} \nOriginal message : {original_message} \nProcessed message : {processed_list}'
                    )
                    raise StageTwoError

        except StageTwoError as second_error:
            buy_price = 'error'
            logger.warning(
                f'{second_error} | Processed message : {processed_list} Original message : {original_message}'
            )
            second_try_list = str(processed_list)
            second_try_list = second_try_list.replace(' ', '')
            second_try_list = second_try_list.replace(",", '')
            second_try_list = second_try_list.replace('[', '')
            second_try_list = second_try_list.replace(']', '')
            second_try_list = second_try_list.split(',')
            for element in second_try_list:
                if second_try_list.count(element) > 1:
                    buy_price = element
                    break
                else:
                    raise StageThreeError

        except StageThreeError as e:
            logger.error(
                f'{e} | Remaining message : {processed_list}\n Original Message : {original_message}'
            )
            buy_price = 'error'

        finally:
            return str(buy_price), processed_list

    def expiration_fixer(self, processed_list, new_trade):
        '''
        Runs after the first round of processing
        detects an error determing the trade expiration.
        Looks for a IN trade that matches this trade,
        and will grab the expiration. Else, run processed
        list again to see if the value is remaining in the
        pruned message.
        '''
        new_expiration = 'error'
        try:
            database_trades = self.fetch_database()
            if database_trades == []:
                raise DatabaseEmpty

            in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color, date, time = new_trade
            ticker = ticker.lower()
            matched_trades = re.findall(
                rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'\d+/\d+\'), (\'\w+\'))\)',
                str(database_trades))

            if len(matched_trades) == 1:
                matched_str = matched_trades[0][0]
                matched_list = matched_str.split(',')
                new_expiration = matched_list[5]
                new_expiration = new_expiration.replace("'", "")
                new_expiration = new_expiration.replace(' ', '')

            elif len(matched_trades) > 1:
                raise MultipleMatchingIn

        except DatabaseEmpty as info_error:
            logger.info(info_error)
            new_expiration = 'error'

        except MultipleMatchingIn as error:
            logger.error(
                f'{error} | Processed message : {processed_list} New trade : {new_trade}'
            )
            new_expiration = 'error'

        except ExpirationFixerFailed as error:
            logger.fatal(f'{error}', exc_info=True)

        finally:
            return new_expiration

    #def get_options_data(self, ticker, contract_symbol):
    #    url = f"https://stock-and-options-trading-data-provider.p.rapidapi.com/options/{ticker.lower()}?length=100"
    #    headers = {
    #        'x-rapidapi-host': f"{RAPID_API_HOST}",
    #        'x-rapidapi-key': f"{RAPID_API_KEY}",
    #        'x-rapidapi-proxy-secret': f"{RAPID_API_PROXY_SECRET}"
    #    }
    #    for attempt in range(5):
    #        try:
    #            response = requests.request("GET", url, headers=headers)
    #            if response.status_code != 200:
    #                raise RuntimeError
    #        except RuntimeError as error:
    #            logger.error(
    #                f"RAPID API GET REQUEST ERROR: STATUS CODE: {response.status_code}"
    #            )
    #            pass
    #    data = json.loads(response.content)
    #    df = pd.json_normalize(data, 'options')
    #    return response.text

    def live_buy_price(self, ticker, strike, expiration, call_or_put):
        '''
        Retreives the live market price for the given trade.
        Parameters:
        ticker, strike, expiration, call_or_put
        '''
        try:
            if 'error' in (ticker, strike, expiration, call_or_put):
                raise LiveBuyPriceError

            converted_expiration = convert_date(expiration)
            split = converted_expiration.split('/')
            converted_expiration = rf"{split[2]}-{split[0]}-{split[1]}"
            ticker_data = yf.Ticker(f"{ticker.upper()}")
            if converted_expiration == 'error':
                raise LiveBuyPriceError
            options = ticker_data.option_chain(converted_expiration)

            if call_or_put == 'call':
                df = options.calls

            if call_or_put == 'put':
                df = options.puts

            if '.' in strike:
                table = df.loc[df['strike'] == float(strike)]
            if '.' not in strike:
                table = df.loc[df['strike'] == int(strike)]

            last_sell_price = list(table['lastPrice'])[0]

        except LiveBuyPriceError as error:
            logger.error(f"{error}", exc_info=True)
            last_sell_price = 'error'

        except (IndexError, KeyError) as error:
            logger.error(f"{error}", exc_info=True)
            last_sell_price = 'error'

        except ValueError as error:
            date_now = standard_datetime()
            logger.error(
                f"{error}:\nLIVE BUY PRICE ERROR:\n Current Date: {date_now} Trade Expiration: {expiration}"
            )
            last_sell_price = 'error'

        finally:
            return str(last_sell_price)

    def live_expiration(self, ticker, strike, expiration, call_or_put):
        '''
        Verifies the expiration date is valid by submitting it to
        the yfinance api as a parameter. Invalid dates throw a ValueError.
        '''
        try:
            converted_expiration = convert_date(expiration)
            split = converted_expiration.split('/')
            converted_expiration = rf"{split[2]}-{split[0]}-{split[1]}"
            ticker_data = yf.Ticker(f"{ticker.upper()}")
            if converted_expiration == 'error':
                raise LiveExpirationError
            ticker_data.option_chain(converted_expiration)

        except LiveExpirationError as error:
            logger.error(f'{error} {expiration}', exc_info=True)
            expiration = 'error'

        except ValueError:
            logger.error("Expiration date is not valid!", exc_info=True)
            expiration = 'error'

        finally:
            return str(expiration)

    def fetch_closest_expiration(self, ticker):
        '''
        Fetches the next expiration date for a tickers options contracts
        '''
        try:
            ticker_data = yf.Ticker(f"{ticker.upper()}")
            expiration = ticker_data.options[0].split('-')
            expiration = rf"{expiration[1]}/{expiration[2]}"
        except:
            pass
        finally:
            return expiration