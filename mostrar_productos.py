import mysql.connector
from mysql.connector import Error

def mostrar_productos():
    try:
        # 1. Establecer conexión
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="ff8wiooi",
            database="inventario"
        )
        
        # 2. Crear cursor con resultados como diccionario
        cursor = conexion.cursor(dictionary=True)
        
        # 3. Ejecutar consulta
        cursor.execute("SELECT id, nombre, descripcion, cantidad, precio FROM productos")
        productos = cursor.fetchall()

        # 4. Mostrar resultados
        if not productos:
            print("\n📦 No hay productos registrados en el inventario.")
            return
            
        print("\n=== LISTA DE PRODUCTOS ===")
        print(f"{'ID':<5}{'Nombre':<20}{'Descripción':<30}{'Stock':<10}{'Precio':<10}")
        print("-" * 80)
        
        for p in productos:
            print(f"{p['id']:<5}"
                  f"{p['nombre']:<20}"
                  f"{p.get('descripcion', '')[:25]:<30}"  # Muestra solo primeros 25 caracteres
                  f"{p['cantidad']:<10}"
                  f"${p['precio']:.2f}")

    except Error as e:
        print(f"\n❌ Error al acceder a la base de datos: {e}")
    finally:
        # 5. Cerrar conexión siempre
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

# Para probar directamente
if __name__ == "__main__":
    mostrar_productos()