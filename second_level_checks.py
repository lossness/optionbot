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
        self.processed_list = processed_list
        self.new_trade_tuple = new_trade_tuple

    def strike_price(self) -> str:
        '''
        This runs when the first round of processing detects
        an error in the strike price value of the processed tuple.
        '''
        strike_price = 'error'
        call_or_put 'error'
        in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, trade_author, expiration = new_trade_tuple
        if 'out' in in_or_out:
            try:
                con = db_connect()
                cur = con.cursor()
                filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, user_name, expiration from trades"
                cur.execute(filtered_trades_sql)
                filtered_trades = cur.fetchall()
                if filtered_trades == []:
                    raise ValueError("The database is empty! Cannot perform level 2 IN match")

            except ValueError as e:
                logger.warning(e, stack_info=True)



        except (IndexError, ValueError) as error:
            print(f"{error} in strike_price level 2 check!")
            logger.warning(f"{error} In strike_price level 2 check!")
            return 'error'

    def call_or_put(self) -> str:
        '''
        This runs when the first round of processing detects
        errors in call_or_put values. processed_list contains
        the remaining values that didn't get trimmed from the 
        original split_result.
        '''
        is_call = False
        is_put = False
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
                return is_call

            elif is_put and not is_call:
                return is_put

        except (IndexError, ValueError) as error:
            print(f"{error} In call_or_put level 2 check!")
            logger.warning(f"{error} In call_or_put level 2 check!")
            return 'error'
