# predecir_demanda.py
import mysql.connector
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ff8wiooi",
    "database": "inventario"
}

def obtener_datos_historicos(producto_id=None):
    """Obtiene datos históricos con validación mejorada"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        where_clause = "WHERE m.tipo = 'SALIDA'"
        params = []
        
        if producto_id:
            where_clause += " AND m.producto_id = %s"
            params.append(producto_id)
        
        query = f"""
        SELECT 
            m.fecha,
            p.nombre as producto,
            p.id as producto_id,
            DAYOFWEEK(m.fecha) as dia_semana,
            (m.cantidad_antes - m.cantidad_despues) as ventas,
            p.precio
        FROM movimientos_inventario m
        JOIN productos p ON m.producto_id = p.id
        {where_clause}
        ORDER BY m.fecha
        """
        
        datos = pd.read_sql(query, conn, params=params if params else None)
        
        if datos.empty:  # Usamos .empty en lugar de verificación booleana
            print("⚠️ No se encontraron datos de ventas")
            return None
            
        datos['fecha'] = pd.to_datetime(datos['fecha'])
        datos['dias'] = (datos['fecha'] - datos['fecha'].min()).dt.days
        datos['mes'] = datos['fecha'].dt.month
        datos['dia_mes'] = datos['fecha'].dt.day
        datos['semana_ano'] = datos['fecha'].dt.isocalendar().week
        datos['fin_de_semana'] = datos['dia_semana'].isin([6, 7]).astype(int)
        
        return datos
        
    except Error as e:
        print(f"❌ Error al obtener datos: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def entrenar_modelo(datos, producto_nombre):
    """Entrena el modelo con validación mejorada"""
    if datos is None or datos.empty or len(datos) < 20:  # Corregido: usa datos.empty
        count = 0 if datos is None or datos.empty else len(datos)
        print(f"⚠️ {producto_nombre}: Datos insuficientes ({count} registros)")
        return None
    
    try:
        X = datos[['dias', 'dia_semana', 'mes', 'fin_de_semana']]
        y = datos['ventas']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        modelo = RandomForestRegressor(
            n_estimators=200,
            max_depth=7,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        modelo.fit(X_train, y_train)
        
        y_pred = modelo.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = modelo.score(X_test, y_test)
        
        cv_scores = cross_val_score(modelo, X, y, cv=5, scoring='neg_mean_absolute_error')
        
        print(f"\n📊 Evaluación para {producto_nombre}:")
        print(f"- Precisión (R²): {r2:.2%}")
        print(f"- Error absoluto medio (MAE): {mae:.2f} unidades")
        print(f"- MAE Validación Cruzada: {-cv_scores.mean():.2f} (±{cv_scores.std():.2f})")
        
        return modelo
        
    except Exception as e:
        print(f"❌ Error al entrenar modelo: {e}")
        return None

def generar_prediccion(modelo, producto, ultima_fecha, datos):
    """Genera predicción con manejo de errores mejorado"""
    try:
        dias_futuros = []
        fechas = []
        hoy = datetime.now().date()
        
        for i in range(1, 8):
            fecha = hoy + timedelta(days=i)
            dia_semana = fecha.weekday() + 1
            mes = fecha.month
            fin_de_semana = 1 if dia_semana in [6, 7] else 0
            dias = (ultima_fecha - datos['fecha'].min()).days + i + 1
            
            dias_futuros.append([dias, dia_semana, mes, fin_de_semana])
            fechas.append(fecha)
        
        predicciones = modelo.predict(np.array(dias_futuros))
        predicciones = [max(0, round(pred)) for pred in predicciones]
        
        return fechas, predicciones
        
    except Exception as e:
        print(f"❌ Error al generar predicción: {e}")
        return None, None

def mostrar_resultados(producto, fechas, predicciones):
    """Muestra resultados con gráficos mejorados"""
    try:
        if not fechas or not predicciones:
            print("❌ No hay datos para mostrar")
            return
        
        print(f"\n📈 Predicción de demanda para {producto}:")
        for fecha, pred in zip(fechas, predicciones):
            print(f"  {fecha.strftime('%a %d/%m')}: {pred} unidades")
        
        plt.figure(figsize=(12, 6))
        
        # Gráfico de barras
        plt.subplot(1, 2, 1)
        plt.bar([d.strftime('%a') for d in fechas], predicciones, color='skyblue')
        plt.title('Predicción próxima semana')
        plt.xlabel('Día')
        plt.ylabel('Unidades vendidas')
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Gráfico de línea
        plt.subplot(1, 2, 2)
        plt.plot(predicciones, 'o-', color='green')
        plt.xticks(range(7), [d.strftime('%a') for d in fechas])
        plt.title('Tendencia de demanda')
        plt.grid(True)
        
        plt.suptitle(f'Producto: {producto}')
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"❌ Error al mostrar gráficos: {e}")

def predecir_demanda(producto_id=None):
    """Función principal corregida"""
    print("\n🔮 INICIANDO PREDICCIÓN DE DEMANDA")
    
    datos = obtener_datos_historicos(producto_id)
    if datos is None or datos.empty:
        print("❌ No hay datos suficientes para realizar la predicción")
        return
    
    productos = datos['producto'].unique()
    
    for producto in productos:
        datos_producto = datos[datos['producto'] == producto]
        ultima_fecha = datos_producto['fecha'].max()
        
        print(f"\n📊 Procesando: {producto} ({len(datos_producto)} registros)...")
        
        modelo = entrenar_modelo(datos_producto, producto)
        if modelo is None:
            continue
        
        fechas, predicciones = generar_prediccion(modelo, producto, ultima_fecha, datos_producto)
        if predicciones:
            mostrar_resultados(producto, fechas, predicciones)

if __name__ == "__main__":
    predecir_demanda()