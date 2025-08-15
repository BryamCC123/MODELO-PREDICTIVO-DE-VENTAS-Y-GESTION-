# movimientos.py
import mysql.connector
from datetime import datetime
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def producto_existe(producto_id):
    """Verifica si un producto existe en la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos WHERE id = %s", (producto_id,))
        return cursor.fetchone()[0] > 0
    except Error as e:
        print(f"❌ Error al verificar producto: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def registrar_entrada(producto_id, cantidad, motivo=""):
    """Registra una entrada de producto al inventario con validaciones mejoradas"""
    if not producto_existe(producto_id):
        print("❌ Error: El producto no existe")
        return False
    
    if cantidad <= 0:
        print("❌ Error: La cantidad debe ser positiva")
        return False
        
    return _gestionar_movimiento('ENTRADA', producto_id, cantidad, motivo)

def registrar_salida(producto_id, cantidad, motivo=""):
    """Registra una salida de producto del inventario con validaciones mejoradas"""
    if not producto_existe(producto_id):
        print("❌ Error: El producto no existe")
        return False
    
    if cantidad <= 0:
        print("❌ Error: La cantidad debe ser positiva")
        return False
        
    return _gestionar_movimiento('SALIDA', producto_id, cantidad, motivo)

def _gestionar_movimiento(tipo, producto_id, cantidad, descripcion):
    """Función interna mejorada para gestionar movimientos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Obtener información completa del producto
        cursor.execute("SELECT cantidad, nombre FROM productos WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        
        if not producto:
            print("❌ Error: Producto no encontrado")
            return False
            
        stock_actual = producto['cantidad']
        nombre_producto = producto['nombre']
        
        # Calcular nuevo stock con validación
        if tipo == 'ENTRADA':
            nuevo_stock = stock_actual + cantidad
        else:  # SALIDA
            nuevo_stock = stock_actual - cantidad
            if nuevo_stock < 0:
                print(f"❌ Error: Stock insuficiente de {nombre_producto} (disponible: {stock_actual})")
                return False
        
        # Registrar movimiento con más detalles
        cursor.execute("""
        INSERT INTO movimientos_inventario 
        (fecha, tipo, producto_id, cantidad_antes, cantidad_despues, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (datetime.now(), tipo, producto_id, stock_actual, nuevo_stock, descripcion))
        
        # Actualizar producto
        cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nuevo_stock, producto_id))
        
        conn.commit()
        print(f"✅ {tipo} registrada para {nombre_producto}. Stock actual: {nuevo_stock}")
        return True
        
    except Error as e:
        print(f"❌ Error al registrar movimiento: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def ver_movimientos(limite=50, producto_id=None):
    """Muestra el historial de movimientos con filtros mejorados"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT m.id, m.fecha, m.tipo, p.nombre, 
               m.cantidad_antes, m.cantidad_despues, m.descripcion
        FROM movimientos_inventario m
        LEFT JOIN productos p ON m.producto_id = p.id
        """
        
        params = []
        
        if producto_id:
            query += " WHERE m.producto_id = %s"
            params.append(producto_id)
            
        query += " ORDER BY m.fecha DESC LIMIT %s"
        params.append(limite)
        
        cursor.execute(query, params)
        movimientos = cursor.fetchall()
        
        if not movimientos:
            print("ℹ️ No se encontraron movimientos")
            return
        
        print("\n🔄 HISTORIAL DE MOVIMIENTOS")
        print("-" * 100)
        print(f"{'ID':<5}{'Fecha':<20}{'Tipo':<10}{'Producto':<20}{'Antes':<10}{'Despues':<10}{'Cambio':<10}{'Descripción'}")
        print("-" * 100)
        
        for mov in movimientos:
            cambio = mov['cantidad_despues'] - mov['cantidad_antes']
            print(f"{mov['id']:<5}"
                  f"{mov['fecha'].strftime('%Y-%m-%d %H:%M'):<20}"
                  f"{mov['tipo']:<10}"
                  f"{mov['nombre'] or 'N/A':<20}"
                  f"{mov['cantidad_antes']:<10}"
                  f"{mov['cantidad_despues']:<10}"
                  f"{cambio:>+5}{'':<5}"
                  f"{mov['descripcion'] or ''}")
        
    except Error as e:
        print(f"❌ Error al obtener movimientos: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def verificar_integridad_datos():
    """Verifica la integridad de los datos para el modelo predictivo"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 1. Verificar movimientos sin producto
        cursor.execute("""
        SELECT COUNT(*) as problemas
        FROM movimientos_inventario
        WHERE producto_id IS NULL OR producto_id NOT IN (SELECT id FROM productos)
        """)
        resultado = cursor.fetchone()
        print(f"\n🔍 Verificación de integridad de datos:")
        print(f"Movimientos sin producto válido: {resultado['problemas']}")
        
        # 2. Verificar inconsistencias en cantidades
        cursor.execute("""
        SELECT COUNT(*) as problemas
        FROM movimientos_inventario
        WHERE cantidad_antes < 0 OR cantidad_despues < 0 
        OR (tipo = 'SALIDA' AND cantidad_antes <= cantidad_despues)
        OR (tipo = 'ENTRADA' AND cantidad_antes >= cantidad_despues)
        """)
        resultado = cursor.fetchone()
        print(f"Inconsistencias en cantidades: {resultado['problemas']}")
        
        # 3. Verificar productos con pocas salidas
        cursor.execute("""
        SELECT p.nombre, COUNT(m.id) as total_salidas
        FROM productos p
        LEFT JOIN movimientos_inventario m ON p.id = m.producto_id AND m.tipo = 'SALIDA'
        GROUP BY p.id
        HAVING total_salidas < 20
        """)
        productos_con_pocos_datos = cursor.fetchall()
        
        if productos_con_pocos_datos:
            print("\n⚠️ Productos con menos de 20 salidas (pueden afectar predicciones):")
            for producto in productos_con_pocos_datos:
                print(f"- {producto['nombre']}: {producto['total_salidas']} salidas")
        else:
            print("\n✅ Todos los productos tienen suficientes datos para predicciones")
            
    except Error as e:
        print(f"❌ Error al verificar integridad: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()