# Guía de desarrollo — Mercadito

Cómo dejar el proyecto corriendo en local y probar lo que se va
construyendo, más los problemas ya resueltos para no repetirlos.

## 1. Requisitos

- Python 3.13 (o compatible)
- Node.js + npm (solo para el CLI de Neon, no para el backend)
- Un proyecto en [Neon](https://neon.tech) ya creado

## 2. Entorno virtual

El entorno virtual vive **dentro de `backend/`** (no en la raíz del repo),
para que coincida con cómo se documenta y se corre el proyecto:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Si en algún momento el entorno queda desincronizado de `requirements.txt`
(por ejemplo, después de que alguien agregue una dependencia nueva),
re-correr `pip install -r requirements.txt` con el entorno activado lo
deja al día — es seguro correrlo varias veces.

## 3. Conexión a Neon

Este proyecto usa el CLI de Neon para obtener la cadena de conexión real
sin copiarla a mano cada vez:

```bash
npm i -g neon@latest
neon login
neon link --project-id shiny-wildflower-29125385 --branch production -y
```

`neon link` genera `.env.local` en la raíz del repo con `DATABASE_URL`,
`DATABASE_URL_UNPOOLED` y `NEON_BRANCH` (gitignored). El backend no lee
ese archivo directamente — lee `.env` (ver `database.py`), así que:

1. Copia `.env.example` a `.env` en la raíz del repo.
2. Pega ahí el `DATABASE_URL` de `.env.local`.
3. Genera un `SECRET_KEY` propio:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

Si Neon llega a rotar la contraseña de la conexión, vuelve a correr
`neon link` y copia el `DATABASE_URL` nuevo de `.env.local` a `.env`.

### Skills y MCP de Neon

Ya están instalados en este repo (`neon skills -y` corrido una vez,
ver `skills-lock.json` y `.claude/skills/`) y el servidor MCP de Neon
está registrado para Claude Code, GitHub Copilot CLI y VS Code
(`neon mcp -y`). No hace falta volver a instalarlos.

## 4. Crear las tablas (mientras no hay Alembic)

Alembic todavía no está inicializado (es un TODO pendiente, ver
`backend/alembic/README.md`). Para no bloquear el desarrollo mientras
tanto, las tablas se crean una vez con un bootstrap directo de
SQLAlchemy:

```bash
cd backend
source .venv/Scripts/activate
python -c "
from dotenv import load_dotenv
load_dotenv('../.env')
from app.database import Base, engine
from app.models import user, category, product, purchase, shopping_list
Base.metadata.create_all(bind=engine)
print('Tablas creadas OK en Neon')
"
```

Cuando se empiece a iterar en serio sobre el modelo de datos, esto se
reemplaza por migraciones reales de Alembic (`alembic init`, luego
`alembic revision --autogenerate` en cada cambio de modelo).

## 5. Levantar el backend

```bash
cd backend
source .venv/Scripts/activate
uvicorn app.main:app --env-file ../.env --reload --port 8000
```

`--reload` reinicia el servidor solo con cada cambio guardado.

## 6. Probar mientras se desarrolla

La forma más rápida es la documentación interactiva que trae FastAPI
de gratis:

**http://127.0.0.1:8000/docs**

- Cada endpoint se puede probar con "Try it out" sin necesitar Postman.
- Para los endpoints protegidos: primero `POST /auth/login`, copiar el
  `access_token` de la respuesta, y pegarlo en el botón "Authorize"
  (arriba a la derecha) — queda aplicado a todas las llamadas siguientes.

También sirve `curl` directo para pruebas puntuales o scripts, por
ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/auth/login -d "username=correo@ejemplo.com&password=1234"
```

## 7. Problemas ya resueltos (para no repetirlos)

### `bcrypt` sin versión fijada rompe el hash de contraseñas

`requirements.txt` originalmente tenía `passlib[bcrypt]` sin pin de
versión. `passlib` 1.7.4 (la última publicada, el proyecto está sin
mantenimiento) hace una auto-detección de backend al primer hash que
falla con `bcrypt >= 4.0` (`ValueError: password cannot be longer than
72 bytes`, lanzado desde el propio self-test interno de passlib, no
por una contraseña real de usuario). Se resolvió fijando:

```
bcrypt==3.2.2
```

Si se llega a quitar `passlib` a favor de usar `bcrypt` directo, este
pin ya no sería necesario.

### Los esquemas `*Out` con IDs como `str` rompían la respuesta

Los modelos usan `UUID(as_uuid=True)` de Postgres (SQLAlchemy los
entrega como objetos `uuid.UUID` de Python), pero los esquemas Pydantic
(`UserOut`, `ProductOut`, `PurchaseOut`) declaraban esos campos como
`id: str`. Pydantic v2 no convierte un `UUID` a `str` automáticamente
en modo `from_attributes`, así que cualquier endpoint que devolviera un
objeto (crear usuario, crear producto, registrar compra, listar) tronaba
con `ResponseValidationError` aunque el dato sí se hubiera guardado bien
en la base.

Se corrigió cambiando esos campos a `uuid.UUID` en lugar de `str` en
`app/schemas/auth.py`, `app/schemas/product.py` y `app/schemas/purchase.py`.
Pydantic serializa un `uuid.UUID` a string automáticamente en el JSON de
salida, así que el contrato de la API hacia afuera no cambia.

**Si se agrega un esquema `*Out` nuevo con un campo de ID o de llave
foránea**, usar `uuid.UUID` (no `str`) para que coincida con el tipo
real de la columna.

## 8. Puerto ocupado / servidor "zombie"

Si `uvicorn` no arranca o `curl` devuelve respuestas viejas después de
reiniciar el servidor, es probable que haya un proceso anterior todavía
escuchando en el puerto 8000 (pasa seguido si se corrió `uvicorn` en
segundo plano en una sesión de terminal distinta). Revisar y matarlo:

```bash
netstat -ano | grep ":8000" | grep LISTENING
taskkill //PID <el_pid_que_aparezca> //F
```
