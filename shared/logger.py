import logging
import os
from shared.http_handler import HTTPLogHandler
from shared.json_formatter import JsonFormatter

def _build_logger(service_name: str,service_id: int) -> logging.Logger:
    logger = logging.getLogger(service_name)

    if logger.handlers:
        return logger  # ya fue inicializado, no duplicar handlers

    logger.setLevel(logging.DEBUG)

    url     = os.getenv('LOGGING_SERVICE_URL', 'http://localhost:8001/logs')
    token   = os.getenv('LOGGING_TOKEN', 'in_case_token')

    handler = HTTPLogHandler(url=url,service_id=service_id, token=token, timeout=0.5)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    # Tambien loguear a consola en desarrollo
    if os.getenv('ENV', 'development') == 'development':
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
        logger.addHandler(console)

    return logger


# Loggers por dominio — importar el que necesites en cada router