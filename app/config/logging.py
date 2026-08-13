import sys

from loguru import logger


def setup_logging() -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        format="Log: [{extra[log_id]}:{time} - {level} - {message}]",
        level="INFO",
        filter=lambda record: record["level"].no < 40,
        enqueue=True,
    )

    logger.add(
        sys.stderr,
        format="Log: [{extra[log_id]}:{time} - {level} - {message}]",
        level="ERROR",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
