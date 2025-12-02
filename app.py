import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page Configuration
st.set_page_config(
    page_title="Dashboard de Reportes Interactivos",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Dashboard de Reportes Interactivos")

# File Path
FILE_PATH = "datos.xlsx"

# Load Data
@st.cache_data
def load_data():
    if not os.path.exists(FILE_PATH):
        return None
    try:
        df = pd.read_excel(FILE_PATH, sheet_name="DINAMIZADO")
        # Ensure FECHA is datetime
        df['FECHA'] = pd.to_datetime(df['FECHA'])
        # Ensure categorical columns are strings to avoid sorting errors
        df['PROD'] = df['PROD'].astype(str)
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = load_data()

if df is None:
    st.error(f"No se encontró el archivo '{FILE_PATH}' o hubo un error al leerlo. Por favor asegúrate de que el archivo esté en la carpeta del proyecto.")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filtros")

# 1. Time Analysis Filter
st.sidebar.subheader("1. Tiempo de Análisis")
min_date = df['FECHA'].min()
max_date = df['FECHA'].max()

start_date = st.sidebar.date_input("Fecha Inicial", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Fecha Final", max_date, min_value=min_date, max_value=max_date)

granularity = st.sidebar.radio("Granularidad", ["Diario", "Mensual"])

# Filter by date
mask_date = (df['FECHA'] >= pd.to_datetime(start_date)) & (df['FECHA'] <= pd.to_datetime(end_date))
df_filtered = df.loc[mask_date]

# 2. Product Filter
st.sidebar.subheader("2. Producto")
products = sorted(df['PROD'].unique())
selected_products = st.sidebar.multiselect("Seleccionar Producto(s)", products, default=products)

if selected_products:
    df_filtered = df_filtered[df_filtered['PROD'].isin(selected_products)]

# 3. Department Filter
st.sidebar.subheader("3. Departamento")
departments = sorted(df['DEPARTAMENTO'].unique())
selected_departments = st.sidebar.multiselect("Seleccionar Departamento(s)", departments, default=departments)

if selected_departments:
    df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(selected_departments)]

# --- Visualizations ---

# Layout: 2 Columns
col1, col2 = st.columns(2)

# Chart 1: Bar Chart (Volume vs Time)
with col1:
    st.subheader("Gráfico 1: Volumen en el Tiempo")
    
    if not df_filtered.empty:
        # Group data based on granularity
        if granularity == "Diario":
            df_grouped_time = df_filtered.groupby('FECHA')['VOLUMEN'].sum().reset_index()
            x_axis = 'FECHA'
            title_suffix = "por Día"
        else: # Mensual
            df_filtered['Month_Year'] = df_filtered['FECHA'].dt.to_period('M').astype(str)
            df_grouped_time = df_filtered.groupby('Month_Year')['VOLUMEN'].sum().reset_index()
            x_axis = 'Month_Year'
            title_suffix = "por Mes"
        
        fig_bar = px.bar(
            df_grouped_time, 
            x=x_axis, 
            y='VOLUMEN',
            title=f"Volumen {title_suffix}",
            color_discrete_sequence=px.colors.sequential.Blues_r  # Blue palette
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

# Chart 2: Pie Chart (Sector Percentage)
with col2:
    st.subheader("Gráfico 2: Distribución por Sector")
    
    if not df_filtered.empty:
        df_grouped_sector = df_filtered.groupby('SECTOR')['VOLUMEN'].sum().reset_index() # Assuming volume weighted or just count? User said "porcentaje según columna: SECTOR". Usually implies count of records or sum of volume. I'll use count of records if Volume isn't specified, but usually pie charts for business data use the metric (Volume). Let's stick to Volume for now as it's the main metric, or just count. The prompt says "GRAFICO DE TORTA, en porcentaje según columna: SECTOR". I will assume it's the distribution of the filtered data, so count of rows is safer if Volume isn't explicitly asked for the pie, but Volume is usually more meaningful. Let's use Count for now as it represents "Market Share" by sector presence, or Volume. Let's use Volume as it's the main metric. Actually, let's use Count of records to show "percentage of entries" if not specified. Wait, "eje y: VOLUMEN" was for bar chart. For Pie, it just says "según columna: SECTOR". I'll use Volume as the value to be safe, as it's a "Reporte de Volumen".
        
        # Let's use Volume for the pie chart values to be consistent with the business context (Volume Analysis).
        fig_pie = px.pie(
            df_filtered, 
            names='SECTOR', 
            values='VOLUMEN', # Using Volume for weight
            title="Porcentaje por Sector (Volumen)",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")

# Data Preview (Optional but helpful)
with st.expander("Ver Datos Filtrados"):
    st.dataframe(df_filtered)
