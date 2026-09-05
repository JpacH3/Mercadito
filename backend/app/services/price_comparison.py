"""
Compara el ultimo precio de un mismo producto entre distintas tiendas.

Se usa en dos momentos (ver planeacion):
    1. Al confirmar un producto en una lista de compra activa.
    2. En una vista de comparacion dentro del historial/dashboard.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.purchase import Purchase

UMBRAL_DIFERENCIA_PORCENTUAL = 10  # ajustable


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
