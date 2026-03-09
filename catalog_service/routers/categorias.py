from fastapi import APIRouter, HTTPException
from typing import List
from catalog_service.DataBase.db import get_connection
from catalog_service.models.schemas import CategoriaCreate, CategoriaOut


router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("/", response_model=List[CategoriaOut])
def listar_categorias():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM Categorias ORDER BY nombre_categoria").fetchall()
    return [CategoriaOut(**dict(r)) for r in rows]


@router.get("/{categoria_id}", response_model=CategoriaOut)
def obtener_categoria(categoria_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM Categorias WHERE id = ?", (categoria_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    return CategoriaOut(**dict(row))


@router.post("/", response_model=CategoriaOut, status_code=201)
def create_categoria(categoria: CategoriaCreate):
    with get_connection() as conn:
        cursor = conn.execute("INSERT INTO Categorias (nombre_categoria) VALUES (?)", (categoria.nombre_categoria,))
        nuevo_id = cursor.lastrowid
    return obtener_categoria(nuevo_id)


@router.patch("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(categoria_id: int, categoria: CategoriaCreate):
    with get_connection() as conn:
        result = conn.execute("UPDATE Categorias SET nombre_categoria = ? WHERE id = ?", (categoria.nombre_categoria, categoria_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="categoria no encontrada")
    return obtener_categoria(categoria_id)


@router.delete("/{categoria_id}", status_code=204)
def eliminar_categoria(categoria_id: int):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM Categorias WHERE id = ?", (categoria_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Categoria no encontrada")
        
