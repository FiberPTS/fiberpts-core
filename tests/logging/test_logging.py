import logging
import logging.config
import os

project_dir = os.path.abspath(os.path.join(__file__, '../../..'))

if __name__ == "__main__":
    logging.config.fileConfig(f'{project_dir}/config/logging.conf')
    logger = logging.getLogger(f'{os.path.basename(__file__)}')
    logger.critical("Testing Critical")
    logger.error("Testing Error")
    logger.warning("Testing Warning")
    logger.info("Testing Info")
    logger.debug("Testing Debug")
