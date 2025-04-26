import os
import logging
import logging.handlers
from .settings import LOG_LEVEL, LOG_FILE, LOG_FORMAT, LOG_BACKUP_COUNT, LOG_MAX_BYTES

def setup_logging():
    """
    Setup logging configuration for the application.
    Configures logging to write to both stdout and a rotating file.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler with rotation
    if LOG_FILE:
        # Create directory for log file if it doesn't exist
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Log startup message
    logger.info("Logging system initialized")
    
    return logger