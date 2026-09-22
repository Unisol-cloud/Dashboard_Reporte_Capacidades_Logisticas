# -*- coding: utf-8 -*-

"""

Dashboard de Capacidades Logisticas - Cotas Proveedores Nacionales

Visualizacion en tiempo real conectada directamente a PostgreSQL OMS y AS400.

"""



import streamlit as st
import requests
import os



import pandas as pd

from io import BytesIO

from datetime import datetime

import os

import subprocess



st.set_page_config(

    page_title="Capacidades Logísticas | Hites",

    page_icon="📦",

    layout="wide",

    initial_sidebar_state="expanded",

)



# ============================================================

# CSS Corporativo Hites
# Paleta: Azul #152088 | Fucsia #FF49A0 | Alerta #993700

# ============================================================

st.markdown("""

<style>

    /* ── Fuente moderna ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Layout general ── */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* ── Sidebar corporativo ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #152088 0%, #0e1660 100%) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown *,
    section[data-testid="stSidebar"] .stText * {
        color: #ffffff !important;
    }
    /* Excepcion para el Selectbox: mantener colores legibles */
    section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #000000 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #e0e4ff !important;
        font-size: 0.88rem;
        padding: 2px 0;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #FF49A0 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
        background-color: #FF49A0 !important;
        border-color: #FF49A0 !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background-color: #FF49A0 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #e03d8e !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,73,160,0.4);
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
    }

    /* ── KPI Cards ── */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px 20px !important;
        border-left: 5px solid #152088;
        box-shadow: 0 2px 8px rgba(21,32,136,0.10);
        transition: box-shadow 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 4px 16px rgba(21,32,136,0.18);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #152088 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #666 !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
    }

    /* ── Títulos de sección ── */
    h1 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #152088 !important;
        padding-bottom: 0.4rem;
        border-bottom: 3px solid #FF49A0;
        margin-bottom: 1.2rem !important;
    }
    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #152088 !important;
    }
    h3 {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #1a2ba0 !important;
    }

    /* ── Tablas de datos ── */
    .stDataFrame thead tr th {
        background-color: #152088 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #f0f2ff !important;
    }
    .stDataFrame tbody tr:hover {
        background-color: #ffe4f2 !important;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        color: #152088 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FF49A0 !important;
        border-bottom: 3px solid #FF49A0 !important;
    }

    /* ── Selectboxes y filtros ── */
    .stSelectbox label, .stMultiSelect label {
        font-weight: 500 !important;
        color: #152088 !important;
        font-size: 0.85rem !important;
    }

    /* ── Alertas y mensajes ── */
    .stAlert {
        border-radius: 10px !important;
    }

    /* ── Botones generales ── */
    .stDownloadButton button {
        background-color: #152088 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stDownloadButton button:hover {
        background-color: #0e1660 !important;
        box-shadow: 0 4px 12px rgba(21,32,136,0.3);
    }

    /* ── Caption / footer ── */
    .stCaption {
        color: #aaa !important;
        font-size: 0.75rem !important;
    }

</style>

""", unsafe_allow_html=True)


# ============================================================
# Descarga Segura en Tiempo Real (API GitHub)
# ============================================================
@st.cache_data(show_spinner=False, ttl=60)
def descargar_datos():
    import requests
    import os
    if "GITHUB_TOKEN" not in st.secrets:
        st.warning("Falta GITHUB_TOKEN en los Secrets de Streamlit.")
        return
    token = st.secrets["GITHUB_TOKEN"]
    # Usamos la API oficial con Accept raw para evadir la caché de la CDN y traer el último commit
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.raw"}
    repo_owner = "Unisol-cloud"
    repo_name = "Dashboard_Datos"
    branch = "master"
    archivos = [
        "cotas_ddc.parquet", "cotas_dvh.parquet", "cotas_mkp.parquet",
        "cota_courier_mkp.parquet", "cota_tamano.parquet", "dia_entrega_dvh.parquet",
        "estado_courier_mkp.parquet", "frecuencia_ddc.parquet", "leadtime_localidad_sellers.parquet",
        "lead_time_sellers.parquet", "lead_time_skus.parquet", "resumen_cotas.parquet",
        "ultima_actualizacion.txt"
    ]
    os.makedirs("datos_cache", exist_ok=True)
    for archivo in archivos:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/datos_cache/{archivo}?ref={branch}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            with open(f"datos_cache/{archivo}", "wb") as f:
                f.write(resp.content)
        else:
            st.error(f"Error descargando {archivo}: HTTP {resp.status_code}")

descargar_datos()





# ============================================================

# Sidebar: Navegacion y controles

# ============================================================

from queries import (

    obtener_cotas_ddc, obtener_cotas_dvh, obtener_cotas_mkp,

    obtener_cota_tamano, obtener_cota_courier_mkp,

    obtener_lead_time_skus, obtener_frecuencia_ddc,

    obtener_lead_time_sellers, obtener_leadtime_localidad_sellers,

    obtener_estado_courier_mkp, obtener_resumen_cotas,

    obtener_fecha_actualizacion

)



# ============================================================

# Sidebar Navegacion

# ============================================================

logo_path = os.path.join(os.path.dirname(__file__), "logo_hites.png")

if os.path.exists(logo_path):

    st.sidebar.image(logo_path, use_container_width=True)

st.sidebar.markdown("---")

st.sidebar.markdown("### 📋 Navegación")



# Mostrar fecha de ultima actualizacion

fecha_act = obtener_fecha_actualizacion()

st.sidebar.markdown(f"🕐 **Datos al:** {fecha_act}")



