from pathlib import Path

from loguru import logger


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def setup_logging() -> None:
    logger.remove()

    LOG_DIR.mkdir(exist_ok=True)

    logger.add(
        LOG_DIR / "info.log",
        format="Log: [{extra[log_id]}:{time} - {level} - {message}]",
        level="INFO",
        enqueue=True,
        rotation="10 MB",
        retention="7 days",
    )
    logger.add(
        LOG_DIR / "errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
