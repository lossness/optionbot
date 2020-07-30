import re
from main_logger import logger
from db_utils import db_connect
import sqlite3
from exceptions import DatabaseEmpty, MultipleMatchingIn, StageOneError, StageTwoError, StageThreeError


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
    def __intit__(self, processed_list, new_trade_tuple):
        '''
        Parameters
        ----------
        processed_list : list
        The end result of the inital trade message
        after having all successful algorithms
        remove required data
        '''
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

    def strike_price_fixer(self, processed_list, new_trade) -> str:
        '''
        This runs when the first round of processing detects
        an error in the strike price value of the processed tuple.
        '''
        strike_price = 'error'
        call_or_put = 'error'
        in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade
        if 'out' in in_or_out:
            try:
                con = db_connect()
                cur = con.cursor()
                filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration from trades"
                cur.execute(filtered_trades_sql)
                filtered_trades = cur.fetchall()

                if filtered_trades == []:
                    raise ValueError(
                        "The database is empty! Cannot perform level 2 IN match"
                    )

                matched_in_trade = re.findall(
                    rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'{expiration}\'))',
                    str(filtered_trades))

                if matched_in_trade != [] and len(matched_in_trade) < 2:
                    strike_price = matched_in_trade[2]
                    call_or_put = matched_in_trade[3]

            except ValueError as e:
                logger.warning(e, stack_info=True)

            finally:
                return strike_price, call_or_put

    def call_or_put_fixer(self) -> str:
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
            for split in self.processed_list:
                if 'call' in split.lower():
                    is_call = 'call'
                if 'put' in split.lower():
                    is_put = 'put'

            if is_call and is_put:
                is_call = 'error'
                is_put = 'error'
                raise ValueError(
                    "Call_or_put level 2 function returned TRUE for both!")

            elif is_call and not is_put:
                result = 'call'

            elif is_put and not is_call:
                result = 'put'

        except (IndexError, ValueError) as error:
            print(f"{error} In call_or_put level 2 check!")
            logger.warning(f"{error} In call_or_put level 2 check!")
            result = 'error'

        finally:
            return result

    def in_or_out_fixer(self) -> str:
        '''
        Runs when the first round of processing
        detects an error determing the in or out
        status of a trade
        '''
        is_in = 'error'

    def buy_price_fixer(self, processed_list, original_message,
                        strike_price) -> str:
        '''
        Runs when the first round of processing
        detects an error determing the buy price.
        Will return a integer / float if successful
        and 'error' if not.
        '''
        try:
            filtered_dict = {}
            for split in processed_list:
                possible_result = split.replace('$', '')
                possible_result = possible_result.replace(' ', '')
                if len(possible_result) > 2 and any(
                        char.isalpha() for char in split) is False:
                    filtered_dict[possible_result] = split
            possible_results = list(filtered_dict.keys())
            buy_price = re.findall(r'\s?([-+]?\d*)(\.)(\d+|\d+)\s?',
                                   str(possible_results))

            if len(buy_price) == 1:
                buy_price = ''.join(buy_price[0])
                processed_list.remove(filtered_dict[buy_price])

            if buy_price == [] or len(buy_price) > 1:
                raise StageOneError

        except StageOneError as error:
            buy_price = 'error'
            logger.warning(
                f'{error} \n {processed_list} \n {original_message}')
            # buy_price_list = list(buy_price)
            # fixed_list = []
            # for item in buy_price_list:
            #     item = list(item)
            #     fixed_list.append(item)
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
                        converted_item = float(item)
                        duplicate_ints.append(converted_item)
                    except ValueError:
                        pass
                if len(duplicate_ints) == 1:
                    buy_price = duplicate_ints[0]
                # testing to see if this stage catches many duplicates and quality of catches
                elif duplicate_ints.count(duplicate_ints[0]) > 1:
                    logger.error(
                        f'DEBUG INFO QUALITY CHECK | Number of Duplicate ints : {duplicate_ints} Original message : {original_message} Processed message : {processed_list}'
                    )
                    raise StageTwoError
                else:
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
                f'{e} | Processed message : {processed_list} Original Message : {original_message}'
            )
            buy_price = 'error'

        finally:
            return buy_price, processed_list

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

            in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration, color = new_trade
            ticker = ticker.lower()
            matched_trades = re.findall(
                rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'\d+/\d+\'), (\'\w+\'))\)',
                str(database_trades))

            if len(matched_trades) == 1:
                matched_str = matched_trades[0][0]
                matched_list = matched_str.split(',')
                new_expiration = matched_list[5]
                new_expiration = expiration.replace("'", "")
                new_expiration = expiration.replace(' ', '')

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

        finally:
            return new_expiration