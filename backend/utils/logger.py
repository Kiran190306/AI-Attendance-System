import logging

from ..config import LOG_FORMAT, LOG_LEVEL


def setup_logging() -> None:
    """Configure root logger with project defaults."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
