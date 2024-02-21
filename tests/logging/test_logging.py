import logging
import logging.handlers


def setup_logger():
    logger = logging.getLogger('FPTS')
    file_handler = logging.handlers.WatchedFileHandler('tests/logging/test.log') #Using WatchedFileHandler to synchronize with logrotate
    logFormat = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s") #Formatting can be changed to preference
    file_handler.setFormatter(logFormat)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG) #Lowest Level which allows for all levels of messages to be output



if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger('FPTS')
    logger.critical("Testing Critical")
    logger.error("Testing Error")
    logger.warning("Testing Warning")
    logger.info("Testing Info")
    logger.debug("Testing Debug")