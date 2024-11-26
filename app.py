import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Ruta relativa para cargar los archivos CSV
ventas_df = pd.read_csv('ventas.csv')
compras_df = pd.read_csv('inventario_peps.csv')

# Archivo para datos del inventario
INVENTARIO_FILE = "inventario_peps.csv"

# Función para cargar el inventario
def cargar_inventario():
    if os.path.exists(INVENTARIO_FILE):
        df = pd.read_csv(INVENTARIO_FILE)
        # Asegurar que las columnas requeridas existan
        if 'Producto' not in df.columns:
            df['Producto'] = None
        if 'Litros Iniciales' not in df.columns:
            df['Litros Iniciales'] = df['Cantidad Disponible']
        return df
    else:
        return pd.DataFrame(columns=['Fecha', 'Costo Unitario', 'Cantidad Disponible', 'Litros Iniciales', 'Producto'])

# Función para guardar el inventario
def guardar_inventario(df):
    df.to_csv(INVENTARIO_FILE, index=False)

# Archivo para datos de las ventas
VENTAS_FILE = "ventas.csv"

# Función para cargar las ventas
def cargar_ventas():
    if os.path.exists(VENTAS_FILE):
        return pd.read_csv(VENTAS_FILE)
    else:
        return pd.DataFrame(columns=["Fecha", "Producto", "Cantidad Vendida", "Precio por Litro"])

# Función para guardar una nueva venta
def guardar_venta(fecha, producto, cantidad, precio):
    nueva_venta = pd.DataFrame([{
        "Fecha": fecha,
        "Producto": producto,
        "Cantidad Vendida": cantidad,
        "Precio por Litro": precio
    }])
    if os.path.exists(VENTAS_FILE):
        ventas = pd.read_csv(VENTAS_FILE)
        ventas = pd.concat([ventas, nueva_venta], ignore_index=True)
    else:
        ventas = nueva_venta
    ventas.to_csv(VENTAS_FILE, index=False)

# Inicializar valores en session_state
if "cantidad" not in st.session_state:
    st.session_state.cantidad = 0.0
if "costo_compra" not in st.session_state:
    st.session_state.costo_compra = 0.0
if "precio_venta" not in st.session_state:
    st.session_state.precio_venta = 0.0

# Cargar datos iniciales
inventario = cargar_inventario()

# Eliminar capas agotadas
inventario = inventario[inventario['Cantidad Disponible'] > 0]
guardar_inventario(inventario)

# Diseño del encabezado con logo
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<h1 style='color: green;'>Módulo de Inventario</h1>", unsafe_allow_html=True)
with col2:
    st.image("Logo_Gas.png", use_column_width=True)

# Sidebar para la navegación
st.sidebar.title("Módulos")
opcion = st.sidebar.radio("Selecciona una opción", ["Registro Diario", "Resumen de Inventario", "Ventas"])

# Registro Diario
if opcion == "Registro Diario":
    st.markdown("<h2 style='color: black;'>Registro Diario</h2>", unsafe_allow_html=True)
    fecha = st.date_input("Fecha", value=pd.Timestamp.now())
    tipo_operacion = st.selectbox("Tipo de operación", ["Compra", "Venta", "Merma"])
    producto = st.selectbox("Producto", ["Magna", "Premium", "Diesel"])
    cantidad = st.number_input("Cantidad (Litros)", step=0.1, value=st.session_state.cantidad)

    if tipo_operacion == "Compra":
        costo_compra = st.number_input("Costo de Compra (por Litro)", min_value=0.0, step=0.01, value=st.session_state.costo_compra)
    
    elif tipo_operacion == "Venta":
        precio_venta = st.number_input("Precio de Venta (por Litro)", min_value=0.0, step=0.01, value=st.session_state.precio_venta)
    else:
        precio_venta = 0.0
        costo_compra = 0.0

    if st.button("Guardar Registro"):
        if tipo_operacion == "Compra":
            if costo_compra == 0 or cantidad <= 0:
                st.error("Debe ingresar un costo válido y una cantidad mayor a 0 para la compra.")
            else:
                nuevo_registro = pd.DataFrame([{
                    'Fecha': fecha,
                    'Producto': producto,
                    'Costo Unitario': costo_compra,
                    'Cantidad Disponible': cantidad,
                    'Litros Iniciales': cantidad
                }])
                inventario = pd.concat([inventario, nuevo_registro], ignore_index=True)
                guardar_inventario(inventario)
                st.success("Compra registrada exitosamente.")

        elif tipo_operacion == "Venta":
            disponible = inventario[inventario['Producto'] == producto]['Cantidad Disponible'].sum()
            if cantidad > disponible or cantidad <= 0:
                st.error("La cantidad ingresada no es válida o excede el inventario disponible.")
            else:
                # Guardar la cantidad original antes de modificarla
                cantidad_original = cantidad

                # Reducir inventario
                for i, row in inventario[inventario['Producto'] == producto].iterrows():
                    if cantidad <= 0:
                        break
                    consumir = min(cantidad, row['Cantidad Disponible'])
                    inventario.at[i, 'Cantidad Disponible'] -= consumir
                    cantidad -= consumir
                guardar_inventario(inventario)

                # Guardar venta en archivo de ventas con la cantidad original
                guardar_venta(fecha, producto, cantidad_original, precio_venta)
                st.success("Venta registrada exitosamente y guardada en el historial.")

