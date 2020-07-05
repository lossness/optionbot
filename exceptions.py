class DuplicateTrade(Exception):
    '''This trade has already been recorded'''


class TradeAlreadyOut(Exception):
    '''This trade already has a match!'''


class IsAInTrade(Exception):
    '''This is an IN trade'''


class IsOldMessage(Exception):
    '''This is an old message'''