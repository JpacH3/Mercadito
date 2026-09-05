from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.purchase import Purchase
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.shopping_list import (
    CerrarListaResponse,
    ConfirmarItemResponse,
    ShoppingListCreate,
    ShoppingListItemConfirm,
    ShoppingListItemCreate,
    ShoppingListItemOut,
    ShoppingListOut,
    ShoppingListWithItemsOut,
)
from app.services import price_comparison

router = APIRouter()


def _obtener_lista_o_404(db: Session, lista_id: UUID) -> ShoppingList:
    lista = db.query(ShoppingList).filter(ShoppingList.id == lista_id).first()
    if not lista:
        raise HTTPException(status_code=404, detail="Lista de compras no encontrada")
    return lista


def _obtener_item_o_404(db: Session, lista_id: UUID, item_id: UUID) -> ShoppingListItem:
    item = (
        db.query(ShoppingListItem)
        .filter(ShoppingListItem.id == item_id, ShoppingListItem.shopping_list_id == lista_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado en esta lista")
    return item


@router.post("/", response_model=ShoppingListOut)
def crear_lista(
    data: ShoppingListCreate,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    lista = ShoppingList(
        usuario_id=usuario_actual.id,
        fecha_creacion=data.fecha_creacion,
        presupuesto=data.presupuesto,  # puede ser None, es solo referencia
        tienda=data.tienda,  # puede ser None si aun no se sabe
        estado="abierta",
    )
    db.add(lista)
    db.commit()
    db.refresh(lista)
    return lista


@router.get("/", response_model=List[ShoppingListOut])
def listar_listas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(ShoppingList).order_by(ShoppingList.fecha_creacion.desc()).all()


@router.get("/pendientes", response_model=List[ShoppingListItemOut])
def listar_pendientes(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Items no confirmados de listas ya cerradas. El usuario decide manualmente
    si los lleva a una lista nueva; no se copian ni se borran automaticamente."""
    return (
        db.query(ShoppingListItem)
        .join(ShoppingList, ShoppingListItem.shopping_list_id == ShoppingList.id)
        .filter(ShoppingList.estado == "cerrada", ShoppingListItem.confirmado.is_(False))
        .all()
    )


@router.get("/{lista_id}", response_model=ShoppingListWithItemsOut)
def obtener_lista(
    lista_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return _obtener_lista_o_404(db, lista_id)


@router.post("/{lista_id}/items", response_model=ShoppingListItemOut)
def agregar_item(
    lista_id: UUID,
    data: ShoppingListItemCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    lista = _obtener_lista_o_404(db, lista_id)
    if lista.estado != "abierta":
        raise HTTPException(status_code=400, detail="No se pueden agregar items a una lista cerrada")

    precio_esperado = data.precio_esperado
    if precio_esperado is None and data.product_id is not None:
        ultima_compra = (
            db.query(Purchase)
            .filter(Purchase.product_id == data.product_id, Purchase.precio_unitario.isnot(None))
            .order_by(Purchase.fecha.desc())
            .first()
        )
        if ultima_compra:
            precio_esperado = ultima_compra.precio_unitario

    item = ShoppingListItem(
        shopping_list_id=lista.id,
        product_id=data.product_id,
        cantidad_planeada=data.cantidad_planeada,
        precio_esperado=precio_esperado,
        confirmado=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{lista_id}/items/{item_id}/confirmar", response_model=ConfirmarItemResponse)
def confirmar_item(
    lista_id: UUID,
    item_id: UUID,
    data: ShoppingListItemConfirm,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    lista = _obtener_lista_o_404(db, lista_id)
    if lista.estado != "abierta":
        raise HTTPException(status_code=400, detail="No se pueden confirmar items de una lista cerrada")

    item = _obtener_item_o_404(db, lista_id, item_id)

    item.cantidad_confirmada = data.cantidad_confirmada
    item.precio_confirmado = data.precio_confirmado
    item.confirmado = True
    item.usuario_id = usuario_actual.id
    db.commit()
    db.refresh(item)

    alerta = None
    if item.product_id is not None and lista.tienda:
        alerta = price_comparison.comparar_precio_nuevo(
            db, item.product_id, lista.tienda, data.precio_confirmado
        )

    return ConfirmarItemResponse(item=item, alerta_precio=alerta)


@router.post("/{lista_id}/cerrar", response_model=CerrarListaResponse)
def cerrar_lista(
    lista_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    lista = _obtener_lista_o_404(db, lista_id)
    if lista.estado != "abierta":
        raise HTTPException(status_code=400, detail="Esta lista ya esta cerrada")

    items_confirmados = (
        db.query(ShoppingListItem)
        .filter(ShoppingListItem.shopping_list_id == lista.id, ShoppingListItem.confirmado.is_(True))
        .all()
    )

    compras_creadas = 0
    for item in items_confirmados:
        if item.product_id is None or item.cantidad_confirmada is None or item.precio_confirmado is None:
            continue  # item sin producto o sin datos suficientes, no se puede convertir en compra

        compra = Purchase(
            product_id=item.product_id,
            usuario_id=item.usuario_id or usuario_actual.id,
            fecha=date.today(),
            cantidad=item.cantidad_confirmada,
            precio_unitario=item.precio_confirmado,
            precio_total=item.cantidad_confirmada * item.precio_confirmado,
            tienda=lista.tienda,
            origen="lista_compra",
        )
        db.add(compra)
        compras_creadas += 1

    lista.estado = "cerrada"
    db.commit()
    db.refresh(lista)

    # los items no confirmados no se tocan: quedan visibles en /pendientes
    return CerrarListaResponse(lista=lista, compras_creadas=compras_creadas)
