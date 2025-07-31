import logging
from typing import Dict

class Logger:
    """Singletons"""
    """
    Multiple Logger Singletons based on application
        - 1 for logging the daily script that retrieves newsletter data
        - 1 for logging interactions at runtime with the chatbot
    """
    _instances: Dict[str, 'Logger'] = {}
    _loggers: Dict[str, logging.Logger]  = {}

    def __init__(self, name: str, log: str):
        self.name = name
        self.log = log
        self.key = f"{name}_{log}"

        if self.key not in Logger._loggers:
            Logger._loggers[self.key] = logging.getLogger(self.key)
            logger = Logger._loggers[self.key]

            if not logger.handlers:
                mode = 'w' if self.log == "runtime" else 'a'
                filename = f"{self.key}.log"
            
                file_handler = logging.FileHandler(filename=filename, mode=mode)
                file_handler.setLevel(logging.INFO)

                formatter = logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.setLevel(logging.INFO)

    def __new__(cls, name: str, log: str):
        key = f"{name}_{log}"
        
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
        return cls._instances[key]    

    def get_logger(self) -> logging.Logger:
        return Logger._loggers[self.key]

    @classmethod
    def get_daily_logger(cls, name: str) -> logging.Logger:
        ins = cls(name=name, log="daily")
        return ins.get_logger()
    
    @classmethod
    def get_runtime_logger(cls, name: str) -> logging.Logger:
        ins = cls(name=name, log="runtime")
        return ins.get_logger()

# initialize Singletons for later use
daily_logger = Logger.get_daily_logger(name="data_fetch")
runtime_logger = Logger.get_runtime_logger(name="chatbot")