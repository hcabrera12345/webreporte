import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import timedelta
# Page Configuration (Responsive and Wide)
st.set_page_config(
    page_title="Dashboard de Reportes Interactivos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Title
st.title("📊 Dashboard de Reportes Interactivos")
# --- NAVEGACIÓN (Añadido según solicitud) ---
st.sidebar.title("Navegación")
report_mode = st.sidebar.radio(
    "Seleccionar Reporte:",
    ["Reporte Facturación", "Reporte de Importación", "Reporte Despachos"]
)
# --- SECCIÓN 1: REPORTE FACTURACIÓN (Tu código original) ---
if report_mode == "Reporte Facturación":
    # File Path
    FILE_PATH = "datos.xlsx"
    # Load Data
    @st.cache_data
    def load_data():
        if not os.path.exists(FILE_PATH):
            return None
        try:
            # Specify engine explicitly to avoid Streamlit Cloud errors
            df = pd.read_excel(FILE_PATH, sheet_name="DINAMIZADO", engine='openpyxl')
            
            # Ensure FECHA is datetime
            df['FECHA'] = pd.to_datetime(df['FECHA'])
            
            # Ensure categorical columns are strings
            df['PROD'] = df['PROD'].astype(str)
            df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str)
            
            # --- MODIFICACIÓN 3: Eliminar GNV y KRS ---
            df = df[~df['PROD'].isin(['GNV', 'KRS'])]
            
            return df
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            return None
    df = load_data()
    if df is None:
        st.error(f"No se encontró el archivo '{FILE_PATH}'. Por favor asegúrate de subirlo al repositorio.")
        st.stop()
    # --- Sidebar Filters ---
    st.sidebar.header("Filtros")
    # --- MODIFICACIÓN 5: Periodos Recomendados ---
    st.sidebar.subheader("1. Tiempo de Análisis")
    # Helper to manage date updates
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
    period_options = ["Personalizado", "Último Mes", "Último Bimestre", "Último Trimestre", "Último Semestre", "Último Año", "Todo el Histórico"]
    st.sidebar.selectbox(
        "Seleccionar Periodo Recomendado", 
        options=period_options, 
        key="period_selector", 
        on_change=update_dates
    )
    # Date Inputs (Connected to Session State)
    start_date = st.sidebar.date_input("Fecha Inicial", key="start_date")
    end_date = st.sidebar.date_input("Fecha Final", key="end_date")
    # Filter by date
    mask_date = (df['FECHA'] >= pd.to_datetime(start_date)) & (df['FECHA'] <= pd.to_datetime(end_date))
    df_filtered = df.loc[mask_date]
    # --- MODIFICACIÓN 2: Granularidad siempre Mensual ---
    # (No hay selector, se asume mensual para el gráfico de tiempo)
    # 2. Product Filter
    st.sidebar.subheader("2. Producto")
    products = sorted(df_filtered['PROD'].unique())
    selected_products = st.sidebar.multiselect("Seleccionar Producto(s)", products, default=products)
    if selected_products:
        df_filtered = df_filtered[df_filtered['PROD'].isin(selected_products)]
    # 3. Department Filter
    st.sidebar.subheader("3. Departamento")
    departments = sorted(df_filtered['DEPARTAMENTO'].unique())
    selected_departments = st.sidebar.multiselect("Seleccionar Departamento(s)", departments, default=departments)
    if selected_departments:
        df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(selected_departments)]
    # --- Visualizations ---
    if df_filtered.empty:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")
        st.stop()
    # Layout: Row 1 (Bar Chart Time + Pie Chart)
    col1, col2 = st.columns([2, 1]) # 2/3 for bar, 1/3 for pie
    # Chart 1: Bar Chart (Volume vs Time - Monthly)
    with col1:
        st.subheader("Gráfico 1: Evolución Mensual del Volumen")
        
        # Group by Month-Year
        df_filtered['Month_Year'] = df_filtered['FECHA'].dt.to_period('M').astype(str)
        df_grouped_time = df_filtered.groupby('Month_Year')['VOLUMEN'].sum().reset_index()
        
        fig_bar_time = px.bar(
            df_grouped_time, 
            x='Month_Year', 
            y='VOLUMEN',
            title="Volumen por Mes",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            text_auto='.2s' # Show values on bars
        )
        fig_bar_time.update_layout(xaxis_title="Mes", yaxis_title="Volumen")
        st.plotly_chart(fig_bar_time, use_container_width=True)
    # Chart 2: Pie Chart (Sector)
    with col2:
        st.subheader("Gráfico 2: Distribución por Sector")
        
        # --- MODIFICACIÓN 1: Colores variados (no solo azul) ---
        fig_pie = px.pie(
            df_filtered, 
            names='SECTOR', 
            values='VOLUMEN', 
            title="Participación por Sector",
            color_discrete_sequence=px.colors.qualitative.Bold # Varied palette
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    # Layout: Row 2 (Horizontal Bar Chart)
    st.markdown("---")
    st.subheader("Gráfico 3: Volumen por Departamento")
    # --- MODIFICACIÓN 4: Gráfico de Barras Horizontales ---
    df_grouped_dept = df_filtered.groupby('DEPARTAMENTO')['VOLUMEN'].sum().reset_index().sort_values('VOLUMEN', ascending=True)
    fig_bar_horiz = px.bar(
        df_grouped_dept,
        x='VOLUMEN',
        y='DEPARTAMENTO',
        orientation='h',
        title="Volumen Total por Departamento",
        color='VOLUMEN',
        color_continuous_scale=px.colors.sequential.Viridis, # Nice gradient
        text_auto='.2s'
    )
    fig_bar_horiz.update_layout(xaxis_title="Volumen", yaxis_title="Departamento")
    st.plotly_chart(fig_bar_horiz, use_container_width=True)
    # Data Preview
    with st.expander("Ver Datos Detallados"):
        st.dataframe(df_filtered, use_container_width=True)
# --- SECCIÓN 2: REPORTE IMPORTACIÓN ---
elif report_mode == "Reporte de Importación":
    st.header("Reporte de Importación")
    if os.path.exists("imagen_importacion.png"):
        st.image("imagen_importacion.png", use_container_width=True)
    else:
        st.info("ℹ️ Sube la imagen 'imagen_importacion.png' al repositorio para verla aquí.")
# --- SECCIÓN 3: REPORTE DESPACHOS ---
elif report_mode == "Reporte Despachos":
    st.header("Reporte de Despachos Diarios")
    if os.path.exists("imagen_despachos.png"):
        st.image("imagen_despachos.png", use_container_width=True)
    else:
        st.info("ℹ️ Sube la imagen 'imagen_despachos.png' al repositorio para verla aquí.")
