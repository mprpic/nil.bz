import os
import logging
from logging.handlers import RotatingFileHandler


def init_logging(level, log_file_name='nil.log'):

    # Determine passed logging level
    level = logging.getLevelName(level)

    # Initialize logger; level is set in the defined handlers
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: '
                                  '%(message)s [in %(filename)s:%(lineno)d]')

    # If we're in DEBUG mode, log everything to stdout. If not, log
    # all messages to the specified log file.
    if level == logging.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    else:
        log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../logs')

        if not os.path.isdir(log_dir):
            os.mkdir(log_dir, mode=0o700)

        # Rotate log files daily and keep log records for 10 days.
        file_handler = RotatingFileHandler(os.path.join(log_dir, log_file_name),
                                           maxBytes=1000, backupCount=2)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
