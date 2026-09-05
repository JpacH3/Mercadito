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

## Lo que falta por programar (marcado con TODO en el código)

- Endpoints de `shopping_lists`: agregar item, confirmar item, cerrar lista
- Cálculo de resumen para el dashboard (total por mes/categoría/tienda)
- Integración real de comparación de precios en el flujo de confirmar item
- Migraciones con Alembic (ver `backend/alembic/README.md`)
- Lógica real de `services/normalizacion.py` para las facturas importadas
- Frontend: pantallas de login, dashboard, registro, modo lista en tienda
- Bot de Telegram (cuando decidas qué notificar)
