import logging
from logging.handlers import TimedRotatingFileHandler
import os
import colorlog
import src.config as config

def setup_logging():
    """Configure logging with color support and proper formatting."""
    # Create a color formatter
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # Get the root logger
    root_logger = logging.getLogger()

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create a stream handler
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(handler)

    # Set the log level based on DEBUG setting
    root_logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('gradio').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('python_multipart').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file = os.path.join(log_directory, "app.log")
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"  # Dateiname mit Datum
    root_logger.addHandler(file_handler)

    return root_logger
