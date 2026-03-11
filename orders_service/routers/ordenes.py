from dotenv import load_dotenv
load_dotenv()

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from httpx import AsyncClient, ConnectError, HTTPStatusError
from orders_service.DataBase.db import get_connection
from orders_service.models.schemas import OrdenCreate, OrdenOut, EstadoUpdate
from shared.logger import _build_logger
from shared.circuit_breaker import catalog_breaker

orders_logger = _build_logger("orders_service", 1)
router = APIRouter(prefix="/ordenes", tags=["Orders"])

# URL del catalogo 
CATALOG_URL = os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:8000")


# --- FUNCIÓN PROTEGIDA POR EL BREAKER ---
@catalog_breaker
async def llamar_patch_stock(client: AsyncClient, variante_id: int, cantidad: int):
    """
    Esta función centraliza la comunicación con el Catálogo.
    Si el Catálogo falla repetidamente, el breaker abrirá el circuito aquí.
    """
    headers = {"Authorization": f"Bearer {os.getenv("CATALOG_SERVICE_TOKEN")}"}
    response = await client.patch(
        f"{CATALOG_URL}/variantes/{variante_id}/stock",
        json={"cantidad": cantidad},
        headers=headers,
        timeout=3.0
    )
    # Lanza HTTPStatusError si es 4xx o 5xx para que el breaker lo detecte
    response.raise_for_status()
    return response


async def validar_producto_en_catalogo(producto_id: int):
    async with AsyncClient() as client:
        try:
            url = f"{CATALOG_URL}/productos/{producto_id}"
            # print(f"DEBUG: Intentando llamar a: {url}") # <--- Ver en consola
            response = await client.get(url, timeout=2.0)
            print(f"DEBUG: Catálogo respondió con: {response.status_code}")
            return response.status_code == 200
        except ConnectError:
            print("DEBUG: ¡ERROR DE CONEXIÓN! ¿El catálogo está prendido?")
            return False
        except Exception as e:
            print(f"DEBUG: Error inesperado: {e}")
            return False



@router.get("/", response_model=List[OrdenOut])
async def listar_ordenes(
    cliente_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None)
):
    query = "SELECT * FROM Ordenes WHERE 1=1"
    params = []

    if cliente_id:
        query += " AND cliente_id = ?"
        params.append(cliente_id)
    if estado:
        query += " AND estado = ?"
        params.append(estado.upper())

    query += " ORDER BY fecha DESC"
    ordenes_finales = []
    
    try:
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                # Reutilizamos la lógica de obtener_orden para traer los items de cada una
                orden_id = row["id"]
                items_rows = conn.execute("SELECT * FROM Ordenes_items WHERE id_orden = ?", (orden_id,)).fetchall()
                orden_dict = dict(row)
                orden_dict["items"] = [dict(item) for item in items_rows]
                ordenes_finales.append(orden_dict)

        return ordenes_finales

    except Exception as e:
        orders_logger.error(f"Error al listar órdenes: {e}")
        raise HTTPException(status_code=500, detail="Error al recuperar la lista de órdenes")



@router.get("/{orden_id}", response_model=OrdenOut)
async def obtener_orden(orden_id : int):
    with get_connection() as conn:
        orden_row = conn.execute("""SELECT * FROM Ordenes WHERE id = ?""",(orden_id,)).fetchone()
        if not orden_row:
            orders_logger.warning(f"Orden id : {orden_id} no fue encontrada [obtener_orden]")
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        items_rows = conn.execute("""SELECT * FROM Ordenes_items WHERE id_orden = ?""", (orden_id,)).fetchall()

        orden_dict = dict(orden_row)
        orden_dict["items"] = [dict(item) for item in items_rows]
        return orden_dict



@router.post("/", response_model=OrdenOut, status_code=201)
async def create_orden(orden: OrdenCreate):
    async with AsyncClient() as client:
        total_orden = sum(item.cantidad * item.precio_unitario for item in orden.items)
        
        # --- PASO 1: VALIDACIÓN Y DESCUENTO DE STOCK ---
        for item in orden.items:
            try:
                # Usamos la función protegida
                await llamar_patch_stock(client, item.id_variante, -item.cantidad)
                
            except HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"Variante {item.id_variante} no existe.")
                if e.response.status_code == 400:
                    raise HTTPException(status_code=400, detail=f"Stock insuficiente para {item.id_variante}.")
                
                orders_logger.error(f"Error de catálogo: {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail="Error en catálogo")
            
            except HTTPException as e:
                # Re-lanzamos el 503 del Circuit Breaker si el circuito está abierto
                raise e
            except Exception as e:
                orders_logger.error(f"Falla crítica de conexión: {e}")
                raise HTTPException(status_code=503, detail="Servicio de catálogo no disponible")

        # --- PASO 2: PERSISTENCIA EN DB ---
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO Ordenes (cliente_id, estado, total) VALUES (?, ?, ?)",
                    (orden.cliente_id, "PENDIENTE", total_orden)
                )
                orden_id = cursor.lastrowid
                for item in orden.items:
                    conn.execute("""
                        INSERT INTO Ordenes_items (id_orden, id_variante, cantidad, precio_unitario) 
                        VALUES (?, ?, ?, ?)
                    """, (orden_id, item.id_variante, item.cantidad, item.precio_unitario))
                
                orders_logger.info(f"Orden {orden_id} creada. Total: {total_orden}")
            return await obtener_orden(orden_id=orden_id)
        
        except Exception as e:
            orders_logger.error(f"Error al escribir en DB: {e}")
            raise HTTPException(status_code=500, detail="Error interno al guardar la orden")
        


@router.patch("/{orden_id}/estado", response_model=OrdenOut)
async def actualizar_estado_orden(orden_id: int, body: EstadoUpdate):
    nuevo_estado = body.estado.upper()
    orden_actual = await obtener_orden(orden_id) 
    
    if nuevo_estado == "CANCELADA" and orden_actual["estado"] != "CANCELADA":
        async with AsyncClient() as client:
            for item in orden_actual["items"]:
                try:
                    # También protegemos la devolución de stock
                    await llamar_patch_stock(client, item['id_variante'], item['cantidad'])
                except Exception as e:
                    orders_logger.error(f"No se pudo devolver stock de orden {orden_id}: {e}")



    # 3. Actualizar el estado en nuestra base de datos
    try:
        with get_connection() as conn:
            result = conn.execute(
                "UPDATE Ordenes SET estado = ? WHERE id = ?",
                (nuevo_estado, orden_id)
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        orders_logger.info(f"Orden {orden_id} cambió estado a: {nuevo_estado}")
        return await obtener_orden(orden_id)

    except Exception as e:
        orders_logger.error(f"Error al actualizar estado de orden {orden_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar estado")