import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.handlers:
        root_logger.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