# Función para mostrar el resumen total del inventario
def mostrar_resumen_total(inventario):
    st.markdown("<h2 style='color: black;'>Resumen Total</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    for producto, col in zip(["Magna", "Premium", "Diesel"], [col1, col2, col3]):
        total_litros = inventario[inventario['Producto'] == producto]['Cantidad Disponible'].sum()
        promedio_costo = inventario[inventario['Producto'] == producto]['Costo Unitario'].mean()
        col.metric(f"Litros de {producto}", f"{total_litros:.1f} L", f"${promedio_costo:.2f}/L")

# Función para mostrar capas más antiguas
def mostrar_capas_estilizadas(producto, inventario):
    capas_producto = inventario[inventario['Producto'] == producto].sort_values(by='Fecha')
    colores = {'Magna': '#28a745', 'Premium': '#dc3545', 'Diesel': '#6c757d'}
    color = colores.get(producto, '#007bff')

    # Encabezado en negro
    st.markdown(f"<h3 style='color: black;'>{producto}</h3>", unsafe_allow_html=True)

    if not capas_producto.empty:
        capa_antigua = capas_producto.iloc[0]  # Solo mostramos la capa más antigua
        cantidad_disponible = capa_antigua['Cantidad Disponible']
        litros_iniciales = capa_antigua['Litros Iniciales']
        costo_unitario = capa_antigua['Costo Unitario']
        porcentaje = (cantidad_disponible / litros_iniciales) * 100 if litros_iniciales > 0 else 0

        # Generar barra con información dinámica y color personalizado
        st.markdown(
            f"""
            <div style="background-color: #f1f1f1; border-radius: 10px; padding: 10px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-size: 16px; font-weight: bold; color: {color};">
                        Costo: ${costo_unitario:.2f}
                    </span>
                    <span style="font-size: 16px; font-weight: bold; color: {color};">
                        {porcentaje:.1f}% ({cantidad_disponible:.1f} L disponibles)
                    </span>
                </div>
                <div style="background-color: #e9ecef; border-radius: 5px; height: 15px; overflow: hidden; margin-top: 5px;">
                    <div style="width: {porcentaje}%; background-color: {color}; height: 100%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.write(f"No hay inventario disponible para {producto}.")

# Resumen de Inventario
def mostrar_compras_por_producto(inventario):
    st.markdown("<h2 style='color: black;'>Compras por Producto</h2>", unsafe_allow_html=True)
    producto_seleccionado = st.radio("Selecciona un Producto:", ["Magna", "Premium", "Diesel"], horizontal=True)

    compras_producto = inventario[inventario['Producto'] == producto_seleccionado].sort_values(by='Fecha', ascending=False)

    if compras_producto.empty:
        st.write(f"No hay compras registradas para {producto_seleccionado}.")
    else:
        st.markdown(f"<h3 style='color: black;'>Compras - {producto_seleccionado}</h3>", unsafe_allow_html=True)
        for _, row in compras_producto.iterrows():
            fecha = row['Fecha']
            litros = row['Cantidad Disponible']
            costo_unitario = row['Costo Unitario']

            # Tarjeta de compra
            st.markdown(
                f"""
                <div style="border: 1px solid #e1e1e1; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: #f9f9f9;">
                    <p style="margin: 5px 0;"><b>Fecha:</b> {fecha}</p>
                    <p style="margin: 5px 0;"><b>Litros Comprados:</b> {litros:.1f} L</p>
                    <p style="margin: 5px 0;"><b>Costo Unitario:</b> ${costo_unitario:.2f}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# Agregar al final del resumen de inventario
if opcion == "Resumen de Inventario":
    mostrar_resumen_total(inventario)

    # Mostrar capas más antiguas
    for producto in ["Magna", "Premium", "Diesel"]:
        mostrar_capas_estilizadas(producto, inventario)

    # Mostrar compras por producto
    mostrar_compras_por_producto(inventario)

# Módulo de Ventas
if opcion == "Ventas":

    # Cargar las ventas
    ventas = cargar_ventas()

    if not ventas.empty:
        # Filtros Interactivos
        st.markdown("<h2 style='color: black;'>Historial y Análisis de Ventas</h2>", unsafe_allow_html=True)
        with st.expander("Aplicar filtros"):
            col1, col2 = st.columns(2)
            with col1:
                fecha_inicio = st.date_input("Fecha de inicio", value=pd.Timestamp(ventas['Fecha'].min()))
            with col2:
                fecha_fin = st.date_input("Fecha de fin", value=pd.Timestamp(ventas['Fecha'].max()))
            
            producto_filtrado = st.multiselect(
                "Selecciona Producto(s)", 
                ["Magna", "Premium", "Diesel"], 
                default=["Magna", "Premium", "Diesel"]
            )

        # Filtrar datos
        ventas['Fecha'] = pd.to_datetime(ventas['Fecha'])
        ventas_filtradas = ventas[
            (ventas['Fecha'] >= pd.to_datetime(fecha_inicio)) & 
            (ventas['Fecha'] <= pd.to_datetime(fecha_fin)) & 
            (ventas['Producto'].isin(producto_filtrado))
        ]

        # Indicadores Clave
        litros_totales = ventas_filtradas['Cantidad Vendida'].sum()
        precio_promedio = ventas_filtradas['Precio por Litro'].mean()
        producto_mas_vendido = ventas_filtradas.groupby('Producto')['Cantidad Vendida'].sum().idxmax()

        st.markdown("<h3 style='color: black;'>Indicadores Clave</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Litros Totales Vendidos", f"{litros_totales:.2f} L")
        col2.metric("Precio Promedio", f"${precio_promedio:.2f}")
        col3.metric("Producto Más Vendido", producto_mas_vendido)

        # Gráfica de Pastel: Proporción por Producto
        st.markdown("<h3 style='color: black;'>Proporción de Ventas por Producto</h3>", unsafe_allow_html=True)
        proporciones = ventas_filtradas.groupby('Producto')['Cantidad Vendida'].sum()
        fig1, ax1 = plt.subplots()
        ax1.pie(proporciones, labels=proporciones.index, autopct='%1.1f%%', startangle=90, colors=['#28a745', '#dc3545', '#ffc107'])
        ax1.axis('equal')  # Asegura que el gráfico sea un círculo
        st.pyplot(fig1)

        # Gráfica de Barras: Ventas Totales por Producto
        st.markdown("<h3 style='color: black;'>Total de Ventas por Producto</h3>", unsafe_allow_html=True)
        ventas_por_producto = ventas_filtradas.groupby('Producto')['Cantidad Vendida'].sum().reset_index()
        fig2, ax2 = plt.subplots()
        ax2.bar(ventas_por_producto['Producto'], ventas_por_producto['Cantidad Vendida'], color=['#28a745', '#dc3545', '#ffc107'])
        ax2.set_title("Total de Ventas por Producto")
        ax2.set_xlabel("Producto")
        ax2.set_ylabel("Litros Vendidos")
        st.pyplot(fig2)

        # Botón para Exportar Datos
        st.markdown("<h3 style='color: black;'>Exportar Datos</h3>", unsafe_allow_html=True)
        csv = ventas_filtradas.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar Ventas como CSV",
            data=csv,
            file_name="ventas_filtradas.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay ventas registradas en el sistema.")

