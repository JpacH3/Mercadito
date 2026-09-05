from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.shopping_list import ShoppingList
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.shopping_list import ShoppingListCreate, ShoppingListItemConfirm, ShoppingListItemCreate

router = APIRouter()


@router.post("/")
def crear_lista(
    data: ShoppingListCreate,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    lista = ShoppingList(
        usuario_id=usuario_actual.id,
        fecha_creacion=data.fecha_creacion,
        presupuesto=data.presupuesto,  # puede ser None, es solo referencia
        estado="abierta",
    )
    db.add(lista)
    db.commit()
    db.refresh(lista)
    return lista


# TODO: POST /shopping-lists/{id}/items         -> agregar producto planeado a la lista
# TODO: PATCH /shopping-lists/{id}/items/{item_id}/confirmar
#       -> confirma cantidad/precio real (usa ShoppingListItemConfirm)
#       -> aqui es donde se dispara la alerta de comparacion de precios entre proveedores
# TODO: POST /shopping-lists/{id}/cerrar
#       -> copia los items confirmados a "purchases" con origen="lista_compra"
#       -> los no confirmados quedan tal cual, visibles luego en /shopping-lists/pendientes
# TODO: GET /shopping-lists/pendientes -> junta items no confirmados de listas cerradas
