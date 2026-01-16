import logging
from logging.handlers import RotatingFileHandler

def get_logger():
    logger = logging.getLogger("app_logger")
    handler = RotatingFileHandler("app.log", maxBytes=1024*1024, backupCount=5)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
