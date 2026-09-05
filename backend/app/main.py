"""
Punto de entrada de la aplicacion FastAPI.

Para correr en desarrollo:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, products, purchases, shopping_lists, predictions

app = FastAPI(
    title="Mercadito API",
    description="Backend de control de mercado del hogar (La Despensa)",
    version="0.1.0",
)

# TODO: en produccion, restringir origins al dominio real del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
