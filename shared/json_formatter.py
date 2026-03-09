import logging
import json
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        # Campos básicos

        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)

        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": dt.isoformat(),
        }

        # Extraer campos personalizados (el 'extra')
        # Evitamos los atributos estándar de logging para quedarnos solo con lo tuyo
        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName'
        }
        
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        log_record["extra"] = extra if extra else None

        # Devolvemos un string JSON
        return json.dumps(log_record, ensure_ascii=False)