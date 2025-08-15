import mysql.connector
import csv
import json
from decimal import Decimal
from datetime import date

def exportar_productos():
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="ff8wiooi",  # ← Cambia esto por tu contraseña real
        database="inventario"
    )

    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    if not productos:
        print("⚠️ No hay productos para exportar.")
        return

    # Exportar a CSV
    with open("productos.csv", "w", newline="", encoding="utf-8") as archivo_csv:
        writer = csv.DictWriter(archivo_csv, fieldnames=productos[0].keys())
        writer.writeheader()
        writer.writerows(productos)

    # Función para convertir tipos no serializables
    def convertir(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, date):
            return obj.isoformat()  # formato YYYY-MM-DD
        return obj

    # Convertir cada valor del diccionario
    productos_convertidos = [
        {k: convertir(v) for k, v in prod.items()} for prod in productos
    ]

    # Exportar a JSON
    with open("productos.json", "w", encoding="utf-8") as archivo_json:
        json.dump(productos_convertidos, archivo_json, ensure_ascii=False, indent=4)

    print("✅ Productos exportados a 'productos.csv' y 'productos.json'")

    cursor.close()
    conexion.close()
