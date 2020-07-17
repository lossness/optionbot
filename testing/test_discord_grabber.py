def prep_message_for_algos(message: str) -> list:
    '''
    Removes various unneeded text in the message string
    for easier processing.
    '''
    try:
        message = re.sub(r'BOT', '', message)
        message = re.sub(r'BBS-TRADE-', '', message)
        message = re.sub(r'\n', '@', message)
        message = message.split('-')
    except:
        pass
    finally:
        return message


def get_trader(split_message: list) -> str:
    '''
    Finds the trade author of the message
    and then removes it from the message
    '''
    match = False
    for trader in TRADERS:
        for split in split_message:
            if trader in split:
                match = (trader, split)
                return match


def error_producer_beta(driver):
    # loop over single discord posts in all matched posts in main channel
    try:
        counter = 1
        message_list = find_new_messages(driver)
        for message in tqdm(message_list):
            try:
                split_result = prep_message_for_algos(message)
                trade_author, corresponding_slice = get_trader(split_result)
                split_result = str(split_result).replace(
                    str(corresponding_slice), '')
                split_result = split_result.split('-')
                trade_author_tup = tuple(trade_author)
                # find the longest string left which is the message string
                longest_string = max(split_result, key=len)
                double_split_result = longest_string.split('-')
                double_split_result = list(filter(None, double_split_result))
                # gets a call or put status, and pops that matched entry out of the list
                call_or_put_tup, strike_price_tup, double_split_result = get_call_or_put_and_strike_price(
                    double_split_result, split_result)
                trade_expiration_tup, double_split_result = get_trade_expiration(
                    double_split_result, longest_string)
                in_or_out_tup, double_split_result = get_in_or_out(
                    double_split_result)
                buy_price_tup, double_split_result = get_buy_price(
                    double_split_result)
                stock_ticker_tup, double_split_result = get_stock_ticker(
                    double_split_result)
                datetime_tup = str(datetime.now())
                stock_ticker_tup = stock_ticker_tup.lower()

                trade_tuple = (
                    in_or_out_tup,
                    stock_ticker_tup,
                    datetime_tup,
                    strike_price_tup,
                    call_or_put_tup,
                    buy_price_tup,
                    trade_author_tup,
                    trade_expiration_tup,
                )

                if 'error' or 'ERROR' in trade_tuple:
                    update_error_table(trade_tuple)
                    print(counter)
                    counter += 1

            except (KeyError, IndexError, ValueError) as error:
                print(f"{error}")
    except (TimeoutException, NoSuchElementException) as error:
        logger.warning(
            f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
        pass


# message_test = 'BOT\nBBS-TRADE-BOT\nJen ❤crypto\nBuy - Amd - 6\n26 - 52p - 64 - Scalp - Have a stop'

# split_message_test = prep_message_for_algos(message_test)


# get_trader(split_message_test)
def error_producer_classic(driver):
    # loop over single discord posts in all matched posts in main channel
    try:
        counter = 1
        message_list = find_new_messages(driver)
        for new_message in tqdm(message_list):
            try:
                split_result = new_message.splitlines()
                # removes any empty strings from list
                split_result = list(filter(None, split_result))
                split_result = list(filter(filter_message, split_result))
                trade_author = list(filter(filter_trader, split_result))
                trade_author_tup = trade_author[0]
                # find the longest string left which is the message string
                longest_string = max(split_result, key=len)
                double_split_result = longest_string.split('-')
                double_split_result = list(filter(None, double_split_result))
                # gets a call or put status, and pops that matched entry out of the list
                call_or_put_tup, strike_price_tup, double_split_result = get_call_or_put_and_strike_price(
                    double_split_result)

                trade_expiration_tup, double_split_result = get_trade_expiration(
                    double_split_result)

                buy_price_tup, double_split_result = get_buy_price(double_split_result)

                in_or_out_tup, double_split_result = get_in_or_out(double_split_result)

                stock_ticker_tup, double_split_result = get_stock_ticker(
                    double_split_result)
                datetime_tup = str(datetime.now())
                stock_ticker_tup = stock_ticker_tup.lower()

                trade_tuple = (
                    in_or_out_tup,
                    stock_ticker_tup,
                    datetime_tup,
                    strike_price_tup,
                    call_or_put_tup,
                    buy_price_tup,
                    trade_author_tup,
                    trade_expiration_tup,
                )
                if 'error' or 'ERROR' in trade_tuple:
                    update_error_table(trade_tuple)
                    print(counter)
                    counter += 1

                    except (KeyError, IndexError, ValueError) as error:
                        print(f"{error}")
            except (TimeoutException, NoSuchElementException) as error:
                logger.warning(
                    f"{error}: PRODUCER COULD NOT FIND NEWEST DISCORD MESSAGE!!")
                pass