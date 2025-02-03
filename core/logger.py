import logging
import colorlog
from rich.console import Console

console = Console()

# Define a custom class that overrides info()
class CustomLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        # Detect if it's JSON
        if isinstance(msg, (dict, list)):
            console.print_json(data=msg)  # Print JSON with colors
        else:
            # If it's not JSON, call the original method
            super().info(msg, *args, **kwargs)

def configure_logger():
    logging.setLoggerClass(CustomLogger)
    logger = logging.getLogger()
    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        fmt='%(asctime)s [%(log_color)s%(levelname)s%(reset)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger