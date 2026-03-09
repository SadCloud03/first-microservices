from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from catalog_service.DataBase.db import get_connection
from catalog_service.models.schemas import VarianteCreate, VarianteOut, VarianteUpdate, StockUpdate
from shared.logger import _build_logger


variantes_logger = _build_logger("variantes_catalog_service", 2)
stock_logger = _build_logger("variantes_stock_catalog_service", 2)

router = APIRouter(prefix="/variantes", tags=["Variantes"])


def row_to_variante(row):
    return VarianteOut(**dict(row))


@router.get("/", response_model=List[VarianteOut])
def listar_variantes(
    id_producto: Optional[int] = Query(None),
    calce: Optional[float] = Query(None),
    color: Optional[str] = Query(None),
    solo_con_stock: bool = Query(False),
    stock_min: Optional[int] = Query(None)
):
    query = """
        SELECT
            v.id, v.id_producto, v.calce, v.color, v.stock, p.nombre AS nombre_producto
        FORM Variantes_producto v
        JOIN Productos p ON v.id_producto = p.id 
        WHERE 1=1
    """

    params = []

    if id_producto is not None:
        query += " AND v.id_producto = ?"
        params.append(id_producto)
    if calce is not None:
        query += " AND v.calce = ?"
        params.append(calce)
    if color:
        query += " AND v.color LIKE ?"
        params.append(f"%{color}%")
    if solo_con_stock:
        query += " AND v.stock > 0"
    if stock_min is not None:
        query += " AND v.stock >= ?"
        params.append(stock_min)
    
    query += " ORDER BY v.id_producto, v.calce"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    
    return [row_to_variante(r) for r in rows]



@router.get("/{variante_id}", response_model=VarianteOut)
def obtener_variante(variante_id: int):
    query = """
        SELECT 
            v.id, v.id_producto, v.calce, v.color, v.stock,
            p.nombre AS nombre_producto
        FROM Variantes_producto v
        JOIN Productos p ON v.id_producto = p.id 
        WHERE v.id = ?
    """

    with get_connection() as conn:
        row = conn.execute(query, (variante_id,)).fetchone()
    if not row:
        variantes_logger.warning(f"Variante de id : {variante_id} no fue encontrada [obtener_variante]")
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    return row_to_variante(row=row)



@router.post("/", response_model=VarianteOut, status_code=201)
def crear_variante(variante: VarianteCreate):
    with get_connection() as conn:
        if not conn.execute("SELECT 1 FROM Productos WHERE id = ?", (variante.id_producto,)).fetchone():
            raise HTTPException(status_code=400, detail="Producto no existe")
        cursor = conn.execute(
            "INSERT INTO Variantes_producto (id_producto, calce, color, stock) VALUES (?, ?, ?, ?)",
            (variante.id_producto, variante.calce, variante.color, variante.stock)
        )
        nuevo_id = cursor.lastrowid
        variantes_logger.info(f"Nueva variante de producto id : {variante.id_producto} fue creada...")
    return obtener_variante(nuevo_id)



@router.patch("/{variante_id}", response_model=VarianteOut)
def actualizar_variante(variante_id: int, datos: VarianteUpdate):
    campos = datos.model_dump(exclude_none=True)
    if not campos:
        variantes_logger.warning(f"al intentar actualizar variante id : {variante_id} no se enviaron campos...")
        raise HTTPException(status_code=400, detail="No se enviaron campos a actializar")
    set_clause = ", ".join(f"{k} = ?" for k in campos)
    values = list(campos.values()) + [variante_id]
    with get_connection() as conn:
        result = conn.execute(f"UPDATE Variante_producto SET {set_clause} WHERE id = ?", values)
        if result.lastrowid == 0:
            variantes_logger.warning(f"variante de id : {variante_id} no fue encontrada [actualizar_variante]")
            raise HTTPException(status_code=404, detail="Variante no encontrada")
    return obtener_variante(variante_id)



@router.delete("/{variante_id}", status_code=204)
def eliminar_variante(variante_id: int):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM  Variantes_producto WHERE id = ?", (variante_id,))
        if result.rowcount == 0:
            variantes_logger.warning(f"variante de id : {variante_id} no fue encontrada [eliminar_variante]")
            raise HTTPException(status_code=404, detail="Variante no encontrada")
        variantes_logger.info(f"Variante id : {variante_id} fue eliminada...")



@router.patch("/{variante_id}/stock", response_model=VarianteOut)
def ajustar_stock(variante_id: int, body: StockUpdate):
    with get_connection() as conn:
        row = conn.execute("SELECT stock FROM Variantes_producto WHERE id = ?", (variante_id)).fetchone()
        if not row:
            stock_logger.warning(f"Variante id : {variante_id} no fue encontrada [ajustar_stock]")
            raise HTTPException(status_code=404, detail="Variante no encontrada")
        nuevo_stock = row["stock"] + body.cantidad
        if nuevo_stock < 0:
            stock_logger.warning(f"el stock de la variante id : {variante_id}, no fue suficiente stock : {nuevo_stock}")
            raise HTTPException(status_code=400, detail=f"Stock insuficiente. Actual: {row['stock']}")
        stock_logger.info(f"El stock de la variante id : {variante_id} fue actualizado stock : {nuevo_stock}")
        conn.execute("UPDATE Variantes_producto SET stock = ? WHERE id = ?", (nuevo_stock, variante_id))
    return obtener_variante(variante_id)



@router.put("/{variante_id}/stock", response_model=VarianteOut)
def establecer_stock(variante_id: int, body: StockUpdate):
    if body.cantidad < 0:
        stock_logger.warning(f"la variante id : {variante_id} intento agregar cantidad : {body.cantidad} a su stock")
        raise HTTPException(status_code=400, detail="El stock no puede ser negativo")
    with get_connection() as conn:
        result = conn.execute("UPDATE Variantes_producto SET stock = ? WHERE id = ?", (body.cantidad, variante_id))
        if result.rowcount == 0:
            stock_logger.warning(f"Variante id : {variante_id} no fue encontrada [establecer_stock]")
            raise HTTPException(status_code=404, detail="Variante no encontrada")
        stock_logger.info(f"se agrego stock : {body.cantidad} a la variante id : {variante_id}")
    return obtener_variante(variante_id)