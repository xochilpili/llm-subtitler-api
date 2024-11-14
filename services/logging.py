import logging

class Logger:
    _instance = None

    def __new__(self):
        if self._instance is None:
            self._instance = super(Logger, self).__new__(self)
            self._instance._initialize_logger()
        return self._instance

    def _initialize_logger(self):
        # Logger Config
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # format
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # rotation config
        #max_bytes = 5 * 1024 * 1024 # 5mb
        # file handler
        #file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=0) # no backup, if 2 will generate log.0, log.1
        #file_handler.setLevel(logging.INFO)
        #file_handler.setFormatter(formatter)
        # logger handler
        #self.logger.addHandler(file_handler)
        
        # console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

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