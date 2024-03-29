from selenium.common.exceptions import NoSuchElementException, TimeoutException


class DuplicateTrade(Exception):
    """This trade has already been recorded"""


class TradeAlreadyOut(Exception):
    """This trade has already exited!"""


class IsAInTrade(Exception):
    """An IN trade already exists with this information!"""


class IsOldMessage(Exception):
    """This is an old message"""


class DatabaseEmpty(Exception):
    """The database is empty."""


class MultipleMatchingIn(Exception):
    """There are multiple matching IN trades. This should never happen!"""


class OutTradeHasNoMatch(Exception):
    """Out trade has no match! ignoring trade!"""


class TickerError(Exception):
    """Could not determine ticker of trade!"""


class LiveStrikePriceError(Exception):
    """Strike price scraped from trade differs +/- 5% of live bid price!"""


class IgnoreTrade(Exception):
    """Ignoring this trade, not commiting to database"""


class StageOneError(Exception):
    """Stage 1 in second level check failed!"""


class StageTwoError(Exception):
    """Stage 2 in second level check failed!!"""


class StageThreeError(Exception):
    """Stage 3 in second level check failed!!!"""


class MakeImageError(Exception):
    """Error creating image!"""


class DateConversionError(Exception):
    """Date could not be converted!"""


class LiveBuyPriceError(Exception):
    """Error in live buy price function!"""


class ReleaseTradeError(Exception):
    """Error in release trade function!"""


class MarketClosed(Exception):
    """Market is closed"""


class ExpirationFixerFailed(Exception):
    """
    All attempts to find an expiration in the trade has failed.
    Typically caused by trader writing the expiration with a . ex. (9.25)
    """


class MatchingInNeverPosted(Exception):
    """
    The matching IN trade never got posted to instagram.
    This out trade will not post to instagram.
    """


class LiveExpirationError(Exception):
    """
    Expiration value is not valid!
    """