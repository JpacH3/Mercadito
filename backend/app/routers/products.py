from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.routers.auth import get_current_user
from app.schemas.product import ProductCreate, ProductOut

router = APIRouter()


@router.get("/", response_model=List[ProductOut])
def listar_productos(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Product).all()


@router.post("/", response_model=ProductOut)
def crear_producto(data: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    producto = Product(**data.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


# TODO: endpoint para buscar por alias_texto y resolver el producto real
# cuando se importe una factura (ver app/services/normalizacion.py)
