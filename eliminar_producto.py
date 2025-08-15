# eliminar_producto.py
import mysql.connector
from mysql.connector import Error
from registrar_movimiento import registrar_movimiento

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def eliminar_producto(id_producto):
    try:
        con = mysql.connector.connect(**DB_CONFIG)
        cur = con.cursor(dictionary=True)

        # Traer estado actual antes de borrar
        cur.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
        antes = cur.fetchone()
        if antes is None:
            print(f"⚠ No se encontró el producto con ID {id_producto}.")
            con.close()
            return

        # Eliminar
        cur.execute("DELETE FROM productos WHERE id = %s", (id_producto,))
        con.commit()

        # Registrar movimiento ELIMINAR (después = None)
        registrar_movimiento(
            tipo="ELIMINAR",
            producto_id=id_producto,   # quedará referenciado, pero si no existiera se permite NULL por FK
            nombre=antes['nombre'],
            cantidad_antes=antes['cantidad'],
            cantidad_despues=None,
            precio_antes=float(antes['precio']),
            precio_despues=None,
            descripcion="Baja de producto"
        )

        print(f"🗑 Producto con ID {id_producto} eliminado correctamente.")
        cur.close()
        con.close()
    except Error as e:
        print(f"❌ Error al eliminar producto: {e}")
