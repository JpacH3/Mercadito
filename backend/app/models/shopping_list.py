import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    fecha_creacion = Column(Date, nullable=False)
    presupuesto = Column(Float, nullable=True)  # opcional, solo referencia, nunca bloqueante

    # un viaje de compras = una tienda; opcional (igual que presupuesto)
    # porque puede no saberse todavia al crear la lista
    tienda = Column(String, nullable=True)

    # abierta | cerrada
    estado = Column(String, nullable=False, default="abierta")

    items = relationship("ShoppingListItem", back_populates="lista")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shopping_list_id = Column(UUID(as_uuid=True), ForeignKey("shopping_lists.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)

    # quien confirmo este item puntual (pensado para el futuro multi-dispositivo)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    cantidad_planeada = Column(Float, nullable=True)
    precio_esperado = Column(Float, nullable=True)  # snapshot del ultimo precio conocido

    cantidad_confirmada = Column(Float, nullable=True)
    precio_confirmado = Column(Float, nullable=True)
    confirmado = Column(Boolean, nullable=False, default=False)

    # util para resolver conflictos cuando haya multiples dispositivos escribiendo
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lista = relationship("ShoppingList", back_populates="items")
    producto = relationship("Product")
