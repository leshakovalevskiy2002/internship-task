from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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


async def request_validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": _format_validation_errors(exc)},
    )
