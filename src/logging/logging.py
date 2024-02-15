import logging
from logging.config import dictConfig
from config.logging_config import LOGGING_CONFIG
from concurrent_log_handler import ConcurrentRotatingFileHandler

class Logger:
    # TODO: Get path to project folder for log_file_path and config_path
    # TODO: Check if logger_name can be used as a way to reference the name of the script doing the logging
    # TODO: Add docstrings
    def __init__(self,
                 logger_name,
                 level=logging.INFO,
                 log_file_path='.app/logs/fpts.log'):
        self.log_file_path = log_file_path
        self.logger_name = logger_name
        self.logger = None
        self._configure_logging()

    def _configure_logging(self):
        """Configure logging using the specified configuration file and set up ConcurrentRotatingFileHandler."""
        # Load basic configuration from file
        dictConfig(LOGGING_CONFIG, disable_existing_loggers=False)

        # Get the logger and add the ConcurrentRotatingFileHandler to it
        self.logger = logging.getLogger(self.logger_name)

    def get_logger(self):
        """Return the configured logger."""
        return self.logger


"""
Example Usage:

if __name__ == "__main__":
    logger_manager = Logger('script_name.py')
    logger = logger_manager.get_logger()
    logger.info("This is a test log message.")
"""
