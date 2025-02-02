import logging
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, logfile, max_log_size=10 * 1024 * 1024, backup_count=10):
        """
        Logger with rotation

        :param logfile: Log file path
        :param max_log_size: Maximum size of log file before rotating (in bytes)
        :param backup_count: Number of backup logs to keep
        """
        self.logger = logging.getLogger("sync_logger")
        self.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        rotating_handler = RotatingFileHandler(logfile, maxBytes=max_log_size, backupCount=backup_count)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')

        console_handler.setFormatter(formatter)
        rotating_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(rotating_handler)

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)
