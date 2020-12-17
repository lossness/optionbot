import datetime
import pytz
import calendar


def get_date_and_time() -> tuple:
    '''
    Fetches the date and time in New York and returns
    a tuple = (date, time) in str format.
    '''
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    timeObj = ast_now.time()
    time_str = timeObj.strftime("%H:%M:%S")
    dateObj = ast_now.date()
    date_str = dateObj.strftime("%d-%m-%Y")
    date_and_time = (date_str, time_str)
    return date_and_time


def east_coast_datetime() -> str:
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    timeObj = ast_now.time()
    time_str = timeObj.strftime("%H:%M:%S")
    dateObj = ast_now.date()
    date_str = dateObj.strftime("%d-%m-%Y")
    date_and_time = f"{date_str}:{time_str}"
    return date_and_time


def get_date() -> str:
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    dateObj = ast_now.date()
    date_str = dateObj.strftime("%Y-%m-%d")
    return date_str


def get_time_and_day() -> tuple:
    '''
    Fetches a datetime object for the local time in New York and
    the calendar day of the week in string format.
    returns a tuple = (datetimeObj, day_of_the_week)
    '''
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    the_time = ast_now.time()
    day_of_the_week = calendar.day_name[ast_now.weekday()]
    return (the_time, day_of_the_week)


def standard_datetime() -> str:
    '''
    Fetches the standard datetime for the local time in New York.
    '''
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    datetime_now = ast_now.now()
    return str(datetime_now)


def newyork_datetime():
    '''
    Fetches the standard datetime for the local time in New York
    and returns the datetime object.
    '''
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    ast_now = utc_now.astimezone(pytz.timezone("America/New_York"))
    return ast_now.time()


def month_converter(month) -> str:
    ''' Converts month to month number.
    JAN -> 01
    '''
    months = [
        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT',
        'NOV', 'DEC'
    ]
    return str(months.index(month) + 1)


def minutes_difference(trade_datetime):
    '''
    Takes a datetime string and finds the difference
    in minutes between the time and the current time.
    '''
    current_time_obj = datetime.datetime.strptime(standard_datetime(),
                                                  '%Y-%m-%d %H:%M:%S.%f')
    trade_datetime_obj = datetime.datetime.strptime(trade_datetime,
                                                    '%Y-%m-%d %H:%M:%S.%f')
    datetime_obj_difference = current_time_obj - trade_datetime_obj
    minutes = datetime_obj_difference.total_seconds() / 60
    return minutes


def is_time_between(begin_time, end_time):
    check_time = newyork_datetime()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time <= end_time


def prune_members_window():
    if is_time_between(datetime.time(18, 30), datetime.time(18, 40)):
        return True
    else:
        return False
