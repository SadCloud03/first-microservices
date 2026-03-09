from pydantic import BaseModel, Field
from typing import Optional


# ----- Para Categorias -----
class CategoriaCreate(BaseModel):
    nombre_categoria: str

class CategoriaOut(BaseModel):
    id: int
    nombre_categoria: str


# ----- Para marcas -----
class MarcaCreate(BaseModel):
    nombre_marca: str

class MarcaOut(BaseModel):
    id: int
    nombre_marca: str


# ----- Para Productos ------
class ProductoCreate(BaseModel):
    id_categoria: int
    id_marca: int
    nombre: str
    descripcion: Optional[str] = None
    precio: float = Field(gt=0)

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = Field(default=None, gt=0)
    id_categoria: Optional[int] = None
    id_marca: Optional[int] = None

class ProductoOut(BaseModel):
    id: int
    id_categoria: int
    id_marca: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    nombre_categoria: Optional[str] = None
    nombre_marca: Optional[str] = None



# ----- para variantes de producto -----
class VarianteCreate(BaseModel):
    id_producto: int
    calce: float = Field(gt=0)
    color: str
    stock: int = Field(gt=0, default=0)

class VarianteUpdate(BaseModel):
    calce: Optional[float] = Field(default=None, gt=0)
    color: Optional[str] = None

class StockUpdate(BaseModel):
    cantidad: int = Field(description="Positivo para sumar, negativo para restar")

class VarianteOut(BaseModel):
    id: int
    id_producto: int
    calce: float
    color: str
    stock: int
    nombre_producto: Optional[str] = None
    
    