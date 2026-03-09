import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from shared.logger import _build_logger

request_logger = _build_logger("Requests", 3)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        level = (
            logging.ERROR   if response.status_code >= 500 else
            logging.WARNING if response.status_code >= 400 else
            logging.INFO
        )

        request_logger.log(
            level,
            f"{request.method} {request.url.path} {response.status_code}",
            extra={
                "query_params": str(request.query_params) or None,
                "status_code":  response.status_code,
                "duration_ms":  duration_ms,
            },
        )

        return response