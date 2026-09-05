import uuid
from datetime import date
from typing import List, Optional

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


class TotalPorGrupo(BaseModel):
    nombre: str  # nombre de la categoria o de la tienda
    total: float


class ResumenResponse(BaseModel):
    anio: int
    mes: int
    total_mes: float
    total_mes_anterior: float
    por_categoria: List[TotalPorGrupo]
    por_tienda: List[TotalPorGrupo]


class ComparacionPrecioOut(BaseModel):
    product_id: uuid.UUID
    producto_nombre: Optional[str] = None
    precios_por_tienda: dict
    diferencia_porcentual: float
