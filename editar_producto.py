# editar_producto.py
import mysql.connector
from mysql.connector import Error
from registrar_movimiento import registrar_movimiento

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def editar_producto(id_producto, nombre, descripcion, cantidad, precio):
    try:
        con = mysql.connector.connect(**DB_CONFIG)
        cur = con.cursor(dictionary=True)

        # Estado actual (antes)
        cur.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
        antes = cur.fetchone()
        if antes is None:
            print(f"⚠ No se encontró el producto con ID {id_producto}.")
            con.close()
            return

        # Update
        cur.execute("""
            UPDATE productos
            SET nombre=%s, descripcion=%s, cantidad=%s, precio=%s
            WHERE id=%s
        """, (nombre, descripcion, cantidad, precio, id_producto))
        con.commit()

        # Registrar movimiento EDITAR (antes -> después)
        registrar_movimiento(
            tipo="EDITAR",
            producto_id=id_producto,
            nombre=nombre,
            cantidad_antes=antes['cantidad'],
            cantidad_despues=cantidad,
            precio_antes=float(antes['precio']),
            precio_despues=precio,
            descripcion="Edición de producto"
        )

        print(f"✅ Producto con ID {id_producto} actualizado correctamente.")
        cur.close()
        con.close()
    except Error as e:
        print(f"❌ Error al editar producto: {e}")
