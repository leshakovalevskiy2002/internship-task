from fastapi import FastAPI

from app.api import router
from app.config.exceptions import setup_exception_handlers
from app.config.lifespan import lifespan
from app.config.logging import setup_logging
from app.config.middlewares import setup_middlewares

app = FastAPI(title="This application works with users and their transactions", version="0.1.0", lifespan=lifespan)

setup_logging()

setup_middlewares(app)
setup_exception_handlers(app)

app.include_router(router)
