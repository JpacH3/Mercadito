import uuid

from sqlalchemy import Column, Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    fecha = Column(Date, nullable=False)
    cantidad = Column(Float, nullable=False, default=1)
    unidad = Column(String, nullable=True)
    precio_unitario = Column(Float, nullable=True)
    precio_total = Column(Float, nullable=False)
    tienda = Column(String, nullable=True)

    # manual | factura | lista_compra
    origen = Column(String, nullable=False, default="manual")

    producto = relationship("Product")
    usuario = relationship("User")
