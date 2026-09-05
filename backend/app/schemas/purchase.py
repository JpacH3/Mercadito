import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel


class PurchaseCreate(BaseModel):
    product_id: uuid.UUID
    fecha: date
    cantidad: float = 1
    unidad: Optional[str] = None
    precio_unitario: Optional[float] = None
    precio_total: float
    tienda: Optional[str] = None
    origen: str = "manual"


class PurchaseOut(PurchaseCreate):
    id: uuid.UUID
    usuario_id: uuid.UUID

    class Config:
        from_attributes = True
