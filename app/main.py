from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.handlers import (
    request_validation_exception_handler,
    transaction_service_exception_handler,
    user_service_exception_handler,
)
from app.api.v1.routers import transactions, users
from app.repositories.database import create_db_and_tables
from app.services import TransactionServiceError
from app.services import UserServiceError

logger.add("../logs/info.log", format="Log: [{extra[log_id]}:{time} - {level} - {message}]", level="INFO", enqueue=True)

logger.add("../logs/errors.log", level="ERROR", enqueue=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        logger.info("The application is starting. Create database tables if not exist")
        try:
            await create_db_and_tables()
            yield
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise
        finally:
            logger.info("The application is shutting down")


app = FastAPI(title="This application works with users and their transactions", version="0.1.0", lifespan=lifespan)


app.include_router(transactions.router)
app.include_router(users.router)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(UserServiceError, user_service_exception_handler)
app.add_exception_handler(TransactionServiceError, transaction_service_exception_handler)


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        url_path = request.url.path
        try:
            response: Response = await call_next(request)
            if response.status_code in (
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_409_CONFLICT,
            ):
                logger.warning(f"Request to {url_path} failed")
            else:
                logger.info(f"Successfully accessed {url_path}")
        except Exception as ex:
            logger.error(f"Request to {url_path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7999, reload=True)
