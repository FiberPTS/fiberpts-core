# Logging configurations
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        # 'default': {
        #     'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
        #     'formatter': 'standard',
        #     'filename': '.app/logs/fpts.log',
        #     'maxBytes': 1024 * 1024 * 5,  # 5 MB
        #     'backupCount': 5,
        #     'encoding': 'utf8',
        # },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'FH',
            'filename': '.app/logs/fpts.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}
