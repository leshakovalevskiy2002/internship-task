from pathlib import Path

from loguru import logger


def setup_logging() -> None:
    logger.remove()

    Path("logs").mkdir(exist_ok=True)

    logger.add(
        "logs/info.log",
        format="Log: [{extra[log_id]}:{time} - {level} - {message}]",
        level="INFO",
        enqueue=True,
        rotation="10 MB",
        retention="7 days",
    )
    logger.add(
        "logs/errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
