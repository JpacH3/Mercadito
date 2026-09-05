import uuid

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
