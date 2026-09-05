"""
Punto de entrada de la aplicacion FastAPI.

Para correr en desarrollo:
    uvicorn app.main:app --reload
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, products, purchases, shopping_lists, predictions

app = FastAPI(
    title="Mercadito API",
    description="Backend de control de mercado del hogar (La Despensa)",
    version="0.1.0",
)

# En produccion, frontend y backend quedan en el mismo dominio (ver mount
# de StaticFiles mas abajo), asi que el navegador ni pasa por CORS ahi.
# Estos origenes son solo para cuando el frontend corre local con
# `python -m http.server` en un puerto distinto al de uvicorn (ver
# docs/DESARROLLO.md).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
app.include_router(shopping_lists.router, prefix="/shopping-lists", tags=["shopping_lists"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])


@app.get("/health")
def health_check():
    """Endpoint simple para verificar que el servicio esta arriba."""
    return {"status": "ok"}


# Sirve el frontend (PWA estatica) desde el mismo proceso/dominio que la
# API. Va al final a proposito: los routers de arriba se resuelven
# primero, y esto queda como fallback para todo lo demas (index.html,
# manifest.json, static/*, service-worker.js).
#
# La profundidad de carpetas hasta "frontend/" no es la misma en local
# (backend/app/main.py -> repo_root/frontend) que en la imagen Docker
# (el Dockerfile aplana "backend/app" a "./app", asi que aqui queda
# app/main.py -> /app/frontend) -- se proban ambas rutas.
_candidatos_frontend = [
    Path(__file__).resolve().parent.parent.parent / "frontend",  # local
    Path(__file__).resolve().parent.parent / "frontend",  # docker
]
_frontend_dir = next((p for p in _candidatos_frontend if p.exists()), None)
if _frontend_dir:
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
