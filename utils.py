import io
import re
import pandas as pd
import streamlit as st

def generar_excel(hojas: dict) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for nombre_hoja, df in hojas.items():
            nombre_seguro = re.sub(r'[\\/\?\*\[\]\:]', '_', nombre_hoja)
            nombre_seguro = nombre_seguro[:31]
            df.to_excel(writer, sheet_name=nombre_seguro, index=False)
    return output.getvalue()

def crear_tabla_dinamica_tamano(df: pd.DataFrame) -> pd.DataFrame:
    df_pivot = df.copy()
    if 'Fecha_Display' not in df_pivot.columns or 'Dia' not in df_pivot.columns:
        return df_pivot
    
    df_pivot['Fecha_Dia'] = df_pivot['Fecha_Display'] + ' ' + df_pivot['Dia']
    df_pivot['Cota'] = pd.to_numeric(df_pivot['Cota'], errors='coerce').fillna(0)
    df_pivot['Consumo'] = pd.to_numeric(df_pivot['Consumo'], errors='coerce').fillna(0)
    df_pivot['% Consumido'] = pd.to_numeric(df_pivot['% Consumido'], errors='coerce').fillna(0)
    
    pivot = pd.pivot_table(
        df_pivot, 
        values=['Cota', 'Consumo', '% Consumido'],
        index=['Razon Social'],
        columns=['Fecha_Dia', 'Tamano'],
        aggfunc='sum',
        fill_value=0
    )
    
    if pivot.empty:
        return df_pivot
    
    pivot.columns = pivot.columns.reorder_levels([1, 2, 0])
    pivot = pivot.sort_index(axis=1, level=[0, 1])
    
    for fecha_dia in pivot.columns.levels[0]:
        tamanos = [t for t in pivot.columns.levels[1] if (fecha_dia, t) in pivot.columns]
        cota_total = pivot.loc[:, (fecha_dia, tamanos, 'Cota')].sum(axis=1)
        consumo_total = pivot.loc[:, (fecha_dia, tamanos, 'Consumo')].sum(axis=1)
        
        pivot[(fecha_dia, 'Total', 'Total Cota')] = cota_total
        pivot[(fecha_dia, 'Total', 'Total Consumo')] = consumo_total
        
        pct_total = (consumo_total / cota_total * 100).fillna(0).round(1)
        pivot[(fecha_dia, 'Total', 'Total % Consumido')] = pct_total
    
    pivot = pivot.sort_index(axis=1)
    return pivot.reset_index()

def crear_tabla_dinamica_lt_localidad(df: pd.DataFrame) -> pd.DataFrame:
    df_pivot = df.copy()
    columnas_agrupacion = ['ID Seller center', 'Seller', 'Region Destino', 'ID Localidad', 'Localidad Destino', 'LeadTime Seller', 'LeadTime Courier']
    for col in columnas_agrupacion:
        if col not in df_pivot.columns:
            return df_pivot
            
    df_pivot['ID Seller center'] = df_pivot['ID Seller center'].fillna("N/A")
    df_pivot['LeadTime Seller'] = pd.to_numeric(df_pivot['LeadTime Seller'], errors='coerce').fillna(0).astype(int)
    df_pivot['LeadTime Courier'] = pd.to_numeric(df_pivot['LeadTime Courier'], errors='coerce').fillna(0).astype(int)
    
    if 'id_legacy' in df_pivot.columns:
        df_pivot['id_legacy'] = pd.to_numeric(df_pivot['id_legacy'], errors='coerce').fillna(0)
        pivot = df_pivot.groupby(columnas_agrupacion, dropna=False).agg(Suma_id_legacy=('id_legacy', 'sum')).reset_index()
        pivot.rename(columns={'Suma_id_legacy': 'Suma de id_legacy'}, inplace=True)
    else:
        pivot = df_pivot.groupby(columnas_agrupacion, dropna=False).size().reset_index(name='Conteo')
        
    pivot = pivot.sort_values(by=['Seller', 'Region Destino', 'ID Localidad'], ascending=[True, True, True])
    pivot['ID Seller center'] = pivot['ID Seller center'].replace("N/A", None)
    return pivot

