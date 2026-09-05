# Modelo de datos — Mercadito

Todas las tablas ya están implementadas como modelos SQLAlchemy en
`backend/app/models/`. Este documento es la referencia de campos y el
razonamiento detrás de cada decisión, para que un agente no las
reinvente ni las simplifique sin saber por qué están así.

Los nombres exactos de columnas se pueden renombrar más adelante sin
problema (es una operación simple en Postgres); lo que si conviene NO
cambiar sin pensarlo dos veces son los tipos de dato y las relaciones
entre tablas (llaves foráneas), porque eso sí implica migrar datos.

## users

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| nombre | string | |
| email | string, único | se usa como usuario de login |
| password_hash | string | nunca se guarda la contraseña en texto plano (bcrypt) |

Solo 2 registros esperados (el usuario y su esposa) en v1.

## categories

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| nombre | string, único | ej. Mercado, Aseo, Otros |

Se dejó como tabla aparte (no un enum fijo) para poder agregar
subcategorías después (ej. Mercado → Lácteos) solo agregando un
`parent_id` opcional, sin tocar la estructura existente.

## products

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| nombre | string | nombre canónico del producto |
| categoria_id | UUID (FK → categories) | |
| unidad_default | string, opcional | ej. "paquete", "kg" |
| codigo_barras | string, único, opcional | cuando la factura lo trae |

## product_aliases

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| product_id | UUID (FK → products) | |
| alias_texto | string | variante de nombre vista en una factura |

Resuelve que el mismo producto aparezca con redacciones distintas entre
facturas de distintas fechas/tiendas. Al importar una factura nueva, se
busca primero en esta tabla antes de crear un producto duplicado.

## purchases

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| product_id | UUID (FK → products) | |
| usuario_id | UUID (FK → users) | quién registró la compra |
| fecha | date | |
| cantidad | float | default 1 |
| unidad | string, opcional | |
| precio_unitario | float, opcional | usado para la comparación de precios |
| precio_total | float | |
| tienda | string, opcional | proveedor — alimenta el desglose del dashboard |
| origen | string | `manual` \| `factura` \| `lista_compra` |

El campo `origen` existe para saber qué tan confiable/rastreable es cada
dato y para depurar si algo se ve raro más adelante.

## shopping_lists

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| usuario_id | UUID (FK → users) | quién creó la lista |
| fecha_creacion | date | |
| presupuesto | float, **opcional (nullable)** | solo referencia, NUNCA bloqueante |
| estado | string | `abierta` \| `cerrada` |

## shopping_list_items

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | |
| shopping_list_id | UUID (FK → shopping_lists) | |
| product_id | UUID (FK → products), opcional | |
| usuario_id | UUID (FK → users), opcional | quién confirmó ESTE ítem puntual — pensado para cuando varios dispositivos registren a la vez |
| cantidad_planeada | float, opcional | |
| precio_esperado | float, opcional | snapshot del último precio conocido al crear la lista |
| cantidad_confirmada | float, opcional | |
| precio_confirmado | float, opcional | |
| confirmado | boolean | default false |
| actualizado_en | timestamp | se actualiza en cada cambio — sirve para resolver conflictos ("gana el último que guardó") el día que haya multi-dispositivo |

Los ítems con `confirmado = false` en una lista ya `cerrada` son los que
alimentan la vista de "Pendientes" — no se copian a ningún lado
automáticamente, el usuario decide manualmente si los lleva a la
siguiente lista.

## Diagrama de relaciones (resumen)

```
users ──< purchases >── products ──< product_aliases
users ──< shopping_lists ──< shopping_list_items >── products
categories ──< products
```

(`──<` significa "uno a muchos")
