import logging
from datetime import datetime
import os

def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO) -> logging.Logger:
    """Set up a logger that logs to both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not os.path.exists("logs"):
        os.makedirs("logs")
    log_file = os.path.join("logs", f"log_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    if not logger.handlers:  # avoid adding handlers multiple times
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
