from typing import cast

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.service_errors.transaction_errors import (
    NegativeBalanceError,
    TransactionAlreadyRollbackedException,
    TransactionBlockedUserException,
    TransactionDoesNotBelongToUserException,
    TransactionNotExistsError,
    TransactionServiceError,
    TransactionUserBlockedError,
    TransactionUserNotFoundError,
    UserBalanceNotFoundError,
)
from app.services.service_errors.user_errors import (
    UserAlreadyActiveError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserServiceError,
)


def _format_validation_errors(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Validation error"

    first_error = errors[0]
    message = first_error.get("msg", "Validation error")

    ctx = first_error.get("ctx")
    if isinstance(ctx, dict):
        original_error = ctx.get("error")
        if isinstance(original_error, Exception):
            return str(original_error) or message

    return str(message)


async def request_validation_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(RequestValidationError, exc)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": _format_validation_errors(error)},
    )


def _status_for_user_error(exc: UserServiceError) -> int:
    if isinstance(exc, UserAlreadyExistsError):
        return status.HTTP_409_CONFLICT
    if isinstance(exc, UserNotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, (UserAlreadyBlockedError, UserAlreadyActiveError)):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_400_BAD_REQUEST


def _status_for_transaction_error(exc: TransactionServiceError) -> int:
    if isinstance(exc, (TransactionUserNotFoundError, UserBalanceNotFoundError)):
        return status.HTTP_404_NOT_FOUND
    if isinstance(
        exc,
        (
            TransactionUserBlockedError,
            TransactionNotExistsError,
            TransactionDoesNotBelongToUserException,
            TransactionAlreadyRollbackedException,
            TransactionBlockedUserException,
            NegativeBalanceError,
        ),
    ):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_400_BAD_REQUEST


async def user_service_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(UserServiceError, exc)
    return JSONResponse(status_code=_status_for_user_error(error), content={"detail": str(exc)})


async def transaction_service_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(TransactionServiceError, exc)
    return JSONResponse(status_code=_status_for_transaction_error(error), content={"detail": str(exc)})
