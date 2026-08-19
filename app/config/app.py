from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from loguru import logger

from app.api import router
from app.config.database import create_db_and_tables, engine
from app.config.exceptions import setup_exception_handlers
from app.config.logging import setup_logging
from app.config.middlewares import setup_middlewares
from app.config.redis import create_redis

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_id = str(uuid4())

    with logger.contextualize(log_id=log_id):
        logger.info("Starting application")

        try:
            logger.info("Initializing database")
            await create_db_and_tables()

            logger.info("Initializing Redis")
            app.state.redis = create_redis()

            await app.state.redis.ping()
            logger.info("Application started")
            yield
        except Exception:
            logger.exception("Application startup failed")
            raise
        finally:
            logger.info("The application is shutting down")
            await engine.dispose()

            if hasattr(app.state, "redis"):
                await app.state.redis.aclose()


app = FastAPI(title="This application works with users and their transactions", version="0.1.0", lifespan=lifespan)

setup_middlewares(app)
setup_exception_handlers(app)

app.include_router(router)
