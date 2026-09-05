# Mercadito (La Despensa) — Contexto del proyecto

Este documento resume todo lo planeado para este proyecto antes de escribir
código. Está pensado para dárselo a un asistente de IA (Claude Code, Copilot,
Cursor, etc.) como contexto de arranque. Si tu agente es Claude Code,
puedes renombrar este archivo a `CLAUDE.md` en la raíz del repo y lo carga
automáticamente en cada sesión.

## Qué es

App casera de control de mercado del hogar para dos usuarios (el dueño del
proyecto y su esposa). Objetivos, en orden de prioridad:

1. **Controlar el gasto total** de mercado/aseo del hogar (prioridad #1).
2. Ver estadísticas: gasto por categoría, por proveedor/tienda, por mes.
3. Estimar qué se está por acabar (predicción, no inventario real).
4. Comparar precios del mismo producto entre distintos proveedores.

## Quién lo usa y cómo

- Dos usuarios con cuenta individual (usuario/contraseña), no un PIN
  compartido — así se sabe quién registró cada compra.
- **v1 es de un solo dispositivo a la vez** (uno de los dos hace el mercado
  con su celular en la mano). El soporte para que varios dispositivos
  registren compras del mismo grupo en simultáneo (tiempo real) es una
  mejora **futura**, no de esta versión — pero el modelo de datos ya está
  preparado para no tener que rediseñar nada cuando llegue ese momento
  (ver notas en `docs/MODELO_DATOS.md`).

## Stack decidido

- **Backend:** Python, FastAPI
- **Base de datos:** PostgreSQL en Neon (se evaluó Azure SQL/SQL Server por
  la experiencia previa del usuario con T-SQL, pero se decidió aprender
  Postgres — es más estándar en el ecosistema FastAPI/Python)
- **Hosting backend:** Fly.io (despliegue vía Dockerfile, el usuario ya
  tiene experiencia con Docker en su trabajo)
- **Frontend:** PWA (HTML/JS simple), instalable en el celular sin pasar
  por App Store/Play Store
- **Notificaciones (a futuro, no definido en detalle todavía):** Telegram
  bot como canal — se prefirió sobre Web Push porque no depende de que la
  PWA esté correctamente instalada en iOS. Los tipos de aviso a activar
  (reabastecimiento, presupuesto, diferencia de precios, pendientes) se
  decidirán más adelante; por ahora todo se revisa manualmente dentro de
  la app.

## Flujo clave: modo "compra en tienda"

Este es el flujo que más valor le da a la app, descríbelo bien si el
agente va a trabajar en él:

1. Antes de salir, se crea una `shopping_list` con productos planeados
   (elegidos de productos ya conocidos, cada uno trae pegado su último
   precio registrado) y, opcionalmente, un presupuesto de referencia.
2. En la tienda, se recorre la lista como checklist. Al seleccionar un
   producto se ve su último precio guardado; el usuario confirma si
   coincide o ingresa el precio nuevo, y la cantidad real comprada.
3. El total se recalcula en tiempo real a medida que se confirman
   productos.
4. **El presupuesto es SIEMPRE solo de referencia — nunca bloquea nada.**
   Si no se llena, no tiene ningún efecto en el comportamiento de la app.
   Si se llena, solo se muestra el avance ("llevas $X de $Y").
5. Si el precio de un producto difiere ≥10% respecto al último precio
   pagado en otra tienda, se muestra un aviso informativo (no bloqueante)
   en el momento de confirmar. La misma comparación existe también como
   una vista aparte en el historial.
6. Al cerrar la lista: los productos confirmados pasan a `purchases`
   (alimentando dashboard e historial). Los productos planeados pero NO
   confirmados **no se borran ni se copian a ningún lado** — quedan
   visibles en una vista de "Pendientes" y el usuario decide manualmente
   si los lleva a la próxima lista.

## Predicción de reabastecimiento

Decisión explícita: es un **estimado por frecuencia de compra**
(promedio de días entre compras del mismo producto vs. días desde la
última compra), **no inventario real**. Se decidió no implementar
registro de consumo real porque la carga de digitación diaria no vale la
pena para un hogar. Este límite debe quedar visible en la UI ("cálculo
aproximado según tu historial de compras"), no presentarse como un dato
exacto.

## Dashboard

Debe mostrar, usando los campos `categoria` y `tienda` que ya existen en
`purchases` (no requieren tablas nuevas):

- Gasto total del mes (y comparación con el mes anterior)
- Desglose por categoría
- Desglose por proveedor/tienda

## Importación de facturas

Las facturas (foto/PDF) se procesan **fuera de la app**, conversando con
Claude para extraer los datos a CSV/JSON (columnas:
`factura_id, fecha, tienda, item_no, producto, categoria, cantidad,
unidad, precio_unitario, precio_total, codigo_barras`). Ese archivo se
carga a la base de datos con un script de importación (pendiente de
escribir). El campo `origen` en `purchases` distingue si una compra vino
de una factura importada, de un registro manual o del cierre de una
`shopping_list`.

Para resolver que un mismo producto aparezca con nombres distintos entre
facturas (ej. "ACEITE DE GIR" vs "aceite girasol"), existe la tabla
`product_aliases` — ver `app/services/normalizacion.py` en el código,
que ya tiene el esqueleto de esta lógica (matching exacto implementado,
matching difuso pendiente).

## Estado actual del código

Ya existe un esqueleto funcional (no solo carpetas vacías) en el repo:

- Modelos SQLAlchemy completos para las 7 tablas (`app/models/`)
- Autenticación con usuario/contraseña funcionando (bcrypt + JWT) en
  `app/routers/auth.py`
- Lógica ya escrita (no placeholder) para:
  - `app/services/prediction.py` — cálculo de predicción de reabastecimiento
  - `app/services/price_comparison.py` — comparación de precios entre tiendas
- Endpoints básicos de productos y compras (`app/routers/products.py`,
  `app/routers/purchases.py`)
- Todo lo que falta por construir está marcado con comentarios `TODO` en
  el código mismo (ver también la sección "Lo que falta" en el `README.md`
  raíz del proyecto)

Antes de proponer una arquitectura distinta a la ya definida arriba,
o de re-decidir algo de esta lista, confirma con el usuario — todo esto
ya fue decidido deliberadamente después de evaluar alternativas.

## Detalle del modelo de datos

Ver `docs/MODELO_DATOS.md` para las tablas y campos exactos.
