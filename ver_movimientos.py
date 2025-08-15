# ver_movimientos.py
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def ver_movimientos(limite: int = 50):
    try:
        con = mysql.connector.connect(**DB_CONFIG)
        cur = con.cursor(dictionary=True)
        cur.execute(f"""
            SELECT id, fecha, tipo, producto_id, nombre,
                   cantidad_antes, cantidad_despues, precio_antes, precio_despues, descripcion
            FROM movimientos_inventario
            ORDER BY fecha DESC, id DESC
            LIMIT %s
        """, (limite,))
        movs = cur.fetchall()
        cur.close()
        con.close()

        if not movs:
            print("\n🕒 No hay movimientos registrados aún.")
            return

        print("\n--- Últimos movimientos ---")
        header = f"{'ID':<6}{'Fecha':<20}{'Tipo':<10}{'ProdID':<8}{'Nombre':<18}{'Cant(antes→desp)':<20}{'Precio(antes→desp)':<22}{'Desc':<20}"
        print(header)
        print("-" * len(header))
        for m in movs:
            cant = f"{str(m['cantidad_antes'])}→{str(m['cantidad_despues'])}"
            prec = f"{str(m['precio_antes'])}→{str(m['precio_despues'])}"
            print(f"{m['id']:<6}{str(m['fecha'])[:19]:<20}{m['tipo']:<10}{str(m['producto_id'] or '-'):<8}"
                  f"{(m['nombre'] or '-')[:17]:<18}{cant:<20}{prec:<22}{(m['descripcion'] or '-')[:19]:<20}")

    except Error as e:
        print(f"❌ Error al ver movimientos: {e}")
