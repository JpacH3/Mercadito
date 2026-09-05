"""
Calcula, para cada producto, cada cuanto se suele comprar y si ya
deberia estar por acabarse segun ese patron.

Importante: esto NO es inventario real, es un estimado basado en el
historial de compras (ver la conversacion de planeacion sobre este punto).
"""
from datetime import date
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.purchase import Purchase


def calcular_predicciones(db: Session) -> list[dict]:
    compras = db.query(Purchase).order_by(Purchase.fecha).all()

    por_producto = defaultdict(list)
    for compra in compras:
        por_producto[compra.product_id].append(compra.fecha)

    resultados = []
    hoy = date.today()

    for product_id, fechas in por_producto.items():
        if len(fechas) < 2:
            continue  # se necesitan al menos 2 compras para estimar

        fechas_ordenadas = sorted(fechas)
        intervalos = [
            (fechas_ordenadas[i] - fechas_ordenadas[i - 1]).days
            for i in range(1, len(fechas_ordenadas))
        ]
        promedio_dias = sum(intervalos) / len(intervalos)

        ultima_compra = fechas_ordenadas[-1]
        dias_desde_ultima = (hoy - ultima_compra).days

        if dias_desde_ultima >= promedio_dias:
            estado = "urgente"
        elif dias_desde_ultima >= promedio_dias * 0.7:
            estado = "se_acerca"
        else:
            estado = "con_tiempo"

        resultados.append({
            "product_id": str(product_id),
            "promedio_dias_entre_compras": round(promedio_dias),
            "dias_desde_ultima_compra": dias_desde_ultima,
            "estado": estado,
        })

    # los mas urgentes primero
    resultados.sort(key=lambda r: r["dias_desde_ultima_compra"] / max(r["promedio_dias_entre_compras"], 1), reverse=True)
    return resultados