def crear_tabla_dinamica_ultima_milla(df: pd.DataFrame) -> pd.DataFrame:
    if 'Courier' not in df.columns or 'FA' not in df.columns or 'R' not in df.columns:
        return df
    
    df_pivot = df.copy()
    df_pivot['FA'] = pd.to_numeric(df_pivot['FA'], errors='coerce').fillna(0)
    df_pivot['R'] = pd.to_numeric(df_pivot['R'], errors='coerce').fillna(0)
    
    pivot = df_pivot.groupby('Courier', dropna=False).agg(FA_sum=('FA', 'sum'), R_sum=('R', 'sum')).reset_index()
    pivot.rename(columns={'Courier': 'Nombre Courier', 'FA_sum': 'Fuente de Abastecimiento Activa', 'R_sum': 'Rutas Activas'}, inplace=True)
    pivot = pivot.sort_values(by='Nombre Courier', ascending=True)
    return pivot

def mostrar_tabla_filtrada(df: pd.DataFrame, titulo: str, key_prefix: str,
                           columnas_filtro: list = None, valores_por_defecto: dict = None,
                           es_pivot_cotas: bool = False, col_fecha: str = None, col_fila: str = None,
                           es_pivot_dias: bool = False, col_dia: str = None,
                           es_pivot_dias_dvh: bool = False, es_pivot_tamano: bool = False,
                           es_pivot_lt_localidad: bool = False, es_pivot_ultima_milla: bool = False):
    st.subheader(titulo)
    if df.empty:
        st.warning("No hay datos disponibles.")
        return
        
    if columnas_filtro:
        columnas_st = st.columns(len(columnas_filtro))
        filtros = {}
        for idx, col in enumerate(columnas_filtro):
            if col not in df.columns:
                continue
            with columnas_st[idx]:
                opciones = ["(Todos)"] + sorted(list(df[col].dropna().unique()))
                val_defecto = "(Todos)"
                if valores_por_defecto and col in valores_por_defecto:
                    val_defecto = valores_por_defecto[col]
                if val_defecto not in opciones:
                    val_defecto = "(Todos)"
                
                seleccion = st.selectbox(f"Filtrar por {col}", opciones, 
                                         index=opciones.index(val_defecto), 
                                         key=f"{key_prefix}_filtro_{col}")
                if seleccion != "(Todos)":
                    filtros[col] = seleccion
                    
        df_filtrado = df.copy()
        for col, val in filtros.items():
            df_filtrado = df_filtrado[df_filtrado[col] == val]
    else:
        df_filtrado = df.copy()

    st.write(f"**Registros encontrados:** {len(df_filtrado)}")
    
    # Renderizado y pivoteos
    if es_pivot_cotas and col_fecha and col_fila:
        df_mostrar = pd.pivot_table(
            df_filtrado, 
            values=['Cota', 'Consumo', '% Consumido'],
            index=[col_fila],
            columns=[col_fecha, 'Dia'],
            aggfunc='sum',
            fill_value=0
        )
        if not df_mostrar.empty:
            df_mostrar.columns = df_mostrar.columns.reorder_levels([1, 2, 0])
            df_mostrar = df_mostrar.sort_index(axis=1, level=[0, 1])
        st.dataframe(df_mostrar, use_container_width=True, height=500)
        
    elif es_pivot_dias and col_dia and col_fila:
        if 'Lead Time (dias)' in df_filtrado.columns:
            val_col = 'Lead Time (dias)'
        elif 'Lead Time' in df_filtrado.columns:
            val_col = 'Lead Time'
        else:
            val_col = None
            
        if val_col:
            df_mostrar = pd.pivot_table(
                df_filtrado,
                values=val_col,
                index=[col_fila, 'Localidad'],
                columns=[col_dia],
                aggfunc='mean'
            ).round(1)
            st.dataframe(df_mostrar, use_container_width=True, height=500)
        else:
            st.dataframe(df_filtrado, use_container_width=True, height=500)
            
    elif es_pivot_dias_dvh:
        df_mostrar = df_filtrado
        def estilo_celda(val):
            if val == "SI": return 'background-color: #bcebc3; color: black'
            elif val == "0": return 'background-color: #ffcccc; color: black'
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

    # Boton descarga CSV (como fallback para Excel o para un set especifico)
    if not df_filtrado.empty:
        csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Descargar datos CSV",
            data=csv,
            file_name=f"{key_prefix}_datos.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl_csv"
        )