grupos_vistas = {
    "🌐 Visión Global": [
        "🎯 Resumen"
    ],
    "🏢 Despacho Vía Hites (DVH)": [
        "📊 Cotas DVH",
        "📦 Cota Recepcion DVH",
        "📅 Dia Entrega DVH"
    ],
    "🚛 Despacho Directo a Cliente (DDC)": [
        "📊 Cotas DDC",
        "📅 Frecuencia DDC"
    ],
    "🏪 Marketplace & Sellers": [
        "📊 Cotas MKP Seller",
        "🏪 Lead Time Sellers",
        "📍 LT Localidad Sellers",
        "⏱ Lead Time SKU VeV"
    ],
    "📦 Última Milla & Courier": [
        "🚚 Cota Courier MKP",
        "🛵 Ultima Milla MKP"
    ]
}

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("---")
area_seleccionada = st.sidebar.radio(
    "📂 **Área de Negocio**", 
    list(grupos_vistas.keys()),
    index=0
)
st.sidebar.markdown("---")

vistas_del_area = grupos_vistas[area_seleccionada]

pagina = st.sidebar.radio(
    "Vistas Disponibles",
    vistas_del_area
)



if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
    st.cache_data.clear()
    st.success("Cache limpia. Recargando datos...")
    st.rerun()


# ============================================================

# Utilidad: Generar Excel descargable

# ============================================================

import re

