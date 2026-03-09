from fastapi import FastAPI, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from DataBase.db import engine, Base
from DataBase.deps import get_db
from models.models import Service, Token, Log
from models.schemas import LogIn, LogOut
from datetime import datetime
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # ligica de shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.post("/logs") #patch para la operacion POST
async def create_log(
    log_in: LogIn,
    authorization: str = Header(..., alias="Authorization"), # Lo llamamos por su nombre real
    session: AsyncSession = Depends(get_db)
):
    # 1. Validar formato del prefijo Bearer
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid token format. Use 'Bearer <token>'"
        )

    # 2. Extraer el token limpiamente
    token_str = authorization.replace("Bearer ", "").strip()

    # 3. Buscar en la DB
    result = await session.execute(
        select(Token).where(Token.token == token_str, Token.is_active == True)
    )
    token_obj = result.scalar_one_or_none()

    # 4. Si no existe, lanzamos el error con tu mensaje
    if not token_obj:
        # Aquí es donde forzamos tu mensaje personalizado
        raise HTTPException(status_code=401, detail="Invalid token (quien sos bro...)")

    # 5. hacer el nuevo log que se va a mandar a la base de datos
    new_log = Log(
        service_id=token_obj.service_id,
        level=log_in.level.upper(),
        message=log_in.message,
        extra=log_in.extra
    )
    # 6. enviar a la base de datos y darle commit() a la operacion
    session.add(new_log)
    await session.commit()

    return {"status": "ok"}

# path operation paon de operacion GET de /logs 
@app.get("/logs", response_model=List[LogOut])
async def get_logs(
    service_name: str | None = Query(None, alias="service"),
    level: str | None = Query(None),
    # Filtros de Recepción (cuando llegó a la base de datos)
    received_at_start: datetime | None = Query(None),
    received_at_end: datetime | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    query = select(Log).order_by(Log.created_at.desc())

    # --- Filtros de Texto ---
    if level:
        query = query.where(Log.level == level.upper())
    if service_name:
        query = query.join(Log.service).where(Service.name == service_name)

    # --- Filtros de Tiempo (Received At) ---
    # Usamos created_at que es la fecha de inserción en DB
    if received_at_start:
        query = query.where(Log.created_at >= received_at_start)
    if received_at_end:
        query = query.where(Log.created_at <= received_at_end)

    # Paginación
    query = query.limit(limit).offset(offset)

    # hacer la query a la base de datos obtener los resultados y devolverlos 
    res = await db.execute(query)
    logs = res.scalars().all()
    return logs