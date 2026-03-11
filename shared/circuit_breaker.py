import time
from functools import wraps
from fastapi import HTTPException
from shared.logger import _build_logger

# Este logger usará la configuración que ya tienes (HTTPLogHandler)
breaker_logger = _build_logger("catalgo_circuitbracker", 4)

class CircuitBreaker:
    def __init__(self, service_name: str, failure_threshold=3, recovery_timeout=30):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = None

    async def _log_state_change(self, new_state, message):
        """Envía un log crítico a la base de datos cuando el estado cambia."""
        log_msg = f"[{self.service_name}] BREAKER {new_state}: {message}"
        if new_state == "OPEN":
            breaker_logger.critical(log_msg, extra={"failures": self.failures, "state": new_state})
        else:
            breaker_logger.warning(log_msg, extra={"state": new_state})

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Verificar si está ABIERTO
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF-OPEN"
                    await self._log_state_change("HALF-OPEN", "Intentando recuperación...")
                else:
                    raise HTTPException(
                        status_code=503, 
                        detail=f"Circuito abierto. Fallas previas hacia {self.service_name}"
                    )

            try:
                result = await func(*args, **kwargs)
                
                # Si tiene éxito y estaba recuperándose o abierto, cerramos
                if self.state in ["OPEN", "HALF-OPEN"]:
                    self.state = "CLOSED"
                    self.failures = 0
                    await self._log_state_change("CLOSED", "Servicio restablecido correctamente.")
                
                self.failures = 0 
                return result

            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                
                if self.failures >= self.failure_threshold and self.state != "OPEN":
                    self.state = "OPEN"
                    await self._log_state_change("OPEN", f"Umbral de fallas alcanzado ({self.failures}). Bloqueando tráfico.")
                
                raise e
        return wrapper

# Instancia específica para el catálogo
catalog_breaker = CircuitBreaker(service_name="CATALOG-SERVICE", failure_threshold=3, recovery_timeout=60)