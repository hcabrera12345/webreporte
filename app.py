import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import timedelta
# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Reportes Interactivos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📊 Dashboard de Reportes Interactivos")
# --- FUNCIONES DE LOS REPORTES ---
def render_facturacion():
    """Lógica completa del Reporte de Facturación"""
    FILE_PATH = "datos.xlsx"
    # --- DIAGNÓSTICO (Opcional, para seguridad) ---
    if os.path.exists(FILE_PATH):
        if os.path.getsize(FILE_PATH) == 0:
            st.error("❌ El archivo 'datos.xlsx' está vacío (0 bytes).")
            st.stop()
    
    # Carga de Datos
    @st.cache_data
    def load_data():
        if not os.path.exists(FILE_PATH):
            return None
        try:
            df = pd.read_excel(FILE_PATH, sheet_name="DINAMIZADO", engine='openpyxl')
            df['FECHA'] = pd.to_datetime(df['FECHA'])
            df['PROD'] = df['PROD'].astype(str)
            df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str)
            df = df[~df['PROD'].isin(['GNV', 'KRS'])]
            return df
        except Exception as e:
            st.error(f"Error leyendo Excel: {e}")
            return None
    df = load_data()
    if df is None:
        st.error(f"No se encontró 'datos.xlsx'. Súbelo al repositorio.")
        return
    # --- FILTROS ---
    st.sidebar.header("Filtros")
    
    # 1. Tiempo
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
        "Seleccionar Periodo", 
        ["Personalizado", "Último Mes", "Último Bimestre", "Último Trimestre", "Último Semestre", "Último Año", "Todo el Histórico"],
        key="period_selector", 
        on_change=update_dates
    )
    
    start_date = st.sidebar.date_input("Fecha Inicial", key="start_date")
    end_date = st.sidebar.date_input("Fecha Final", key="end_date")
    mask_date = (df['FECHA'] >= pd.to_datetime(start_date)) & (df['FECHA'] <= pd.to_datetime(end_date))
    df_filtered = df.loc[mask_date]
    # 2. Producto
    st.sidebar.subheader("2. Producto")
    products = sorted(df_filtered['PROD'].unique())
    selected_products = st.sidebar.multiselect("Seleccionar Producto(s)", products, default=products)
    if selected_products:
        df_filtered = df_filtered[df_filtered['PROD'].isin(selected_products)]
    # 3. Departamento
    st.sidebar.subheader("3. Departamento")
    departments = sorted(df_filtered['DEPARTAMENTO'].unique())
    selected_departments = st.sidebar.multiselect("Seleccionar Departamento(s)", departments, default=departments)
    if selected_departments:
        df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(selected_departments)]
    if df_filtered.empty:
        st.warning("No hay datos con estos filtros.")
        return
    # --- GRÁFICOS ---
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
        st.dataframe(df_filtered, use_container_width=True)
def render_importacion():
    """Lógica del Reporte de Importación"""
    st.header("Reporte de Importación")
    if os.path.exists("imagen_importacion.png"):
        st.image("imagen_importacion.png", use_container_width=True)
    else:
        st.info("ℹ️ Sube 'imagen_importacion.png' al repositorio.")
def render_despachos():
    """Lógica del Reporte de Despachos"""
    st.header("Reporte de Despachos Diarios")
    if os.path.exists("imagen_despachos.png"):
        st.image("imagen_despachos.png", use_container_width=True)
    else:
        st.info("ℹ️ Sube 'imagen_despachos.png' al repositorio.")
# --- CONTROLADOR PRINCIPAL ---
def main():
    # Menú de Navegación
    st.sidebar.title("Navegación")
    opcion = st.sidebar.radio(
        "Seleccionar Reporte:",
        ["Reporte Facturación", "Reporte de Importación", "Reporte Despachos"]
    )
    # Enrutador
    if opcion == "Reporte Facturación":
        render_facturacion()
    elif opcion == "Reporte de Importación":
        render_importacion()
    elif opcion == "Reporte Despachos":
        render_despachos()
if __name__ == "__main__":
    main()
