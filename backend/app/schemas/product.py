import uuid
from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    nombre: str
    categoria_id: Optional[uuid.UUID] = None
    unidad_default: Optional[str] = None
    codigo_barras: Optional[str] = None


class ProductOut(ProductCreate):
    id: uuid.UUID

    class Config:
        from_attributes = True
