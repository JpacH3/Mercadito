from datetime import date
from typing import Optional

from pydantic import BaseModel


class ShoppingListCreate(BaseModel):
    fecha_creacion: date
    presupuesto: Optional[float] = None  # opcional, solo referencia


class ShoppingListItemCreate(BaseModel):
    product_id: Optional[str] = None
    cantidad_planeada: Optional[float] = None
    precio_esperado: Optional[float] = None


class ShoppingListItemConfirm(BaseModel):
    cantidad_confirmada: float
    precio_confirmado: float
