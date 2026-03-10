from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from catalog_service.DataBase.db import get_connection
from catalog_service.models.schemas import ProductoCreate, ProductoUpdate, ProductoOut
from shared.logger import _build_logger
from sqlite3 import IntegrityError
from catalog_service.auth import obtener_usuario_actual


productos_logger = _build_logger("productos_catalog_service", 2) # creacion del logger para este microservicio

router = APIRouter(prefix="/productos", tags=["Productos"]) # manejo de rutas de la api


def row_to_producto(row) -> ProductoOut:
    return ProductoOut(**dict(row))


@router.get("/", response_model=List[ProductoOut])
def buscar_productos(
    nombre: Optional[str] =  Query(None, description="Busqueda parcial por nombre"),
    id_categoria: Optional[int] = Query(None, description="Filtrar por categoria"),
    id_marca: Optional[int] = Query(None, description="Filtrar por marca"),
    precio_min: Optional[float] = Query(None, description="Precio minimo"),
    precio_max: Optional[float] = Query(None, description="Precio maximo"),
    calce: Optional[float] = Query(None, description="Filtrar por talla/calce disponible"),
    color: Optional[str] = Query(None, description="Filtrar por color disponible"),
    solo_con_stock: bool = Query(False, description="Solo productos con stock > 0"),
):

    # "Buscar y filtrar productos, Todos los parametros son opcionales y combinables"

    query = """
        SELECT DISTINCT
            p.id, p.id_categoria, p.id_marca, p.nombre, p.descripcion, p.precio, c.nombre_categoria, m.nombre_marca
        FROM Productos p
        JOIN Categorias c ON p.id_categoria = c.id
        JOIN Marcas m ON p.id_marca = m.id
        LEFT JOIN Variantes_producto v ON p.id = v.id_producto
        WHERE 1=1
    """

    params = []

    # Para los parametros
    if nombre:
        query += " AND p.nombre LIKE ?"
        params.append(f"%{nombre}%")
    if id_categoria:
        query += " AND p.id_categoria = ?"
        params.append(id_categoria)
    if id_marca:
        query += " AND p.id_marca = ?"
        params.append(id_marca)
    if precio_min is not None:
        query += " AND p.precio >= ?"
        params.append(precio_min)
    if precio_max is not None:
        query += " AND p.precio <= ?"
        params.append(precio_max)
    if calce is not None:
        query += " AND v.calce = ?"
        params.append(calce)
    if color:
        query += " AND v.color LIKE ?"
        params.append(f"%{color}%")
    if solo_con_stock:
        query += " AND v.stock > 0"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [row_to_producto(r) for r in rows]



@router.get("/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int):
    query = """
        SELECT 
            p.id, p.id_categoria, p.id_marca, p.nombre, p.descripcion, p.precio,
            c.nombre_categoria, m.nombre_marca
        FROM Productos p
        JOIN Categorias c ON p.id_categoria = c.id
        JOIN Marcas m ON p.id_marca = m.id
        WHERE p.id =?
    """
    with get_connection() as conn:
        row = conn.execute(query, (producto_id,)).fetchone()
    if not row:
        productos_logger.warning(f"producto de id : {producto_id} no fue encontrado [obtener_producto]")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return row_to_producto(row=row)


@router.post("/", response_model=ProductoOut, status_code=201)
def crear_producto(producto: ProductoCreate, usuario : str = Depends(obtener_usuario_actual)):
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO Productos (id_categoria, id_marca, nombre, descripcion, precio) VALUES (?, ?, ?, ?, ?)",
                (producto.id_categoria, producto.id_marca, producto.nombre, producto.descripcion, producto.precio)
            )
            nuevo_id = cursor.lastrowid
            productos_logger.info(f"Producto: {producto.nombre} creado con ID: {nuevo_id}")
        return obtener_producto(nuevo_id)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="La Categoría o Marca proporcionada no existe")



@router.patch("/{producto_id}", response_model=ProductoOut)
def actualizar_producto(producto_id: int, datos: ProductoUpdate, usuario : str = Depends(obtener_usuario_actual)):
    campos = datos.model_dump(exclude_none=True)
    if not campos:
        productos_logger.warning(f"Producto de id : {producto_id} se intento actualizar sin campos")
        raise HTTPException(status_code=400, detail="No se enviaron campos a actualizar")
    set_clause = ", ".join(f"{k} = ?" for k in campos)
    values = list(campos.values()) + [producto_id]
    with get_connection() as conn:

        result = conn.execute(f"UPDATE Productos SET {set_clause} WHERE id = ?", values)
        if result.rowcount == 0:
            productos_logger.warning(f"producto de id : {producto_id} no fue encontrado [actualizar_producto]")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        productos_logger.info(f"Producto de id : {producto_id} fue actualizado con : {campos}")
    return obtener_producto(producto_id)



@router.delete("/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int, usuario : str = Depends(obtener_usuario_actual)):
    with get_connection() as conn:
        result = conn.execute("DELETE FROM Productos WHERE id = ?", (producto_id,))
        if result.rowcount == 0:
            productos_logger.warning(f"producto de id : {producto_id} no fue encontrado [eliminar_producto]")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        productos_logger.info(f"Producto de id : {producto_id} fue eliminado")
        