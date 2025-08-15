# menu.py
import mysql.connector
from mysql.connector import Error
from insertar_producto import insertar_producto
from editar_producto import editar_producto
from eliminar_producto import eliminar_producto
from exportar_productos import exportar_productos
from movimientos import ver_movimientos, registrar_entrada, registrar_salida, verificar_integridad_datos
from predecir_demanda import predecir_demanda

# Configuración base sin database para evitar el error de duplicado
DB_CONFIG_BASE = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi"
}

DATABASE_NAME = "inventario"

def obtener_conexion():
    """Obtiene una conexión a la base de datos específica"""
    config = DB_CONFIG_BASE.copy()
    config["database"] = DATABASE_NAME
    return mysql.connector.connect(**config)

def inicializar_bd():
    """Función mejorada para inicializar la base de datos"""
    try:
        # Conexión inicial sin base de datos
        conexion = mysql.connector.connect(**DB_CONFIG_BASE)
        cursor = conexion.cursor()
        
        # Crear base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {DATABASE_NAME}")

        # Tabla productos con más restricciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            descripcion TEXT,
            cantidad INT NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
            precio DECIMAL(10,2) NOT NULL CHECK (precio > 0),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)

        # Tabla movimientos con más restricciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo ENUM('CREAR','EDITAR','ELIMINAR','ENTRADA','SALIDA','AJUSTE') NOT NULL,
            producto_id INT NULL,
            nombre VARCHAR(100),
            cantidad_antes INT NULL CHECK (cantidad_antes >= 0),
            cantidad_despues INT NULL CHECK (cantidad_despues >= 0),
            precio_antes DECIMAL(10,2) NULL,
            precio_despues DECIMAL(10,2) NULL,
            descripcion TEXT NULL,
            CONSTRAINT fk_mov_prod FOREIGN KEY (producto_id) 
                REFERENCES productos(id) ON DELETE SET NULL,
            INDEX idx_fecha (fecha),
            INDEX idx_producto (producto_id)
        ) ENGINE=InnoDB
        """)

        conexion.commit()
        print("✅ Base de datos y tablas inicializadas correctamente")
        
    except Error as e:
        print(f"❌ Error al inicializar BD: {e}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def mostrar_productos():
    """Función mejorada para mostrar productos"""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
        SELECT p.id, p.nombre, p.descripcion, p.cantidad, p.precio, 
               COUNT(m.id) as total_movimientos
        FROM productos p
        LEFT JOIN movimientos_inventario m ON p.id = m.producto_id
        GROUP BY p.id
        ORDER BY p.nombre
        """)
        
        productos = cursor.fetchall()

        if not productos:
            print("\n📦 No hay productos en el inventario.")
            return

        print("\n📋 LISTA DE PRODUCTOS")
        print("-" * 90)
        print(f"{'ID':<5}{'Nombre':<20}{'Descripción':<25}{'Stock':<8}{'Precio':<10}{'Movimientos'}")
        print("-" * 90)
        
        for p in productos:
            descripcion = (p['descripcion'] or '')[:25] + ('...' if len(p['descripcion'] or '') > 25 else '')
            print(f"{p['id']:<5}"
                  f"{p['nombre']:<20}"
                  f"{descripcion:<25}"
                  f"{p['cantidad']:<8}"
                  f"${p['precio']:<9.2f}"
                  f"{p['total_movimientos']}")
        
    except Error as e:
        print(f"❌ Error al mostrar productos: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

def menu():
    """Menú principal mejorado"""
    inicializar_bd()

    while True:
        print("\n" + "=" * 50)
        print(" SISTEMA DE INVENTARIO Y PREDICCIÓN DE DEMANDA ".center(50))
        print("=" * 50)
        print("\n--- GESTIÓN DE PRODUCTOS ---")
        print("1. Insertar producto")
        print("2. Editar producto")
        print("3. Eliminar producto")
        print("4. Ver productos")
        print("5. Exportar productos (CSV y JSON)")
        
        print("\n--- MOVIMIENTOS ---")
        print("6. Ver movimientos (historial)")
        print("7. Predecir demanda")
        print("8. Registrar entrada")
        print("9. Registrar salida")
        
        print("\n--- SISTEMA ---")
        print("10. Verificar integridad de datos")
        print("11. Salir")

        opcion = input("\nSeleccione una opción: ").strip()

        try:
            if opcion == "1":
                print("\n📥 INSERTAR NUEVO PRODUCTO")
                nombre = input("Nombre: ").strip()
                descripcion = input("Descripción: ").strip()
                cantidad = int(input("Cantidad inicial: ").strip())
                precio = float(input("Precio unitario: ").strip())
                insertar_producto(nombre, descripcion, cantidad, precio)

            elif opcion == "2":
                print("\n✏️ EDITAR PRODUCTO")
                mostrar_productos()
                id_producto = int(input("\nID del producto a editar: ").strip())
                nombre = input("Nuevo nombre (dejar vacío para no cambiar): ").strip() or None
                descripcion = input("Nueva descripción (dejar vacío para no cambiar): ").strip() or None
                cantidad = input("Nueva cantidad (dejar vacío para no cambiar): ").strip()
                cantidad = int(cantidad) if cantidad else None
                precio = input("Nuevo precio (dejar vacío para no cambiar): ").strip()
                precio = float(precio) if precio else None
                editar_producto(id_producto, nombre, descripcion, cantidad, precio)

            elif opcion == "3":
                print("\n❌ ELIMINAR PRODUCTO")
                mostrar_productos()
                id_producto = int(input("\nID del producto a eliminar: ").strip())
                confirmar = input(f"¿Está seguro de eliminar este producto? (s/n): ").lower()
                if confirmar == 's':
                    eliminar_producto(id_producto)

            elif opcion == "4":
                mostrar_productos()

            elif opcion == "5":
                exportar_productos()

            elif opcion == "6":
                print("\n🔄 HISTORIAL DE MOVIMIENTOS")
                try:
                    limite = int(input("¿Cuántos registros mostrar? (50): ").strip() or "50")
                    filtro = input("¿Filtrar por ID de producto? (dejar vacío para todos): ").strip()
                    producto_id = int(filtro) if filtro else None
                    ver_movimientos(limite, producto_id)
                except ValueError:
                    print("❌ Error: Debe ingresar un número válido")

            elif opcion == "7":
                print("\n🔮 PREDICCIÓN DE DEMANDA")
                mostrar_productos()
                filtro = input("\n¿Predecir para un producto específico? (ingrese ID o dejar vacío para todos): ").strip()
                producto_id = int(filtro) if filtro else None
                predecir_demanda(producto_id)

            elif opcion == "8":
                print("\n📥 REGISTRAR ENTRADA")
                mostrar_productos()
                producto_id = int(input("\nID del producto: ").strip())
                cantidad = int(input("Cantidad a ingresar: ").strip())
                motivo = input("Motivo (opcional): ").strip()
                registrar_entrada(producto_id, cantidad, motivo)

            elif opcion == "9":
                print("\n📤 REGISTRAR SALIDA")
                mostrar_productos()
                producto_id = int(input("\nID del producto: ").strip())
                cantidad = int(input("Cantidad a retirar: ").strip())
                motivo = input("Motivo (opcional): ").strip()
                registrar_salida(producto_id, cantidad, motivo)

            elif opcion == "10":
                verificar_integridad_datos()

            elif opcion == "11":
                print("\n👋 Saliendo del sistema...")
                break

            else:
                print("⚠️ Opción no válida. Intente nuevamente.")

        except ValueError as ve:
            print(f"❌ Error: Entrada inválida - {ve}")
        except Error as e:
            print(f"❌ Error de base de datos: {e}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    menu()