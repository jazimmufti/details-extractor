"""Application logging configuration."""

import logging
import sys
from app.core.config import settings


def setup_logger(name: str = "yt_intelligence") -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
        
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.propagate = False
        
    return logger


logger = setup_logger()
