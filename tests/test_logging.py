import logging
from logging.config import dictConfig
from config.logging_config import LOGGING_CONFIG
from src.logging.logger import Logger


logger_manager = Logger('test_logging.py')
logger = logger_manager.get_logger()
logger.info("This is a test log message.")