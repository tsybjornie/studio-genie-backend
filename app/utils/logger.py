import logging
import sys
from app.core.config import settings

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = __name__) -> logging.Logger:
    """Set up and configure logger"""
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level based on environment
    if settings.ENVIRONMENT == "production":
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


# Default logger instance
logger = setup_logger("studio_genie")
