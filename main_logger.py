# main_logger.py

import logging

# Gets or creates a logger
logger = logging.getLogger(__name__)

# set log level
logger.setLevel(logging.ERROR)

# define file handler and set formatter
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)

# add file handler to logger
logger.addHandler(file_handler)

# Logs
