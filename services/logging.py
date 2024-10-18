import logging
from logging.handlers import RotatingFileHandler

class Logger:
    _instance = None

    def __new__(self, log_file='app.log'):
        if self._instance is None:
            self._instance = super(Logger, self).__new__(self)
            self._instance._initialize_logger(log_file)
        return self._instance

    def _initialize_logger(self, log_file):
        # Logger Config
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # rotation config
        max_bytes = 5 * 1024 * 1024 # 5mb
        # file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=0) # no backup, if 2 will generate log.0, log.1
        file_handler.setLevel(logging.INFO)

        # format
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)

        # logger handler
        self.logger.addHandler(file_handler)

    def info(self, message: str) -> None:
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        self.logger.error(message)
    
    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def critial(self, message: str) -> None:
        self.logger.critical(message)
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)