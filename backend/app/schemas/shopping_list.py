import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class ShoppingListCreate(BaseModel):
    fecha_creacion: date
    presupuesto: Optional[float] = None  # opcional, solo referencia
    tienda: Optional[str] = None  # un viaje = una tienda; puede no saberse aun


class ShoppingListOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    fecha_creacion: date
    presupuesto: Optional[float] = None
    tienda: Optional[str] = None
    estado: str

    class Config:
        from_attributes = True


class ShoppingListItemCreate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    cantidad_planeada: Optional[float] = None
    precio_esperado: Optional[float] = None  # si no se manda, se autocompleta con el ultimo precio conocido


class ShoppingListItemOut(BaseModel):
    id: uuid.UUID
    shopping_list_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    usuario_id: Optional[uuid.UUID] = None
    cantidad_planeada: Optional[float] = None
    precio_esperado: Optional[float] = None
    cantidad_confirmada: Optional[float] = None
    precio_confirmado: Optional[float] = None
    confirmado: bool
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShoppingListWithItemsOut(ShoppingListOut):
    items: List[ShoppingListItemOut] = []


class ShoppingListItemConfirm(BaseModel):
    cantidad_confirmada: float
    precio_confirmado: float  # precio unitario


class AlertaPrecio(BaseModel):
    tienda_referencia: str
    precio_referencia: float
    diferencia_porcentual: float


class ConfirmarItemResponse(BaseModel):
    item: ShoppingListItemOut
    alerta_precio: Optional[AlertaPrecio] = None


class CerrarListaResponse(BaseModel):
    lista: ShoppingListOut
    compras_creadas: int
