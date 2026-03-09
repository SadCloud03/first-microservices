from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class OrdenItemBase(BaseModel):
    id_variante : int
    cantidad : int
    precio_unitario : float

class OrdenItemOut(BaseModel):
    id : int
    id_variante : int
    cantidad : int
    precio_unitario : float
    
    class config:
        from_atributes = True

class OrdenCreate(BaseModel):
    cliente_id : int
    items : List[OrdenItemBase]

class OrdenOut(BaseModel):
    id : int
    cliente_id : int
    fecha : datetime
    estado : str
    total : float
    items : List[OrdenItemOut]

class EstadoUpdate(BaseModel):
    estado : str = Field(..., pattern="^(PENDIENTE|PAGADA|ENVIADA|CANCELADA)$")