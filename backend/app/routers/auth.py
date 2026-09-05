"""
Autenticacion con usuario y contrasena individual (2 usuarios: tu y tu esposa).

Flujo:
    POST /auth/register  -> crea un usuario (usalo una sola vez por persona)
    POST /auth/login      -> devuelve un JWT que se manda luego en cada request
                             como header: Authorization: Bearer <token>

TODO antes de usar en produccion:
    - Definir SECRET_KEY como variable de entorno (no dejarla fija en el codigo)
    - Ajustar el tiempo de expiracion del token a tu gusto
"""
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserOut

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def crear_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesion",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existente = db.query(User).filter(User.email == data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ese correo ya esta registrado")

    nuevo_usuario = User(
        nombre=data.nombre,
        email=data.email,
        password_hash=pwd_context.hash(data.password),
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.get("/me", response_model=UserOut)
def me(usuario_actual: User = Depends(get_current_user)):
    return usuario_actual


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == form_data.username).first()
    if not usuario or not pwd_context.verify(form_data.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contrasena incorrectos")

    token = crear_token({"sub": str(usuario.id)})
    return Token(access_token=token)
