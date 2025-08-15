# insertar_producto.py
import mysql.connector
from mysql.connector import Error
from registrar_movimiento import registrar_movimiento

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def insertar_producto(nombre, descripcion, cantidad, precio):
    try:
        con = mysql.connector.connect(**DB_CONFIG)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, descripcion, cantidad, precio)
            VALUES (%s, %s, %s, %s)
        """, (nombre, descripcion, cantidad, precio))
        con.commit()
        producto_id = cur.lastrowid

        # Registrar movimiento CREAR
        registrar_movimiento(
            tipo="CREAR",
            producto_id=producto_id,
            nombre=nombre,
            cantidad_antes=None,
            cantidad_despues=cantidad,
            precio_antes=None,
            precio_despues=precio,
            descripcion="Alta de producto"
        )

        print(f"✅ Producto '{nombre}' agregado correctamente (ID {producto_id}).")
        cur.close()
        con.close()
    except Error as e:
        print(f"❌ Error al insertar producto: {e}")
