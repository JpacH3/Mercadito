"""
Configuracion de la conexion a Postgres (Neon) usando SQLAlchemy.

DATABASE_URL se lee de una variable de entorno, nunca hardcodeada.
Formato esperado (Neon te lo da tal cual en su panel):
    postgresql://usuario:password@host/nombre_db?sslmode=require
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Falta la variable de entorno DATABASE_URL. "
        "Copia .env.example a .env y complétala con tu cadena de conexion de Neon."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesion de base de datos por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
