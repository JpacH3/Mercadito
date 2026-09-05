# Migraciones con Alembic

Esta carpeta esta vacia a proposito. Cuando vayas a empezar a programar:

```
cd backend
alembic init alembic
```

Esto genera `alembic.ini` y la estructura real de migraciones.
Configura `sqlalchemy.url` en `alembic.ini` para que apunte a tu
`DATABASE_URL` de Neon (o mejor, que lo lea desde la variable de entorno
en `alembic/env.py`, para no dejar la cadena de conexion escrita ahi).

Luego, cada vez que cambies un modelo en `app/models/`:

```
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```
