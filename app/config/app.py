from app.config.broker import configure_broker

configure_broker()

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text

from app.api import router
from app.config.database import create_engine, create_session_maker
from app.config.exceptions import setup_exception_handlers
from app.config.logging import setup_logging
from app.config.middlewares import setup_middlewares
from app.config.redis import create_redis

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_engine()
    app.state.session_maker = create_session_maker(app.state.engine)

    log_id = str(uuid4())

    with logger.contextualize(log_id=log_id):
        logger.info("The application is starting.")

        try:
            logger.info("Initializing database")
            async with app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database initialized")

            logger.info("Initializing Redis")
            app.state.redis = create_redis()
            await app.state.redis.ping()
            logger.info("Redis initialized")

            logger.info("Application started")
            yield
        except Exception:
            logger.exception("Application startup failed")
            raise
        finally:
            logger.info("The application is shutting down")
            await app.state.engine.dispose()

            if hasattr(app.state, "redis"):
                await app.state.redis.aclose()


description_path = Path(__file__).parent.parent / "docs" / "description.md"
description = description_path.read_text(encoding="utf-8")

app = FastAPI(
    title="Financial User & Transaction Management Service", description=description, version="0.1.0", lifespan=lifespan
)

setup_middlewares(app)
setup_exception_handlers(app)

app.include_router(router)


@app.get(
    "/",
    description="Health-check endpoint. Returns a service name to confirm the application is running.",
    summary="Home endpoint",
)
async def home():
    return {"message": "Transactions Service"}
