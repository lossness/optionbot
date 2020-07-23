import re
from main_logger import logger
from db_utils import db_connect


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

    def strike_price_fixer(self) -> str:
        '''
        This runs when the first round of processing detects
        an error in the strike price value of the processed tuple.
        '''
        strike_price = 'error'
        call_or_put = 'error'
        in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration = self.new_trade_tuple
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
                    rf'\(((\'in\'), (\'{ticker}\'), (\'{strike_price}\'), (\'{call_or_put}\'), (\'{user_name}\'), (\'{expiration}\')',
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

    def buy_price_fixer(self, processed_list) -> str:
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
                possible_result = possible_result.replace(',', '.')
                if len(possible_result) > 2 and any(
                        char.isalpha() for char in split) is False:
                    filtered_dict[possible_result] = split
            possible_results = list(filtered_dict.keys())
            buy_price = re.findall(r'\s?([-+]?\d*)(\.)(\d+|\d+)\s?',
                                   str(possible_results))

            if buy_price == [] or len(buy_price) > 1:
                raise KeyError("Could not determine buy price! LEVEL 2")

            if buy_price:
                buy_price = ''.join(buy_price[0])
                processed_list.remove(filtered_dict[buy_price])

        except KeyError as e:
            logger.error(f'{e} : {processed_list}')
            buy_price = 'error'

        finally:
            return buy_price, processed_list