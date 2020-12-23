# main_logger.py

import logging
from time_utils import east_coast_datetime

# Gets or creates a logger
logger = logging.getLogger(__name__)

# set log level
logger.setLevel(logging.DEBUG)

datetime = east_coast_datetime()
# define file handler and set formatter
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s',
                              datefmt="%m/%d/%Y %I:%M:%S %p %Z")
file_handler.setFormatter(formatter)

# add file handler to logger
logger.addHandler(file_handler)