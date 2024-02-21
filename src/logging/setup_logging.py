import logging
import logging.handlers


def setup_logger():
    logger = logging.getLogger('FPTS')
    file_handler = logging.handlers.WatchedFileHandler('.app/logs/fpts.log')
    logFormat = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(logFormat)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    

if __name__ == "__main__":
    setup_logger()
