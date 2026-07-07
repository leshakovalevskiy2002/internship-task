from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.handlers import (
    request_validation_exception_handler,
    transaction_service_exception_handler,
    user_service_exception_handler,
)
from app.services import TransactionServiceError, UserServiceError


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(UserServiceError, user_service_exception_handler)
    app.add_exception_handler(TransactionServiceError, transaction_service_exception_handler)
