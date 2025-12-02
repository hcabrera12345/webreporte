import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import timedelta
# Configuración de Página
st.set_page_config(
    page_title="Dashboard de Reportes Interactivos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📊 Dashboard de Reportes Interactivos")
# Navegación Lateral
st.sidebar.title("Navegación")
report_mode = st.sidebar.radio(
    "Seleccionar Reporte:",
    ["Reporte Facturación", "Reporte de Importación", "Reporte Despachos"]
)
# ==========================================
# REPORTE 1: FACTURACIÓN (Tu reporte original)
# ==========================================
if report_mode == "Reporte Facturación":
    
    FILE_PATH = "datos.xlsx"
    # Función de Carga de Datos
    @st.cache_data
    def load_data():
        if not os.path.exists(FILE_PATH):
            return None
        try:
            # Leer Excel con motor openpyxl
            df = pd.read_excel(FILE_PATH, sheet_name="DINAMIZADO", engine='openpyxl')
            
            # Convertir Fecha
            df['FECHA'] = pd.to_datetime(df['FECHA'])
            
            # Convertir Textos
            df['PROD'] = df['PROD'].astype(str)
            df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str)
            
            # CORRECCIÓN DECIMALES: Reemplazar ',' por '.' en VOLUMEN
            if df['VOLUMEN'].dtype == 'object':
                df['VOLUMEN'] = df['VOLUMEN'].astype(str).str.replace('.', '', regex=False) # Quitar miles
                df['VOLUMEN'] = df['VOLUMEN'].str.replace(',', '.') # Cambiar coma por punto
                df['VOLUMEN'] = pd.to_numeric(df['VOLUMEN'], errors='coerce')
            
            # FILTRO: Eliminar GNV y KRS
            df = df[~df['PROD'].isin(['GNV', 'KRS'])]
            
            return df
        except Exception as e:
            st.error(f"Error crítico leyendo el Excel: {e}")
            return None
    # Cargar datos
    df = load_data()
    # Verificar si cargó bien
    if df is None:
        st.error("❌ El archivo 'datos.xlsx' está dañado o no existe en GitHub. Por favor súbelo de nuevo.")
        st.stop()
    # --- FILTROS ORIGINALES ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filtros Facturación")
    # 1. Filtro de Tiempo
    st.sidebar.subheader("1. Tiempo de Análisis")
    
    if 'start_date' not in st.session_state:
        st.session_state.start_date = df['FECHA'].min()
    if 'end_date' not in st.session_state:
        st.session_state.end_date = df['FECHA'].max()
    def update_dates():
        period = st.session_state.period_selector
        max_date = df['FECHA'].max()
        if period == "Último Mes":
            st.session_state.start_date = max_date - pd.DateOffset(months=1)
            st.session_state.end_date = max_date
        elif period == "Último Bimestre":
            st.session_state.start_date = max_date - pd.DateOffset(months=2)
            st.session_state.end_date = max_date
        elif period == "Último Trimestre":
            st.session_state.start_date = max_date - pd.DateOffset(months=3)
            st.session_state.end_date = max_date
        elif period == "Último Semestre":
            st.session_state.start_date = max_date - pd.DateOffset(months=6)
            st.session_state.end_date = max_date
        elif period == "Último Año":
            st.session_state.start_date = max_date - pd.DateOffset(years=1)
            st.session_state.end_date = max_date
        elif period == "Todo el Histórico":
            st.session_state.start_date = df['FECHA'].min()
            st.session_state.end_date = df['FECHA'].max()
    st.sidebar.selectbox(
        "Seleccionar Periodo Recomendado", 
        ["Personalizado", "Último Mes", "Último Bimestre", "Último Trimestre", "Último Semestre", "Último Año", "Todo el Histórico"],
        key="period_selector", 
        on_change=update_dates
    )
    
    start_date = st.sidebar.date_input("Fecha Inicial", key="start_date")
    end_date = st.sidebar.date_input("Fecha Final", key="end_date")
    # Aplicar Filtro Fecha
    mask_date = (df['FECHA'] >= pd.to_datetime(start_date)) & (df['FECHA'] <= pd.to_datetime(end_date))
    df_filtered = df.loc[mask_date]
    # 2. Filtro Producto
    st.sidebar.subheader("2. Producto")
    products = sorted(df_filtered['PROD'].unique())
    selected_products = st.sidebar.multiselect("Seleccionar Producto(s)", products, default=products)
    if selected_products:
        df_filtered = df_filtered[df_filtered['PROD'].isin(selected_products)]
    # 3. Filtro Departamento
    st.sidebar.subheader("3. Departamento")
    departments = sorted(df_filtered['DEPARTAMENTO'].unique())
    selected_departments = st.sidebar.multiselect("Seleccionar Departamento(s)", departments, default=departments)
    if selected_departments:
        df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(selected_departments)]
    # --- GRÁFICOS ---
    if df_filtered.empty:
        st.warning("No hay datos con estos filtros.")
        st.stop()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Gráfico 1: Evolución Mensual")
        df_filtered['Month_Year'] = df_filtered['FECHA'].dt.to_period('M').astype(str)
        df_grouped_time = df_filtered.groupby('Month_Year')['VOLUMEN'].sum().reset_index()
        fig_bar = px.bar(df_grouped_time, x='Month_Year', y='VOLUMEN', title="Volumen Mensual", text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.subheader("Gráfico 2: Sectores")
        fig_pie = px.pie(df_filtered, names='SECTOR', values='VOLUMEN', title="Distribución", color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown("---")
    st.subheader("Gráfico 3: Volumen por Departamento")
    df_dept = df_filtered.groupby('DEPARTAMENTO')['VOLUMEN'].sum().reset_index().sort_values('VOLUMEN')
    fig_horiz = px.bar(df_dept, x='VOLUMEN', y='DEPARTAMENTO', orientation='h', title="Ranking Departamentos", color='VOLUMEN', text_auto='.2s')
    st.plotly_chart(fig_horiz, use_container_width=True)
    with st.expander("Ver Datos"):
        st.dataframe(df_filtered)
# ==========================================
# REPORTE 2: IMPORTACIÓN
# ==========================================
elif report_mode == "Reporte de Importación":
    st.header("Reporte de Importación")
    if os.path.exists("imagen_importacion.png"):
        st.image("imagen_importacion.png", use_container_width=True)
    else:
        st.info("ℹ️ Sube la imagen 'imagen_importacion.png' a GitHub.")
# ==========================================
# REPORTE 3: DESPACHOS
# ==========================================
elif report_mode == "Reporte Despachos":
    st.header("Reporte de Despachos Diarios")
    if os.path.exists("imagen_despachos.png"):
        st.image("imagen_despachos.png", use_container_width=True)
    else:
        st.info("ℹ️ Sube la imagen 'imagen_despachos.png' a GitHub.")