def generar_excel(dataframes: dict) -> bytes:
    """Genera un archivo Excel con múltiples hojas y formato corporativo Hites."""
    from openpyxl.styles import PatternFill, Font, Alignment
    from openpyxl.utils import get_column_letter
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nombre_hoja, df in dataframes.items():
            # Limpiar caracteres prohibidos en hojas de Excel
            nombre_limpio = re.sub(r'[\\/\?\*\[\]\:]', '_', nombre_hoja)
            nombre_limpio = nombre_limpio[:31]
            df.to_excel(writer, sheet_name=nombre_limpio, index=False)
            
            # Formatear la hoja
            worksheet = writer.sheets[nombre_limpio]
            
            # Colores corporativos
            header_fill = PatternFill(start_color='152088', end_color='152088', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True)
            
            # Cabeceras
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Congelar paneles y autofiltro
            worksheet.freeze_panes = 'A2'
            max_col_letter = get_column_letter(worksheet.max_column)
            worksheet.auto_filter.ref = f"A1:{max_col_letter}{worksheet.max_row}"
            
            # Auto-ajuste de ancho de columnas
            for col in worksheet.columns:
                max_length = 0
                column_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                # Ancho mínimo de 10, máximo de 50
                adjusted_width = min(max(max_length + 2, 10), 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
    return output.getvalue()


def boton_descarga(df: pd.DataFrame, nombre: str, key: str):

    """Muestra un boton de descarga de Excel para un DataFrame."""

    excel_data = generar_excel({nombre: df})

    st.download_button(

        label="📥 Descargar Excel",

        data=excel_data,

        file_name=f"{nombre}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",

        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

        key=key,

    )





def crear_tabla_dinamica_tamano(df: pd.DataFrame) -> pd.DataFrame:
    """Crea tabla dinamica tipo pivot con semaforo de colores para recepcion por tamaño."""
    if df.empty: return df
    df_base = df.copy()
    
    if "Cota Inicial" in df_base.columns:
        df_base.rename(columns={"Cota Inicial": "Cota"}, inplace=True)
    if "Fecha Ingreso CD" in df_base.columns:
        df_base.rename(columns={"Fecha Ingreso CD": "Fecha Recepcion"}, inplace=True)
        
    df_base['Cota'] = pd.to_numeric(df_base['Cota'], errors='coerce').fillna(0)
    df_base['Cota Acumulada'] = pd.to_numeric(df_base['Cota Acumulada'], errors='coerce').fillna(0)
    df_base['Fecha Recepcion'] = pd.to_datetime(df_base['Fecha Recepcion'], errors='coerce')
    df_base = df_base.dropna(subset=['Fecha Recepcion'])
    
    dias_es = {
        0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
        4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
    }
    df_base['Nombre_Dia'] = df_base['Fecha Recepcion'].dt.dayofweek.map(dias_es)
    
    df_base['Fecha_Dia'] = df_base['Fecha Recepcion'].dt.strftime('%d-%m-%Y') + " " + df_base['Nombre_Dia']
    
    fechas_ordenadas = df_base[['Fecha Recepcion', 'Fecha_Dia']].drop_duplicates().sort_values('Fecha Recepcion')
    df_base['Fecha_Dia'] = pd.Categorical(df_base['Fecha_Dia'], categories=fechas_ordenadas['Fecha_Dia'], ordered=True)
    
    agrupado = df_base.groupby(['Fecha_Dia', 'Tamano'])[['Cota', 'Cota Acumulada']].sum().reset_index()
    
    agrupado['pct_num'] = agrupado.apply(
        lambda x: x['Cota Acumulada'] / x['Cota'] * 100 if x['Cota'] > 0 else 0, axis=1
    )
    
    def aplicar_semaforo(pct):
        if pct >= 100:
            return "\U0001f534 {:.0f}%".format(pct)
        elif pct >= 75:
            return "\U0001f7e0 {:.0f}%".format(pct)
        else:
            return "\U0001f7e2 {:.0f}%".format(pct)
            
    agrupado['% Consumido'] = agrupado['pct_num'].apply(aplicar_semaforo)
    agrupado.rename(columns={'Cota Acumulada': 'Consumo'}, inplace=True)
    
    agrupado['Cota'] = agrupado['Cota'].astype(int).astype(str)
    agrupado['Consumo'] = agrupado['Consumo'].astype(int).astype(str)
    
    pivot = agrupado.pivot_table(
        index='Fecha_Dia',
        columns='Tamano',
        values=['Cota', 'Consumo', '% Consumido'],
        aggfunc='first'
    )
    
    if pivot.empty: return pivot
    
    pivot = pivot.reorder_levels([1, 0], axis=1)
    
    tamanos = ['L', 'M', 'S']
    cols_existentes = [t for t in tamanos if t in pivot.columns.get_level_values(0)]
    metricas = ['Cota', 'Consumo', '% Consumido']
    
    multi_cols = pd.MultiIndex.from_product([cols_existentes, metricas], names=['Tamano', 'Metrica'])
    pivot = pivot.reindex(multi_cols, axis=1).fillna("")
    
    totales = df_base.groupby('Fecha_Dia')[['Cota', 'Cota Acumulada']].sum().reset_index()
    totales['pct_num'] = totales.apply(
        lambda x: x['Cota Acumulada'] / x['Cota'] * 100 if x['Cota'] > 0 else 0, axis=1
    )
    totales['Total % Consumido'] = totales['pct_num'].apply(aplicar_semaforo)
    totales.rename(columns={'Cota': 'Total Cota', 'Cota Acumulada': 'Total Consumo'}, inplace=True)
    totales['Total Cota'] = totales['Total Cota'].astype(int).astype(str)
    totales['Total Consumo'] = totales['Total Consumo'].astype(int).astype(str)
    
    totales = totales.set_index('Fecha_Dia')
    
    pivot[('Totales', 'Total Cota')] = totales['Total Cota']
    pivot[('Totales', 'Total Consumo')] = totales['Total Consumo']
    pivot[('Totales', 'Total % Consumido')] = totales['Total % Consumido']
    
    pivot.columns.names = ['Tamaño / Totales', 'Métrica']
    
    return pivot

def crear_tabla_dinamica_cotas(df: pd.DataFrame, col_fecha: str, col_fila: str) -> pd.DataFrame:

    """Crea tabla dinamica tipo pivot con semaforo de colores para cotas."""

    if df.empty:

        return df

    df_base = df.copy()

    if 'Cota' not in df_base.columns or 'Cota Acumulada' not in df_base.columns:

        return df

    df_base['Cota'] = pd.to_numeric(df_base['Cota'], errors='coerce').fillna(0)

    df_base['Cota Acumulada'] = pd.to_numeric(df_base['Cota Acumulada'], errors='coerce').fillna(0)

    if 'Dia' not in df_base.columns:

        return df

    if col_fecha not in df_base.columns or col_fila not in df_base.columns:

        return df



    # Convertir fecha a datetime para ordenamiento correcto

    df_base[col_fecha] = pd.to_datetime(df_base[col_fecha], errors='coerce')

    df_base = df_base.dropna(subset=[col_fecha])



    # Obtener orden cronologico de fechas

    fechas_ordenadas = sorted(df_base[col_fecha].unique())

    # Formatear fecha como DD-MM-YYYY para display

    fecha_display_map = {}

    for f in fechas_ordenadas:

        fecha_display_map[f] = pd.Timestamp(f).strftime('%d-%m-%Y')

    fecha_display_order = [fecha_display_map[f] for f in fechas_ordenadas]



    df_base['Fecha_Display'] = df_base[col_fecha].map(fecha_display_map)

    df_base['Fecha_Display'] = pd.Categorical(

        df_base['Fecha_Display'], categories=fecha_display_order, ordered=True

    )



    # Agrupar

    agrupado = df_base.groupby([col_fila, 'Fecha_Display', 'Dia'])[['Cota', 'Cota Acumulada']].sum().reset_index()



    # Calcular % Consumido con indicadores de color (circulos emoji)

    agrupado['pct_num'] = agrupado.apply(

        lambda x: x['Cota Acumulada'] / x['Cota'] * 100 if x['Cota'] > 0 else 0, axis=1

    )



    def aplicar_semaforo(pct):

        if pct >= 100:

            return "\U0001f534 {:.0f}%".format(pct)

        elif pct >= 75:

            return "\U0001f7e0 {:.0f}%".format(pct)

        else:

            return "\U0001f7e2 {:.0f}%".format(pct)



    agrupado['% Consumido'] = agrupado['pct_num'].apply(aplicar_semaforo)

    agrupado.rename(columns={'Cota Acumulada': 'Consumo'}, inplace=True)



    # Convertir TODO a string para evitar errores de tipo mixto en el pivot

    agrupado['Cota'] = agrupado['Cota'].astype(int).astype(str)

    agrupado['Consumo'] = agrupado['Consumo'].astype(int).astype(str)



    # Crear pivot

    pivot = agrupado.pivot_table(

        index=col_fila,

        columns=['Fecha_Display', 'Dia'],

        values=['Cota', 'Consumo', '% Consumido'],

        aggfunc='first'

    )

    if pivot.empty:

        return pivot



    # Reordenar niveles: Fecha > Dia > Metrica

    pivot = pivot.reorder_levels([1, 2, 0], axis=1)

    pivot = pivot.sort_index(axis=1, level=[0, 1], sort_remaining=False)

    # Orden de metricas: Cota, Consumo, % Consumido

    pivot = pivot.reindex(['Cota', 'Consumo', '% Consumido'], level=2, axis=1)

    pivot.fillna("", inplace=True)



    # Renombrar nivel superior de columnas para que diga "Fechas"

    pivot.columns.names = ['Fechas', 'Dia', 'Metrica']



    return pivot





def crear_tabla_frecuencia_dias(df: pd.DataFrame, col_fila: str, col_dia: str) -> pd.DataFrame:

    """Crea tabla dinamica tipo pivot para Dias de Entrega (SI/0)."""

    if df.empty or col_fila not in df.columns or col_dia not in df.columns:

        return df



    df_base = df.copy()

    

    # Mapear dias a formato corto

    day_map = {

        'Lunes': 'Lun', 'Martes': 'Mar', 'Miércoles': 'Mie', 'Miercoles': 'Mie', 'Jueves': 'Jue',

        'Viernes': 'Vie', 'Sábado': 'Sab', 'Sabado': 'Sab', 'Domingo': 'Dom',

        'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mie', 'Thursday': 'Jue',

        'Friday': 'Vie', 'Saturday': 'Sab', 'Sunday': 'Dom',

        'Lun': 'Lun', 'Mar': 'Mar', 'Mie': 'Mie', 'Jue': 'Jue', 'Vie': 'Vie', 'Sab': 'Sab', 'Dom': 'Dom'

    }

    df_base['Dia_Corto'] = df_base[col_dia].astype(str).str.strip().map(day_map).fillna(df_base[col_dia])



    agrupado = df_base.groupby([col_fila, 'Dia_Corto']).size().reset_index(name='count')

    agrupado['Valor'] = agrupado['count'].apply(lambda x: "SI" if x > 0 else "0")



    pivot = agrupado.pivot_table(

        index=col_fila,

        columns='Dia_Corto',

        values='Valor',

        aggfunc='first'

    ).fillna("0")



    # Asegurar que todas las columnas de dias existan y en orden

    orden_dias = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']

    for d in orden_dias:

        if d not in pivot.columns:

            pivot[d] = "0"

            

    pivot = pivot[orden_dias]

    return pivot



def crear_tabla_dias_entrega_dvh(df: pd.DataFrame, col_fila: str, col_dia_no_laborable: str) -> pd.DataFrame:

    """Crea tabla dinamica tipo pivot para Dias de Entrega DVH (Lógica invertida)."""

    if df.empty or col_fila not in df.columns or col_dia_no_laborable not in df.columns:

        return df



    df_base = df.copy()

    proveedores = df_base[col_fila].unique()

    orden_dias = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']

    

    day_map = {

        'Lunes': 'Lun', 'Martes': 'Mar', 'Miércoles': 'Mie', 'Miercoles': 'Mie', 'Jueves': 'Jue',

        'Viernes': 'Vie', 'Sábado': 'Sab', 'Sabado': 'Sab', 'Domingo': 'Dom',

        'Lun': 'Lun', 'Mar': 'Mar', 'Mie': 'Mie', 'Jue': 'Jue', 'Vie': 'Vie', 'Sab': 'Sab', 'Dom': 'Dom'

    }

    

    df_base['Dia_Corto'] = df_base[col_dia_no_laborable].astype(str).str.strip().map(day_map).fillna(df_base[col_dia_no_laborable])

    

    no_laborables_por_prov = df_base.dropna(subset=['Dia_Corto']).groupby(col_fila)['Dia_Corto'].apply(set).to_dict()

    

    datos = []

    for prov in proveedores:

        fila = {col_fila: prov}

        no_lab = no_laborables_por_prov.get(prov, set())

        for d in orden_dias:

            if d in no_lab:

                fila[d] = "0"

            else:

                fila[d] = "SI"

        datos.append(fila)

        

    pivot = pd.DataFrame(datos).set_index(col_fila)

    return pivot[orden_dias]







def crear_tabla_dinamica_lt_localidad(df: pd.DataFrame) -> pd.DataFrame:
    """Genera la tabla tabular (filas) de LT Localidad Sellers."""
    df_pivot = df.copy()
    
    columnas_agrupacion = [
        'ID Seller center', 'Seller', 'Region Destino', 
        'ID Localidad', 'Localidad Destino', 'LeadTime Seller', 'LeadTime Courier'
    ]
    
    # Verificar que existan las columnas
    for col in columnas_agrupacion:
        if col not in df_pivot.columns:
            return df_pivot
            
    # Llenar nulos para no perder registros en groupby (por seguridad si pandas es < 1.1)
    df_pivot['ID Seller center'] = df_pivot['ID Seller center'].fillna("N/A")
    df_pivot['LeadTime Seller'] = pd.to_numeric(df_pivot['LeadTime Seller'], errors='coerce').fillna(0).astype(int)
    df_pivot['LeadTime Courier'] = pd.to_numeric(df_pivot['LeadTime Courier'], errors='coerce').fillna(0).astype(int)
    
    if 'id_legacy' in df_pivot.columns:
        df_pivot['id_legacy'] = pd.to_numeric(df_pivot['id_legacy'], errors='coerce').fillna(0)
        pivot = df_pivot.groupby(columnas_agrupacion).agg(
            Suma_id_legacy=('id_legacy', 'sum')
        ).reset_index()
        pivot.rename(columns={'Suma_id_legacy': 'Suma de id_legacy'}, inplace=True)
    else:
        pivot = df_pivot.groupby(columnas_agrupacion).size().reset_index(name='Conteo')
        
    pivot = pivot.sort_values(by=['Seller', 'Region Destino', 'ID Localidad'], ascending=[True, True, True])
    pivot['ID Seller center'] = pivot['ID Seller center'].replace("N/A", None)
    
    return pivot

def crear_tabla_dinamica_ultima_milla(df: pd.DataFrame) -> pd.DataFrame:
    """Genera la tabla agrupada de Ultima Milla MKP."""
    if 'Courier' not in df.columns or 'FA' not in df.columns or 'R' not in df.columns:
        return df
    
    df_pivot = df.copy()
    
    # Asegurar que sean numericos
    df_pivot['FA'] = pd.to_numeric(df_pivot['FA'], errors='coerce').fillna(0)
    df_pivot['R'] = pd.to_numeric(df_pivot['R'], errors='coerce').fillna(0)
    
    pivot = df_pivot.groupby('Courier', dropna=False).agg(
        FA_sum=('FA', 'sum'),
        R_sum=('R', 'sum')
    ).reset_index()
    
    pivot.rename(columns={
        'Courier': 'Nombre Courier',
        'FA_sum': 'Fuente de Abastecimiento Activa',
        'R_sum': 'Rutas Activas'
    }, inplace=True)
    
    pivot = pivot.sort_values(by='Nombre Courier', ascending=True)
    
    return pivot

def mostrar_tabla_filtrada(df: pd.DataFrame, titulo: str, key_prefix: str,

                           columnas_filtro: list = None, valores_por_defecto: dict = None,

                           es_pivot_cotas: bool = False, col_fecha: str = None, col_fila: str = None,

                           es_pivot_dias: bool = False, col_dia: str = None,
                           es_pivot_dias_dvh: bool = False, es_pivot_tamano: bool = False,
                           es_pivot_lt_localidad: bool = False, es_pivot_ultima_milla: bool = False):

    """Muestra una tabla con filtros interactivos y boton de descarga (descarga datos sin filtrar)."""

    st.subheader(titulo)



    if df.empty:

        st.warning("No hay datos disponibles.")

        return



    df_filtrado = df.copy()

    if valores_por_defecto is None:

        valores_por_defecto = {}



    # Filtros dinamicos

    if columnas_filtro:

        cols = st.columns(len(columnas_filtro))

        for i, col_name in enumerate(columnas_filtro):

            if col_name in df_filtrado.columns:

                opciones = ["Todos"] + sorted(

                    [str(x) for x in df_filtrado[col_name].dropna().unique().tolist()]

                )



                # Seleccionar valor por defecto si existe

                default_idx = 0

                if col_name in valores_por_defecto and str(valores_por_defecto[col_name]) in opciones:

                    default_idx = opciones.index(str(valores_por_defecto[col_name]))



                with cols[i]:

                    seleccion = st.selectbox(

                        col_name,

                        opciones,

                        index=default_idx,

                        key=f"{key_prefix}_{col_name}",

                    )

                    if seleccion != "Todos":

                        df_filtrado = df_filtrado[df_filtrado[col_name].astype(str) == seleccion]



    # Metricas rapidas

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Registros (Vista)", f"{len(df_filtrado):,}")

    if "Cota" in df_filtrado.columns:

        try:

            col2.metric("Suma Cota (Vista)", f"{pd.to_numeric(df_filtrado['Cota'], errors='coerce').sum():,.0f}")

        except Exception:

            pass

    elif "Cota Inicial" in df_filtrado.columns:

        try:

            col2.metric("Suma Cota Inicial (Vista)", f"{pd.to_numeric(df_filtrado['Cota Inicial'], errors='coerce').sum():,.0f}")

        except Exception:

            pass

    if "Cota Quemada" in df_filtrado.columns:

        quemadas = (df_filtrado["Cota Quemada"] == "Cota Quemada").sum()

        col3.metric("Cotas Quemadas (Vista)", f"{quemadas:,}")



    # Tabla

    if es_pivot_cotas and col_fecha and col_fila:

        df_mostrar = crear_tabla_dinamica_cotas(df_filtrado, col_fecha, col_fila)

        st.dataframe(df_mostrar, use_container_width=True, height=500)

    elif es_pivot_dias_dvh and col_fila and col_dia:

        df_mostrar = crear_tabla_dias_entrega_dvh(df_filtrado, col_fila, col_dia)

        

        def estilo_celda(val):

            if val == "SI":

                return 'background-color: #bcebc3; color: black'

            elif val == "0":

                return 'background-color: #ffcccc; color: black'

            return ''

        

        st.dataframe(df_mostrar.style.map(estilo_celda), use_container_width=True, height=500)

    elif es_pivot_dias and col_fila and col_dia:
        df_mostrar = crear_tabla_frecuencia_dias(df_filtrado, col_fila, col_dia)
        
        def estilo_celda(val):
            if val == "SI":
                return 'background-color: #bcebc3; color: black'
            elif val == "0":
                return 'background-color: #ffcccc; color: black'
            return ''
        
        st.dataframe(df_mostrar.style.map(estilo_celda), use_container_width=True, height=500)
    elif es_pivot_tamano:
        df_mostrar = crear_tabla_dinamica_tamano(df_filtrado)
        st.dataframe(df_mostrar, use_container_width=True, height=500)
    elif es_pivot_lt_localidad:
        df_mostrar = crear_tabla_dinamica_lt_localidad(df_filtrado)
        st.dataframe(df_mostrar, use_container_width=True, height=500)
    elif es_pivot_ultima_milla:
        df_mostrar = crear_tabla_dinamica_ultima_milla(df_filtrado)
        st.dataframe(df_mostrar, use_container_width=True, height=500)
    else:

        df_mostrar = df_filtrado

        st.dataframe(df_mostrar, use_container_width=True, height=500)



    # Descarga (siempre descarga el DF original completo, sin filtros)

    boton_descarga(df, titulo.replace(" ", "_") + "_Completo", f"dl_{key_prefix}")





# ============================================================

# PAGINAS

# ============================================================



if pagina == "🎯 Resumen":

    st.title("🎯 Resumen de Capacidades Logisticas")

    st.caption("Datos en tiempo real desde OMS PostgreSQL")



    try:

        df_resumen = obtener_resumen_cotas()



        col1, col2, col3 = st.columns(3)

        for _, row in df_resumen.iterrows():

            flujo = row["flujo"]

            total = int(row["total_cota"] or 0)

            acum = int(row["total_acumulada"] or 0)

            quemadas = int(row["cotas_quemadas"] or 0)

            registros = int(row["total_registros"] or 0)

            disponible = total - acum



            if flujo == "DDC":

                with col1:

                    st.markdown("### 📦 DDC")

                    st.metric("Registros", f"{registros:,}")

                    st.metric("Cota Total", f"{total:,}")

                    st.metric("Disponible", f"{disponible:,}")

                    st.metric("Cotas Quemadas", f"{quemadas:,}")

            elif flujo == "DVH":

                with col2:

                    st.markdown("### 🚚 DVH")

                    st.metric("Registros", f"{registros:,}")

                    st.metric("Cota Total", f"{total:,}")

                    st.metric("Disponible", f"{disponible:,}")

                    st.metric("Cotas Quemadas", f"{quemadas:,}")

            elif flujo == "MKP":

                with col3:

                    st.markdown("###  MKP")

                    st.metric("Registros", f"{registros:,}")

                    st.metric("Cota Total", f"{total:,}")

                    st.metric("Disponible", f"{disponible:,}")

                    st.metric("Cotas Quemadas", f"{quemadas:,}")



        # Boton de descarga del reporte completo

        st.divider()

        st.subheader("📥 Descargar Reporte Completo en Excel")

        st.caption("Este archivo incluira TODA la informacion sin filtros (universo completo) para que puedas cruzarla a tu antojo en Excel.")

        if st.button("Generar Reporte Excel Completo", use_container_width=True):

            with st.spinner("Consultando todas las fuentes de datos..."):

                hojas = {

                    "Resumen": df_resumen,

                    "Cotas DDC": obtener_cotas_ddc(),

                    "Cotas DVH": obtener_cotas_dvh(),

                    "Cotas MKP Seller": obtener_cotas_mkp(),

                    "Cota Recepcion DVH": obtener_cota_tamano(),

                    "Cota Courier MKP": obtener_cota_courier_mkp(),

                    "Frecuencia DDC": obtener_frecuencia_ddc(),

                    "Lead Time Sellers": obtener_lead_time_sellers(),

                    "Ultima Milla MKP": obtener_estado_courier_mkp(),

                }

                excel_data = generar_excel(hojas)

                st.download_button(

                    label="📥 Descargar Reporte Completo",

                    data=excel_data,

                    file_name=f"Reporte_Capacidades_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",

                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

                    key="dl_reporte_completo",

                )



        st.divider()

        st.subheader("🔥 Detalle de Cotas Quemadas (Igual a Hoja Resumen en Excel)")

        st.caption("A continuacion se muestra solo el detalle de los proveedores/sellers con la cota quemada. Para ver todo el universo, descarga el Excel o ve a las otras pestanas.")



        tab1, tab2, tab3 = st.tabs(["📦 DDC Quemadas", "🚚 DVH Quemadas", " MKP Quemadas"])



        with tab1:

            df_ddc = obtener_cotas_ddc()

            if not df_ddc.empty:

                quemadas_ddc = df_ddc[

                    (df_ddc["Cota Quemada"] == "Cota Quemada") &

                    (df_ddc["Cota Acumulada"] != 0) &

                    (df_ddc["Filtro Fecha DDC"] == "OK")

                ]

                st.dataframe(quemadas_ddc, use_container_width=True)



        with tab2:

            df_dvh = obtener_cotas_dvh()

            if not df_dvh.empty:

                quemadas_dvh = df_dvh[

                    (df_dvh["Cota Quemada"] == "Cota Quemada") &

                    (df_dvh["Cota Acumulada"] != 0) &

                    (df_dvh["Filtro Fecha DVH"] == "OK")

                ]

                st.dataframe(quemadas_dvh, use_container_width=True)



        with tab3:

            df_mkp = obtener_cotas_mkp()

            if not df_mkp.empty:

                quemadas_mkp = df_mkp[

                    (df_mkp["Cota Quemada"] == "Cota Quemada") &

                    (df_mkp["Cota Acumulada"] != 0) &

                    (df_mkp["Filtro Fecha MKP"] == "OK")

                ]

                st.dataframe(quemadas_mkp, use_container_width=True)



    except Exception as e:

        st.error(f"Error al conectar con la base de datos: {e}")



elif pagina == "📊 Cotas DDC":

    st.title("📊 Cotas DDC (Despacho Directo a Cliente)")

    try:

        df = obtener_cotas_ddc()

        if "Proveedor" in df.columns:

            df.rename(columns={"Proveedor": "Razon Social"}, inplace=True)



        mostrar_tabla_filtrada(

            df, "Cotas DDC", "ddc",

            columnas_filtro=["Razon Social", "Cota Quemada", "Mes", "Filtro Fecha DDC"],

            valores_por_defecto={},

            es_pivot_cotas=True, col_fecha="Fecha Compromiso", col_fila="Razon Social"

        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "📊 Cotas DVH":

    st.title("📊 Cotas DVH (Despacho Vía Hites)")

    try:

        df = obtener_cotas_dvh()

        if "Proveedor" in df.columns:

            df.rename(columns={"Proveedor": "Razon Social"}, inplace=True)



        mostrar_tabla_filtrada(

            df, "Cotas DVH", "dvh",

            columnas_filtro=["Razon Social", "Cota Quemada", "Mes", "Filtro Fecha DVH"],

            valores_por_defecto={},

            es_pivot_cotas=True, col_fecha="Fecha Entrega CD", col_fila="Razon Social"

        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "📊 Cotas MKP Seller":

    st.title("📊 Cotas MKP (Marketplace Sellers)")

    try:

        df = obtener_cotas_mkp()

        # Normalizar nombre de columna por si viene con encoding diferente

        for col in df.columns:

            if "raz" in col.lower() and "social" in col.lower():

                df.rename(columns={col: "Razon Social"}, inplace=True)

                break



        mostrar_tabla_filtrada(

            df, "Cotas MKP Seller", "mkp",

            columnas_filtro=["Razon Social", "Cota Quemada", "Mes", "Filtro Fecha MKP"],

            valores_por_defecto={},

            es_pivot_cotas=True, col_fecha="Fecha Compromiso Inicial", col_fila="Razon Social"

        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "📅 Dia Entrega DVH":

    st.title("📅 Dia Entrega DVH")

    try:

        from queries import obtener_dia_entrega_dvh

        df = obtener_dia_entrega_dvh()



        mostrar_tabla_filtrada(

            df, "Dia Entrega DVH", "dia_entrega_dvh",

            columnas_filtro=["Razon Social"],

            valores_por_defecto={},

            es_pivot_dias_dvh=True, col_fila="Razon Social", col_dia="Dia No Laborable"

        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "📦 Cota Recepcion DVH":

    st.title("📦 Cota Recepcion DVH")

    try:

        df = obtener_cota_tamano()

        # Normalizar nombre de columna Tamano

        for col in df.columns:

            if "tama" in col.lower():

                df.rename(columns={col: "Tamano"}, inplace=True)

                break

        mostrar_tabla_filtrada(

            df, "Cota Recepcion DVH", "tamano",

            columnas_filtro=["Tamano", "Cota Quemada", "Mes"],

            valores_por_defecto={"Cota Quemada": "Cota Quemada"},
            
            es_pivot_tamano=True

        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "🚚 Cota Courier MKP":

    st.title("🚚 Cota Courier MKP")

    try:

        df = obtener_cota_courier_mkp()

        mostrar_tabla_filtrada(

            df, "Cota Courier MKP", "courier_mkp",

            columnas_filtro=["Nombre Fuente Abastecimiento", "Cota Quemada", "Mes"],

            valores_por_defecto={"Cota Quemada": "Cota Quemada"}

        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "⏱ Lead Time SKU VeV":

    st.title("⏱ Lead Time SKU - Venta en Verde")

    st.caption("Esta consulta cruza con AS400 TOPART y puede tardar unos segundos la primera vez.")

    try:

        df = obtener_lead_time_skus()

        # Normalizar nombre de columna Seccion

        for col in df.columns:

            if "secci" in col.lower() or "seccion" in col.lower():

                df.rename(columns={col: "Seccion"}, inplace=True)

                break

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Promedio por Proveedor", "📊 LT > 35 Días", "📊 Prov. Sin Stock", "📊 Inactivos Con Stock", "📄 Base de Datos"])
        
        with tab1:
            st.subheader("Lead Time Promedio por Proveedor Activo")
            st.caption("Filtros aplicados: Tipo='Venta En Verde', Estado Proveedor='Activo', Estado SKU='Habilitado'")
            
            mask1 = (
                (df['Tipo'] == 'Venta En Verde') &
                (df['Estado Proveedor'] == 'Activo') &
                (df['Estado SKU'] == 'Habilitado')
            )
            df_pivot_1 = df[mask1].copy()
            
            if not df_pivot_1.empty:
                df_pivot_1['LT SKU'] = pd.to_numeric(df_pivot_1['LT SKU'], errors='coerce').fillna(0)
                pivot_1 = df_pivot_1.groupby('Razon Social').agg(
                    Cantidad_SKUs=('SKU', 'count'),
                    Promedio_LT_SKU=('LT SKU', 'mean')
                ).reset_index()
                
                pivot_1.rename(columns={
                    'Cantidad_SKUs': 'Cantidad de SKUs',
                    'Promedio_LT_SKU': 'Promedio LT SKU'
                }, inplace=True)
                
                pivot_1['Promedio LT SKU'] = pivot_1['Promedio LT SKU'].round(1)
                pivot_1 = pivot_1.sort_values('Cantidad de SKUs', ascending=False)
                
                st.dataframe(pivot_1, use_container_width=True, height=500)
                boton_descarga(pivot_1, "LT_Promedio_Proveedor", "dl_lt_prom_prov")
            else:
                st.warning("No hay datos que coincidan con los filtros para esta tabla.")
                
        with tab2:
            st.subheader("Proveedores Activos con LT > 35 Días")
            st.caption("Filtros aplicados: Tipo='Venta En Verde', Estado Proveedor='Activo', Estado SKU='Habilitado', LT Mayor 35 Dias='LT Mayor a 35 Dias'")
            
            mask2 = (
                (df['Tipo'] == 'Venta En Verde') &
                (df['Estado Proveedor'] == 'Activo') &
                (df['Estado SKU'] == 'Habilitado') &
                (df['LT Mayor 35 Dias'] == 'LT Mayor a 35 Dias')
            )
            df_pivot_2 = df[mask2].copy()
            
            if not df_pivot_2.empty:
                df_pivot_2['LT SKU'] = pd.to_numeric(df_pivot_2['LT SKU'], errors='coerce').fillna(0)
                pivot_2 = df_pivot_2.groupby('Razon Social').agg(
                    Cantidad_SKUs=('SKU', 'count'),
                    Promedio_LT_SKU=('LT SKU', 'mean')
                ).reset_index()
                
                pivot_2.rename(columns={
                    'Cantidad_SKUs': 'Cantidad de SKUs',
                    'Promedio_LT_SKU': 'Promedio LT SKU'
                }, inplace=True)
                
                pivot_2['Promedio LT SKU'] = pivot_2['Promedio LT SKU'].round(1)
                pivot_2 = pivot_2.sort_values('Cantidad de SKUs', ascending=False)
                
                st.dataframe(pivot_2, use_container_width=True, height=500)
                boton_descarga(pivot_2, "LT_Mayor_35_Dias", "dl_lt_35_dias")
            else:
                st.warning("No hay datos que coincidan con los filtros para esta tabla (¡Ninguno superó los 35 días!).")
                
        with tab3:
            st.subheader("Proveedores Activos con todos sus SKU's sin Stock")
            st.caption("Filtros aplicados: Tipo='Venta En Verde', Estado Proveedor='Activo', Estado SKU='Habilitado', Proveedor Con/Sin Stock='Proveedor Sin Stock'")
            
            mask3 = (
                (df['Tipo'] == 'Venta En Verde') &
                (df['Estado Proveedor'] == 'Activo') &
                (df['Estado SKU'] == 'Habilitado') &
                (df['Proveedor Con/Sin Stock'] == 'Proveedor Sin Stock')
            )
            df_pivot_3 = df[mask3].copy()
            
            if not df_pivot_3.empty:
                df_pivot_3['LT SKU'] = pd.to_numeric(df_pivot_3['LT SKU'], errors='coerce').fillna(0)
                pivot_3 = df_pivot_3.groupby('Razon Social').agg(
                    Cantidad_SKUs=('SKU', 'count'),
                    Promedio_LT_SKU=('LT SKU', 'mean')
                ).reset_index()
                
                pivot_3.rename(columns={
                    'Cantidad_SKUs': 'Cantidad de SKUs',
                    'Promedio_LT_SKU': 'Promedio LT SKU'
                }, inplace=True)
                
                pivot_3['Promedio LT SKU'] = pivot_3['Promedio LT SKU'].round(1)
                pivot_3 = pivot_3.sort_values('Cantidad de SKUs', ascending=False)
                
                st.dataframe(pivot_3, use_container_width=True, height=500)
                boton_descarga(pivot_3, "Prov_Sin_Stock", "dl_prov_sin_stock")
            else:
                st.warning("No hay datos que coincidan con los filtros para esta tabla.")
                
        with tab4:
            st.subheader("Proveedores Con productos Inactivos con Stock")
            st.caption("Filtros aplicados: Estado Proveedor='Activo', Estado SKU='Deshabilitado', Proveedor SKU Inhabilitado Con/Sin Stock='Proveedor Con Stock'")
            
            mask4 = (
                (df['Estado Proveedor'] == 'Activo') &
                (df['Estado SKU'] == 'Deshabilitado') &
                (df['Proveedor SKU Inhabilitado Con/Sin Stock'] == 'Proveedor Con Stock')
            )
            df_pivot_4 = df[mask4].copy()
            
            if not df_pivot_4.empty:
                df_pivot_4['LT SKU'] = pd.to_numeric(df_pivot_4['LT SKU'], errors='coerce').fillna(0)
                pivot_4 = df_pivot_4.groupby('Razon Social').agg(
                    Cantidad_SKUs=('SKU', 'count'),
                    Promedio_LT_SKU=('LT SKU', 'mean')
                ).reset_index()
                
                pivot_4.rename(columns={
                    'Cantidad_SKUs': 'Cantidad de SKUs',
                    'Promedio_LT_SKU': 'Promedio LT SKU'
                }, inplace=True)
                
                pivot_4['Promedio LT SKU'] = pivot_4['Promedio LT SKU'].round(1)
                pivot_4 = pivot_4.sort_values('Cantidad de SKUs', ascending=False)
                
                st.dataframe(pivot_4, use_container_width=True, height=500)
                boton_descarga(pivot_4, "Inactivos_Con_Stock", "dl_inactivos_con_stock")
            else:
                st.warning("No hay datos que coincidan con los filtros para esta tabla.")
                
        with tab5:
            mostrar_tabla_filtrada(
                df, "Base Completa: Lead Time SKU VeV", "lt_sku",
                columnas_filtro=["Estado Proveedor", "Estado Stock", "LT Mayor 35 Dias", "Tipo", "Departamento", "Seccion", "Product Manager"]
            )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "📅 Frecuencia DDC":

    st.title("📅 Frecuencia de Proveedores DDC")

    try:

        df = obtener_frecuencia_ddc()
        # Normalizar nombre de columna Region si no existe explícitamente
        if "Region" not in df.columns:
            for col in df.columns:
                if "regi" in col.lower() and "id" not in col.lower():
                    df.rename(columns={col: "Region"}, inplace=True)
                    break
        
        # Mapear 1 a 'SI' y NaN a '0'
        dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        for dia in dias:
            if dia in df.columns:
                df[dia] = df[dia].apply(lambda x: "SI" if pd.notnull(x) and x == 1 else "0")
        
        mostrar_tabla_filtrada(
            df, "Frecuencia DDC", "frec_ddc",
            columnas_filtro=["Proveedor", "Region", "Comuna"],
            valores_por_defecto={},
            es_pivot_dias_dvh=True
        )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "🏪 Lead Time Sellers":

    st.title("🏪 Lead Time Sellers MKP")

    try:
        df = obtener_lead_time_sellers()
        
        # Filtro obligatorio
        if 'flag_activo' in df.columns:
            df = df[df['flag_activo'] == 'S']
            
        mostrar_tabla_filtrada(
            df, "Lead Time Sellers", "lt_sellers",
            columnas_filtro=["Seller"]
        )
    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "📍 LT Localidad Sellers":

    st.title("📍 LeadTime por Localidad Destino - Sellers MKP")

    try:
        df = obtener_leadtime_localidad_sellers()
        tab1, tab2 = st.tabs(["📊 Vista Tabular", "📄 Base de Datos"])
        
        with tab1:
            mostrar_tabla_filtrada(
                df, "LT Localidad Sellers (Tabular)", "lt_loc_tab",
                columnas_filtro=["Seller", "Region Destino"],
                es_pivot_lt_localidad=True
            )
            
        with tab2:
            mostrar_tabla_filtrada(
                df, "LT Localidad Sellers (Crudo)", "lt_loc_raw",
                columnas_filtro=["Seller", "Region Destino"]
            )

    except Exception as e:

        st.error(f"Error: {e}")



elif pagina == "🛵 Ultima Milla MKP":

    st.title("🛵 Ultima Milla MKP - Estado Courier")

    try:
        df = obtener_estado_courier_mkp()
        
        # Filtro obligatorio R = 1
        if 'R' in df.columns:
            df = df[df['R'] == 1]
            
        # Normalizar nombre de columna Region si no existe explícitamente
        if "Region" not in df.columns:
            for col in df.columns:
                if "regi" in col.lower() and "id" not in col.lower() and col != "Region Destino":
                    df.rename(columns={col: "Region"}, inplace=True)
                    break
        
        tab1, tab2 = st.tabs(["📊 Vista Agrupada", "📄 Base de Datos"])
        
        with tab1:
            mostrar_tabla_filtrada(
                df, "Ultima Milla MKP (Pivot)", "um_mkp_pivot",
                columnas_filtro=["Courier", "Region", "Flag Fuente Abastecimiento"],
                es_pivot_ultima_milla=True
            )
            
        with tab2:
            mostrar_tabla_filtrada(
                df, "Ultima Milla MKP (Crudo)", "ult_milla",
                columnas_filtro=["Courier", "Region", "Flag Fuente Abastecimiento"]
            )
            
    except Exception as e:

        st.error(f"Error: {e}")





# ============================================================

# Footer

# ============================================================

st.sidebar.divider()

st.sidebar.caption("🔒 Conexiones en modo solo lectura")

st.sidebar.caption("📡 PostgreSQL OMS | AS400 sistemdb")

st.sidebar.caption("Datos actualizados cada hora (cache)")

