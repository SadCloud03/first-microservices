from fastapi import FastAPI
from catalog_service.DataBase.db import init_db
from catalog_service.routers import productos, variantes, categorias, marcas
from shared.logging_middleware import LoggingMiddleware
from shared.logger import _build_logger
from contextlib import asynccontextmanager

db_logger = _build_logger("main_catalog_service", 2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_logger.info("Iniciando Microservicio de Catalogo...")
    init_db()

    yield

    db_logger.info("Cerrando Microservicio de Catalogo....")

app = FastAPI(
    title="Microservicio de Productos",
    lifespan=lifespan,
    description="API para gestionar productos, variantes, categorias y marcas",
    version="1.0.0"
)

app.add_middleware(LoggingMiddleware)

app.include_router(productos.router)
app.include_router(variantes.router)
app.include_router(categorias.router)
app.include_router(marcas.router)


@app.get("/", tags=["Health"])
def health():
    return {
        "status" : "ok",
        "service" : "productos-microservice"
    }