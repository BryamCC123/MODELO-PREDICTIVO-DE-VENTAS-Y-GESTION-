# registrar_movimiento.py
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def registrar_movimiento(
    tipo: str,
    producto_id: int | None,
    nombre: str | None,
    cantidad_antes: int | None,
    cantidad_despues: int | None,
    precio_antes: float | None,
    precio_despues: float | None,
    descripcion: str | None = None,
):
    """
    tipo: 'CREAR' | 'EDITAR' | 'ELIMINAR' | 'ENTRADA' | 'SALIDA' | 'AJUSTE'
    producto_id puede ser None si el producto ya no existe (deleted)
    """
    try:
        con = mysql.connector.connect(**DB_CONFIG)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO movimientos_inventario
            (tipo, producto_id, nombre, cantidad_antes, cantidad_despues, precio_antes, precio_despues, descripcion)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (tipo, producto_id, nombre, cantidad_antes, cantidad_despues, precio_antes, precio_despues, descripcion))
        con.commit()
        cur.close()
        con.close()
    except Error as e:
        print(f"❌ Error al registrar movimiento: {e}")
