from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict, Union, List

#toco simular un JSONB (maldito PostgreSQL)
JSONB = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

#
class LogOut(BaseModel):
    id : int
    service_id : int
    level : str
    message : str
    extra : Optional[JSONB]
    created_at : datetime

class LogIn(BaseModel):
    service_id: int   # <-- ¿Está llegando como int?
    level: str
    message: str
    extra: Optional[JSONB] = None # Usa Any temporalmente para debuguear