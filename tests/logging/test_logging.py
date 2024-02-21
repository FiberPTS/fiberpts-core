import logging
import logging.handlers


def setup_logger(logger_name):
    logger = logging.getLogger(logger_name)
    time_format = "%Y-%m-%d %H:%M:%S"
    file_handler = logging.handlers.WatchedFileHandler('tests/logging/test.log') #Using WatchedFileHandler to synchronize with logrotate
    logFormat = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s", datefmt=time_format) #Formatting can be changed to preference
    file_handler.setFormatter(logFormat)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG) #Lowest Level which allows for all levels of messages to be output




if __name__ == "__main__":
    setup_logger(__name__)
    screen_logger = logging.getLogger(__name__)
    screen_logger.critical("Testing Critical")
    screen_logger.error("Testing Error")
    screen_logger.warning("Testing Warning")
    screen_logger.info("Testing Info")
    screen_logger.debug("Testing Debug")