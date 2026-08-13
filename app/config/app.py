from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from loguru import logger

from app.api import router
from app.config.exceptions import setup_exception_handlers
from app.config.logging import setup_logging
from app.config.middlewares import setup_middlewares

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_id = str(uuid4())

    with logger.contextualize(log_id=log_id):
        logger.info("The application is starting.")

        try:
            yield
        except Exception:
            logger.exception("Application startup failed")
            raise
        finally:
            logger.info("The application is shutting down")


app = FastAPI(title="This application works with users and their transactions", version="0.1.0", lifespan=lifespan)

setup_middlewares(app)
setup_exception_handlers(app)

app.include_router(router)


@app.get("/")
async def home():
    return {"message": "Transactions Service"}
