import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    unidad_default = Column(String, nullable=True)
    codigo_barras = Column(String, unique=True, nullable=True)

    categoria = relationship("Category")
    aliases = relationship("ProductAlias", back_populates="producto")


class ProductAlias(Base):
    """
    Nombres alternativos con los que puede aparecer un mismo producto
    (ej. facturas escaneadas con distinta redaccion).
    """
    __tablename__ = "product_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    alias_texto = Column(String, nullable=False, index=True)

    producto = relationship("Product", back_populates="aliases")
