from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.purchase import Purchase
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.purchase import PurchaseCreate, PurchaseOut

router = APIRouter()


@router.get("/", response_model=List[PurchaseOut])
def listar_compras(db: Session = Depends(get_db), _=Depends(get_current_user)):
    # TODO: agregar filtros por fecha, categoria, tienda (para el historial y el dashboard)
    return db.query(Purchase).order_by(Purchase.fecha.desc()).all()


@router.post("/", response_model=PurchaseOut)
def registrar_compra(
    data: PurchaseCreate,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    compra = Purchase(**data.model_dump(), usuario_id=usuario_actual.id)
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra


# TODO: endpoint /purchases/resumen -> total del mes, por categoria y por tienda
#       (alimenta el dashboard)
# TODO: endpoint /purchases/comparacion-precios -> mismo producto en distintas tiendas
