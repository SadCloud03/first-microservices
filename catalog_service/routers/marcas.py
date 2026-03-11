from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from catalog_service.auth import obtener_usuario_actual
from catalog_service.DataBase.db import get_connection
from catalog_service.models.schemas import MarcaCreate, MarcaOut
from shared.logger import _build_logger



logger_marcas = _build_logger("marcas_catalog_service", 2)
router = APIRouter(prefix="/marcas", tags=["Marcas"])


@router.get("/", response_model=List[MarcaOut])
def listar_marcas():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM Marcas ORDER BY nombre_marca").fetchall()
    return [MarcaOut(**dict(r)) for r in rows]


@router.get("/{marca_id}", response_model=MarcaOut)
def obtener_marca(marca_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM Marcas WHERE id = ?", (marca_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return MarcaOut(**dict(row))


@router.post("/", response_model=MarcaOut, status_code=201)
def crear_marca(marca: MarcaCreate, usuario : str = Depends(obtener_usuario_actual)):
    with get_connection() as conn:
        cursor = conn.execute("INSERT INTO Marcas (nombre_marca) VALUES (?)", (marca.nombre_marca,))
        nuevo_id = cursor.lastrowid
        logger_marcas.info(f"Marca {marca.nombre_marca} fue creada con id : {nuevo_id}")

    return obtener_marca(nuevo_id)


@router.patch("/{marca_id}", response_model=MarcaOut)
def actualizar_marca(marca_id: int, marca: MarcaCreate, usuario : str = Depends(obtener_usuario_actual)):
    with get_connection() as conn:
        result = conn.execute("UPDATE Marcas SET nombre_marca = ? WHERE id = ?", (marca.nombre_marca, marca_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Marca no encontrada")
    return obtener_marca(marca_id)


@router.delete("/{marca_id}", status_code=204)
def eliminar_marca(marca_id: int, usuario : str = Depends(obtener_usuario_actual)):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM Marcas WHERE id = ?", (marca_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        
