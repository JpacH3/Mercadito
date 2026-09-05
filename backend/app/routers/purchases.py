from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.purchase import (
    ComparacionPrecioOut,
    PurchaseCreate,
    PurchaseOut,
    ResumenResponse,
    TotalPorGrupo,
)
from app.services import price_comparison

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


def _total_del_mes(db: Session, anio: int, mes: int) -> float:
    total = (
        db.query(func.sum(Purchase.precio_total))
        .filter(extract("year", Purchase.fecha) == anio, extract("month", Purchase.fecha) == mes)
        .scalar()
    )
    return total or 0.0


@router.get("/resumen", response_model=ResumenResponse)
def resumen(
    anio: Optional[int] = Query(None, description="Default: año actual"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Default: mes actual"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Gasto total del mes, comparado con el mes anterior, y desglosado
    por categoria y por tienda. Alimenta el dashboard."""
    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month

    if mes == 1:
        anio_anterior, mes_anterior = anio - 1, 12
    else:
        anio_anterior, mes_anterior = anio, mes - 1

    total_mes = _total_del_mes(db, anio, mes)
    total_mes_anterior = _total_del_mes(db, anio_anterior, mes_anterior)

    filtro_mes = (extract("year", Purchase.fecha) == anio, extract("month", Purchase.fecha) == mes)

    por_categoria_rows = (
        db.query(func.coalesce(Category.nombre, "Sin categoria"), func.sum(Purchase.precio_total))
        .outerjoin(Product, Purchase.product_id == Product.id)
        .outerjoin(Category, Product.categoria_id == Category.id)
        .filter(*filtro_mes)
        .group_by(Category.nombre)
        .all()
    )
    por_tienda_rows = (
        db.query(func.coalesce(Purchase.tienda, "Sin tienda"), func.sum(Purchase.precio_total))
        .filter(*filtro_mes)
        .group_by(Purchase.tienda)
        .all()
    )

    return ResumenResponse(
        anio=anio,
        mes=mes,
        total_mes=total_mes,
        total_mes_anterior=total_mes_anterior,
        por_categoria=[TotalPorGrupo(nombre=nombre, total=total) for nombre, total in por_categoria_rows],
        por_tienda=[TotalPorGrupo(nombre=nombre, total=total) for nombre, total in por_tienda_rows],
    )


@router.get("/comparacion-precios", response_model=List[ComparacionPrecioOut])
def comparacion_precios(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Mismo producto, precios distintos segun la tienda (diferencia >= 10%).
    Vista de historial equivalente al aviso que se muestra al confirmar un
    item de una lista de compras."""
    resultados = price_comparison.comparar_precios_por_producto(db)

    salida = []
    for r in resultados:
        producto = db.query(Product).filter(Product.id == r["product_id"]).first()
        salida.append(
            ComparacionPrecioOut(
                product_id=r["product_id"],
                producto_nombre=producto.nombre if producto else None,
                precios_por_tienda=r["precios_por_tienda"],
                diferencia_porcentual=r["diferencia_porcentual"],
            )
        )
    return salida
