import logging
import sys

def get_logger(name: str = "RootIQ") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Force UTF-8 on Windows to prevent cp1252 UnicodeEncodeError
        stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1) if hasattr(sys.stdout, 'fileno') else sys.stdout
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", "%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
