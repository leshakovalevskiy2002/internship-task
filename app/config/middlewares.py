from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger


def setup_middlewares(app: FastAPI) -> None:
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
            except Exception:
                logger.exception(f"Request to {url_path} failed")
                response = JSONResponse(content={"success": False}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return response
