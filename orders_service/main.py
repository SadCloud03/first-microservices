from fastapi import FastAPI 
from contextlib import asynccontextmanager
from orders_service.DataBase.db import init_db
from orders_service.routers import ordenes
from shared.logging_middleware import LoggingMiddleware
from shared.logger import _build_logger

system_logger = _build_logger("orders-service", 1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    system_logger.info("Iniciando Microservicio de Ordenes")
    init_db()
    yield
    system_logger.info("Cerrando Microservicio de Ordenes")

app = FastAPI(
    title="Microservicio de Ordenes",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)

app.include_router(ordenes.router)

@app.get("/", tags=["Health"])
def health():
    return {
        "status" : "ok",
        "service" : "orders-microservice"
    }