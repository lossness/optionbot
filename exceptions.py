class DuplicateTrade(Exception):
    '''This trade has already been recorded'''


class TradeAlreadyOut(Exception):
    '''This trade has already exited!'''


class IsAInTrade(Exception):
    '''This is an IN trade'''


class IsOldMessage(Exception):
    '''This is an old message'''


class DatabaseEmpty(Exception):
    '''The database is empty.'''


class MultipleMatchingIn(Exception):
    '''There are multiple matching IN trades. This should never happen!'''


class OutTradeHasNoMatch(Exception):
    '''Out trade has no match! ignoring trade!'''


class TickerError(Exception):
    '''Could not determine ticker of trade!'''


class LiveStrikePriceError(Exception):
    '''Strike price scraped from trade differs +/- 5% of live bid price!'''