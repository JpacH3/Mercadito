import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False, unique=True)

    # TODO: si mas adelante quieres subcategorias, agregar aqui:
    # parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
