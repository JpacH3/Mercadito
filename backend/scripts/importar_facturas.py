"""
Importa un CSV de facturas (ver columnas esperadas mas abajo) a la base
de datos, creando productos/categorias que no existan y registrando
cada linea como una Purchase con origen="factura".

Columnas esperadas en el CSV (ver CLAUDE.md, seccion "Importacion de
facturas"):
    factura_id, fecha, tienda, item_no, producto, categoria, cantidad,
    unidad, precio_unitario, precio_total, codigo_barras

Como resuelve que producto es cual:
    1. Si la fila tiene codigo_barras Y ese codigo no es ambiguo (no
       aparece en el CSV con mas de un nombre de producto distinto),
       se busca/crea el producto por codigo_barras. Es el metodo mas
       confiable porque no depende de como quedo escrito el nombre en
       el recibo.
    2. Si no hay codigo_barras, o el codigo es ambiguo (aparece con
       nombres distintos en el propio CSV -- pasa cuando el recibo
       original tiene un error de lectura/digitacion), se ignora el
       codigo de barras y se resuelve por nombre exacto: primero contra
       product_aliases (ver services/normalizacion.py), luego contra
       Product.nombre. Si no hay match, se crea un producto nuevo SIN
       codigo_barras (para no arrastrar un codigo que no es confiable)
       y se guarda un alias con el texto exacto visto, para que la
       proxima fila con el mismo texto (en este u otro import) matchee
       directo.

Uso:
    python importar_facturas.py <ruta_csv> --usuario-email correo@ejemplo.com \
        [--fecha-default 2026-07-01] [--dry-run]

--fecha-default se usa solo para filas con la columna fecha vacia en
el CSV (facturas viejas donde no se conserva la fecha exacta).
--dry-run corre todo el proceso sin hacer commit, solo para revisar el
resumen antes de escribir en la base real.
"""
import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
load_dotenv(_BACKEND_DIR.parent / ".env")

from app.database import SessionLocal  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.product import Product, ProductAlias  # noqa: E402
from app.models.purchase import Purchase  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.normalizacion import resolver_producto_por_texto  # noqa: E402


def parsear_fecha(valor: str, fecha_default) -> "datetime.date":
    valor = (valor or "").strip()
    if not valor:
        return fecha_default
    return datetime.strptime(valor, "%d/%m/%Y").date()


def detectar_codigos_ambiguos(filas: list[dict]) -> set[str]:
    """Codigos de barras que en el propio CSV aparecen con mas de un
    nombre de producto distinto -- senal de error en el recibo original,
    no de que sean el mismo producto."""
    nombres_por_codigo = defaultdict(set)
    for fila in filas:
        codigo = (fila["codigo_barras"] or "").strip()
        if codigo:
            nombres_por_codigo[codigo].add(fila["producto"].strip())

    return {codigo for codigo, nombres in nombres_por_codigo.items() if len(nombres) > 1}


def obtener_o_crear_categoria(db, cache: dict, nombre: str) -> Category:
    nombre = nombre.strip()
    if nombre in cache:
        return cache[nombre]

    categoria = db.query(Category).filter(Category.nombre == nombre).first()
    if not categoria:
        categoria = Category(nombre=nombre)
        db.add(categoria)
        db.flush()

    cache[nombre] = categoria
    return categoria


def obtener_o_crear_producto(db, cache: dict, fila: dict, codigos_ambiguos: set[str], categoria: Category) -> Product:
    nombre = fila["producto"].strip()
    codigo = (fila["codigo_barras"] or "").strip()
    usar_codigo = bool(codigo) and codigo not in codigos_ambiguos

    clave_cache = codigo if usar_codigo else f"nombre:{nombre.lower()}"
    if clave_cache in cache:
        return cache[clave_cache]

    producto = None
    if usar_codigo:
        producto = db.query(Product).filter(Product.codigo_barras == codigo).first()
    else:
        producto = resolver_producto_por_texto(db, nombre)
        if not producto:
            producto = db.query(Product).filter(Product.nombre == nombre).first()

    if not producto:
        producto = Product(
            nombre=nombre,
            categoria_id=categoria.id,
            unidad_default=fila["unidad"].strip() or None,
            codigo_barras=codigo if usar_codigo else None,
        )
        db.add(producto)
        db.flush()

        if not usar_codigo:
            db.add(ProductAlias(product_id=producto.id, alias_texto=nombre))

    cache[clave_cache] = producto
    return producto


def importar(ruta_csv: Path, usuario_email: str, fecha_default, dry_run: bool):
    db = SessionLocal()

    usuario = db.query(User).filter(User.email == usuario_email).first()
    if not usuario:
        print(f"No existe ningun usuario con el correo {usuario_email}")
        sys.exit(1)

    with open(ruta_csv, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    codigos_ambiguos = detectar_codigos_ambiguos(filas)
    if codigos_ambiguos:
        print("Codigos de barras ambiguos en el CSV (se ignoran, se resuelve por nombre):")
        for codigo in codigos_ambiguos:
            nombres = {fila["producto"].strip() for fila in filas if fila["codigo_barras"].strip() == codigo}
            print(f"  {codigo}: {sorted(nombres)}")

    cache_categorias: dict = {}
    cache_productos: dict = {}
    compras_creadas = 0

    for fila in filas:
        categoria = obtener_o_crear_categoria(db, cache_categorias, fila["categoria"])
        producto = obtener_o_crear_producto(db, cache_productos, fila, codigos_ambiguos, categoria)

        compra = Purchase(
            product_id=producto.id,
            usuario_id=usuario.id,
            fecha=parsear_fecha(fila["fecha"], fecha_default),
            cantidad=float(fila["cantidad"]),
            unidad=fila["unidad"].strip() or None,
            precio_unitario=float(fila["precio_unitario"]) if fila["precio_unitario"].strip() else None,
            precio_total=float(fila["precio_total"]),
            tienda=fila["tienda"].strip() or None,
            origen="factura",
        )
        db.add(compra)
        compras_creadas += 1

    productos_nuevos = sum(1 for k in cache_productos if True)  # informativo, ver mensaje abajo

    if dry_run:
        db.rollback()
        print(f"[dry-run] Se habrian creado {compras_creadas} compras y hasta {len(cache_productos)} productos distintos referenciados. No se escribio nada.")
    else:
        db.commit()
        print(f"Listo: {compras_creadas} compras importadas, {len(cache_productos)} productos distintos referenciados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--usuario-email", required=True)
    parser.add_argument("--fecha-default", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(), required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    importar(args.csv_path, args.usuario_email, args.fecha_default, args.dry_run)
