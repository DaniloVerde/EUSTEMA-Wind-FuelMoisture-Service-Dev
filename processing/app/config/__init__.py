import logging
from .logging_config import setup_logging

# Initialize a shared logger instance
setup_logging()

def get_logger(name=None):
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger (usually __name__ from the calling module)
        
    Returns:
        A logger instance
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()