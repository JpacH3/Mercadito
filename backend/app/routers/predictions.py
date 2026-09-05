from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.services import prediction

router = APIRouter()


@router.get("/reabastecimiento")
def reabastecimiento(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """
    Devuelve la lista de productos con su estimado de reabastecimiento.
    Recordatorio: esto es un ESTIMADO por frecuencia de compra, no inventario real.
    """
    return prediction.calcular_predicciones(db)
