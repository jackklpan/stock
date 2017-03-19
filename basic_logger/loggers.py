import logging
from logging.handlers import RotatingFileHandler

def get_stream_logger(name="stream_logger", level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    return logger

def get_rotating_file_logger(name="rotating_file_logger", level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    path='rotating_file_log.txt', max_bytes=10485760, backup_count=5):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count)
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    return logger
