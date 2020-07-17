import re


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
