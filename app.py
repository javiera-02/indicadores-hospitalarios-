import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# --- CONFIGURACIÓN DE LA INTERFAZ WEB ---
st.set_page_config(page_title="Indicadores Hospitalarios REM20", layout="wide")
st.title("📊 Análisis de Indicadores Hospitalarios (REM20)")
st.write("Plataforma interactiva de consulta de datos extraídos en tiempo real desde datos.gob.cl")

# --- EXTRACCIÓN DESDE LA API (MÉTODO GET) ---
url_api = 'https://datos.gob.cl/api/3/action/datastore_search?resource_id=657cc933-eac8-4bfc-b004-c4d6dcd988a8'

@st.cache_data
def cargar_datos_api(url):
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            datos_json = respuesta.json()
            registros = datos_json['result']['records']
            return pd.DataFrame(registros)
        else:
            st.error(f"Error en la API. Código de estado: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"No se pudo conectar con la API: {e}")
        return None

df = cargar_datos_api(url_api)

if df is not None:
    # --- ANÁLISIS Y PROCESAMIENTO DE DATOS ---
    # Convertimos de forma forzada las columnas que traen los números del hospital
    columnas_numericas_fijas = ['_id', 'id', 'Valor', 'Cantidad']
    for col in df.columns:
        if col in columnas_numericas_fijas or df[col].astype(str).str.isdigit().sum() > len(df) * 0.4:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Filtro interactivo en la barra lateral
    st.sidebar.header("Filtros de Búsqueda")
    
    columnas_texto = [c for c in df.columns if c not in ['_id', 'id'] and df[c].dtype == 'object']
    if 'PERIODO' in df.columns:
        columnas_texto.append('PERIODO')

    columna_filtro = st.sidebar.selectbox("Selecciona columna para filtrar:", columnas_texto, index=columnas_texto.index('ESTABLECIMIENTO') if 'ESTABLECIMIENTO' in columnas_texto else 0)
    valores_unicos = df[columna_filtro].dropna().unique()
    valor_seleccionado = st.sidebar.selectbox("Selecciona un valor:", valores_unicos)
    
    # Filtrado con Pandas
    df_filtrado = df[df[columna_filtro] == valor_seleccionado]
    
    # --- MOSTRAR RESULTADOS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Datos Procesados")
        st.write(f"Registros encontrados: *{len(df_filtrado)}*")
        st.dataframe(df_filtrado, use_container_width=True)
        
    with col2:
        st.subheader("📉 Visualización Gráfica")
        
        # Forzamos una columna numérica para el gráfico (como el ID único o registros)
        fig, ax = plt.subplots(figsize=(6, 4))
        datos_grafico = df_filtrado.head(10)
        
        # Graficamos el ID del registro para mostrar la distribución de filas del hospital
        ax.bar(datos_grafico.index.astype(str), datos_grafico['_id'], color='#3498db')
        ax.set_title("Distribución de Registros en el Sistema")
        ax.set_ylabel("ID de Registro (Muestra)")
        ax.set_xlabel("Índice de Fila")
        plt.tight_layout()
        st.pyplot(fig)
