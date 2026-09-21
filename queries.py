# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st

DATOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_cache")

# Solo traduccion de dias y meses al espanol (para filtros y pivot headers)
MESES_EN_A_ES = {
    'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
    'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
    'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre',
    'Jan': 'Enero', 'Feb': 'Febrero', 'Mar': 'Marzo', 'Apr': 'Abril',
    'Jun': 'Junio', 'Jul': 'Julio', 'Aug': 'Agosto', 'Sep': 'Septiembre',
    'Oct': 'Octubre', 'Nov': 'Noviembre', 'Dec': 'Diciembre'
}

DIAS_EN_A_ES = {
    'Mon': 'Lunes', 'Tue': 'Martes', 'Wed': 'Miercoles', 'Thu': 'Jueves',
    'Fri': 'Viernes', 'Sat': 'Sabado', 'Sun': 'Domingo',
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles', 'Thursday': 'Jueves',
    'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
}


def _traducir_dia_mes(df: pd.DataFrame) -> pd.DataFrame:
    """Solo traduce columnas Dia y Mes al espanol. No toca las fechas."""
    df_res = df.copy()
    if "Mes" in df_res.columns:
        df_res["Mes"] = df_res["Mes"].astype(str).str.strip().map(lambda x: MESES_EN_A_ES.get(x, x))
    if "Dia" in df_res.columns:
        df_res["Dia"] = df_res["Dia"].astype(str).str.strip().map(lambda x: DIAS_EN_A_ES.get(x, x))
    return df_res


def _cargar(nombre: str) -> pd.DataFrame:
    """Carga un dataframe desde cache local."""
    path = os.path.join(DATOS_DIR, f"{nombre}.parquet")
    if os.path.exists(path):
        try:
            df = pd.read_parquet(path)
            if not df.empty:
                df = _traducir_dia_mes(df)
            return df
        except Exception as e:
            print(f"Error loading {nombre}.parquet: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def obtener_fecha_actualizacion() -> str:
    path = os.path.join(DATOS_DIR, "ultima_actualizacion.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Nunca"

# Envolvemos las funciones con st.cache_data pero con un TTL corto 
# para que Streamlit detecte los archivos nuevos cuando el actualizador los pise.
@st.cache_data(ttl=60)
def obtener_cotas_ddc(): return _cargar("cotas_ddc")

@st.cache_data(ttl=60)
def obtener_cotas_dvh(): return _cargar("cotas_dvh")

@st.cache_data(ttl=60)
def obtener_cotas_mkp(): return _cargar("cotas_mkp")

@st.cache_data(ttl=60)
def obtener_dia_entrega_dvh(): return _cargar("dia_entrega_dvh")

@st.cache_data(ttl=60)
def obtener_cota_tamano(): return _cargar("cota_tamano")

@st.cache_data(ttl=60)
def obtener_cota_courier_mkp(): return _cargar("cota_courier_mkp")

@st.cache_data(ttl=60)
def obtener_lead_time_skus(): return _cargar("lead_time_skus")

@st.cache_data(ttl=60)
def obtener_frecuencia_ddc(): return _cargar("frecuencia_ddc")

@st.cache_data(ttl=60)
def obtener_lead_time_sellers(): return _cargar("lead_time_sellers")

@st.cache_data(ttl=60)
def obtener_leadtime_localidad_sellers(): return _cargar("leadtime_localidad_sellers")

@st.cache_data(ttl=60)
def obtener_estado_courier_mkp(): return _cargar("estado_courier_mkp")

@st.cache_data(ttl=60)
def obtener_resumen_cotas(): return _cargar("resumen_cotas")
