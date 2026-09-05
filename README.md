# Mercadito (La Despensa)

App casera de control de mercado del hogar: registro de compras, gasto por
categoria y proveedor, predicción de reabastecimiento (estimado por
frecuencia de compra) y comparación de precios entre proveedores.

## Stack

- **Backend:** FastAPI (Python), desplegado en Fly.io
- **Base de datos:** PostgreSQL en Neon
- **Frontend:** HTML/JS simple como PWA instalable

## Estructura

```
backend/app/
  main.py          arranque de FastAPI y registro de routers
  database.py      conexion a Postgres via SQLAlchemy
  models/          tablas: users, categories, products, product_aliases,
                    purchases, shopping_lists, shopping_list_items
  schemas/         validacion de entrada/salida (Pydantic)
  routers/         endpoints agrupados por recurso
  services/        logica de negocio: prediccion, comparacion de precios,
                    normalizacion de nombres de producto

frontend/          PWA (manifest, service worker, HTML/CSS/JS)
```

## Arrancar en desarrollo

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env
# completa DATABASE_URL con tu cadena de conexion de Neon

uvicorn app.main:app --reload
```

La API queda arriba en `http://127.0.0.1:8000` — la documentación
interactiva (Swagger) queda automáticamente en `http://127.0.0.1:8000/docs`.

Ver [`docs/DESARROLLO.md`](docs/DESARROLLO.md) para la guía completa de
setup (Neon CLI, `.env`, entorno virtual) y problemas ya resueltos.

## Importar facturas

`backend/scripts/importar_facturas.py` toma el CSV extraído de una
factura (ver columnas en `CLAUDE.md`) y lo carga a la base: crea
categorías/productos que no existan, resuelve duplicados por código de
barras (o por nombre vía `product_aliases` cuando no hay código, o
cuando el mismo código aparece con nombres distintos en el CSV — señal
de error de lectura en el recibo original), y registra cada línea como
una compra con `origen="factura"`.

```bash
cd backend
python scripts/importar_facturas.py ../facturas.csv \
  --usuario-email correo@ejemplo.com \
  --fecha-default 2026-07-01 \
  --dry-run   # quitar --dry-run cuando el resumen se vea bien
```

`--fecha-default` se usa solo para filas del CSV sin fecha (facturas
viejas donde no se conserva la fecha exacta).

## Lo que falta por programar

- Filtros (fecha, categoría, tienda) en `GET /purchases/`, para historial
- Migraciones con Alembic (ver `backend/alembic/README.md`)
- Matching difuso en `services/normalizacion.py` (hoy solo hace match exacto)
- Service worker con cache real para soporte offline (hoy pasa todo directo a la red)
- Asignar categoría a un producto desde la UI (el backend ya lo soporta, falta el selector)
- Bot de Telegram (cuando decidas qué notificar)

Ya completo: backend (`shopping_lists`, `/purchases/resumen`,
`/purchases/comparacion-precios`, importación de facturas) y un
frontend PWA funcional (login, registro, dashboard, productos, compras,
listas de compra con el checklist completo, pendientes, comparación de
precios, predicción de reabastecimiento) — ver `docs/DESARROLLO.md`
para cómo levantarlo.
