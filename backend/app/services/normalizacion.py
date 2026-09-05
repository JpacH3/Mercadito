"""
Cuando se importa una factura (CSV/JSON extraido), los nombres de producto
pueden venir distintos cada vez (ej. "ACEITE DE GIR" vs "aceite girasol").

Este servicio busca si el texto ya existe como alias de un producto
conocido; si no, hay que crear el producto y/o el alias nuevo.

TODO: implementar la logica real de matching (por ahora es un placeholder).
Ideas para cuando lo desarrolles:
    - Comparacion exacta primero (mas rapido)
    - Luego una comparacion difusa (ej. libreria rapidfuzz) para variaciones
    - Si no hay match razonable, devolver None y que la app pregunte al usuario
"""
from sqlalchemy.orm import Session

from app.models.product import Product, ProductAlias


def resolver_producto_por_texto(db: Session, texto: str) -> Product | None:
    alias = db.query(ProductAlias).filter(ProductAlias.alias_texto.ilike(texto)).first()
    if alias:
        return alias.producto

    # TODO: agregar comparacion difusa aqui antes de devolver None
    return None
