from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from loguru import logger

from app.config.database import create_db_and_tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        logger.info("The application is starting. Create database tables if not exist")
        try:
            await create_db_and_tables()
            yield
        except Exception:
            logger.exception("Application startup failed")
            raise
        finally:
            logger.info("The application is shutting down")
