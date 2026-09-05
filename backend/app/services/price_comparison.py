"""
Compara el ultimo precio de un mismo producto entre distintas tiendas.

Se usa en dos momentos (ver planeacion):
    1. Al confirmar un producto en una lista de compra activa.
    2. En una vista de comparacion dentro del historial/dashboard.
"""
import uuid
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.purchase import Purchase

UMBRAL_DIFERENCIA_PORCENTUAL = 10  # ajustable


def comparar_precio_nuevo(
    db: Session, product_id: uuid.UUID, tienda_actual: str, precio_actual: float
) -> Optional[dict]:
    """
    Compara un precio que se esta confirmando ahora mismo (en una tienda dada)
    contra el ultimo precio pagado por ese mismo producto en otra tienda.

    Devuelve un aviso informativo si la diferencia es >= UMBRAL_DIFERENCIA_PORCENTUAL,
    o None si no hay con que comparar o la diferencia no es significativa.
    Este aviso nunca bloquea el flujo de confirmar, solo informa.
    """
    ultima_compra_otra_tienda = (
        db.query(Purchase)
        .filter(
            Purchase.product_id == product_id,
            Purchase.tienda.isnot(None),
            Purchase.tienda != tienda_actual,
            Purchase.precio_unitario.isnot(None),
        )
        .order_by(Purchase.fecha.desc())
        .first()
    )

    if not ultima_compra_otra_tienda:
        return None

    precio_referencia = ultima_compra_otra_tienda.precio_unitario
    diferencia_pct = abs(precio_actual - precio_referencia) / precio_referencia * 100

    if diferencia_pct < UMBRAL_DIFERENCIA_PORCENTUAL:
        return None

    return {
        "tienda_referencia": ultima_compra_otra_tienda.tienda,
        "precio_referencia": precio_referencia,
        "diferencia_porcentual": round(diferencia_pct, 1),
    }


def comparar_precios_por_producto(db: Session) -> list[dict]:
    compras = db.query(Purchase).order_by(Purchase.fecha).all()

    ultimo_precio_por_tienda = defaultdict(dict)  # {product_id: {tienda: precio_unitario}}
    for compra in compras:
        if compra.tienda and compra.precio_unitario:
            ultimo_precio_por_tienda[compra.product_id][compra.tienda] = compra.precio_unitario

    resultados = []
    for product_id, precios_por_tienda in ultimo_precio_por_tienda.items():
        if len(precios_por_tienda) < 2:
            continue  # solo se ha comprado en una tienda, no hay que comparar

        precio_min = min(precios_por_tienda.values())
        precio_max = max(precios_por_tienda.values())
        diferencia_pct = ((precio_max - precio_min) / precio_min) * 100

        if diferencia_pct >= UMBRAL_DIFERENCIA_PORCENTUAL:
            resultados.append({
                "product_id": str(product_id),
                "precios_por_tienda": precios_por_tienda,
                "diferencia_porcentual": round(diferencia_pct, 1),
            })

    resultados.sort(key=lambda r: r["diferencia_porcentual"], reverse=True)
    return resultados
