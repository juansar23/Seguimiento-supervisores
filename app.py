import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Asignación Supervisores - UT", layout="wide")

st.title("👨‍💼 Asignación Automática a Supervisores")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()

    # ================================
    # VALIDAR COLUMNAS (Sin TECNICOS_INTEGRALES)
    # ================================
    columnas_necesarias = ["RANGO_EDAD", "SUBCATEGORIA", "DEUDA_TOTAL"]
    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(f"❌ Falta la columna necesaria: {col}")
            st.stop()

    # Limpieza de deuda
    df["_deuda_num"] = (
        df["DEUDA_TOTAL"].astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.strip()
    )
    df["_deuda_num"] = pd.to_numeric(df["_deuda_num"], errors="coerce").fillna(0)

    # ================================
    # SIDEBAR - CONFIGURACIÓN
    # ================================
    st.sidebar.header("🎯 Parámetros")

    supervisores_base = [
        "FAVIO ERNESTO VASQUEZ ROMERO",
        "DEGUIN ZOCRATE DEGUIN ZOCRATE",
        "YESID RAFAEL REALES MORENO",
        "ABILIO SEGUNDO ARAUJO ARIÑO",
        "JAVIER DAVID GOMEZ BARRIOS"
    ]

    sub_sel = st.sidebar.multiselect("Subcategoría", sorted(df["SUBCATEGORIA"].unique()), default=df["SUBCATEGORIA"].unique())
    deuda_minima = st.sidebar.number_input("Deudas mayores a:", min_value=0, value=0)

    st.sidebar.divider()
    st.sidebar.subheader("👥 Supervisores Activos")
    
    # Permitir elegir a quiénes se les va a asignar hoy
    sups_activos = st.sidebar.multiselect("Asignar a:", supervisores_base, default=supervisores_base)

    # ================================
    # PROCESO DE ASIGNACIÓN DINÁMICA
    # ================================
    
    # 1. Filtrar la base general por criterios
    df_pool = df[
        (df["SUBCATEGORIA"].isin(sub_sel)) &
        (df["_deuda_num"] >= deuda_minima)
    ].copy()

    # 2. Ordenar por deuda (para dar las más importantes)
    df_pool = df_pool.sort_values(by="_deuda_num", ascending=False)

    # 3. CREAR LA COLUMNA DE SUPERVISORES Y ASIGNAR
    # Calculamos cuántas pólizas necesitamos en total (8 por cada supervisor activo)
    total_necesario = len(sups_activos) * 8
    df_asignable = df_pool.head(total_necesario).copy()

    if not df_asignable.empty and sups_activos:
        # Repartimos los nombres de los supervisores en la nueva columna
        lista_asignacion = []
        for s in sups_activos:
            lista_asignacion.extend([s] * 8)
        
        # Ajustamos al tamaño real por si hay menos de 40 pólizas disponibles
        lista_asignacion = lista_asignacion[:len(df_asignable)]
        
        df_asignable["SUPERVISOR_ASIGNADO"] = lista_asignacion
    else:
        df_asignable["SUPERVISOR_ASIGNADO"] = None

    # ================================
    # VISTA Y DESCARGA
    # ================================
    tab1, tab2 = st.tabs(["📋 Lista de Asignación", "📊 Resumen"])

    with tab1:
        if sups_activos:
            st.success(f"Se han repartido las mejores pólizas entre {len(sups_activos)} supervisores.")
            st.dataframe(df_asignable, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_export = df_asignable.drop(columns=["_deuda_num"], errors="ignore")
                df_export.to_excel(writer, index=False, sheet_name="Asignacion")
            
            output.seek(0)
            st.download_button("📥 Descargar Reporte", output, "Asignacion_Supervisores.xlsx")
        else:
            st.warning("Selecciona al menos un supervisor en el panel de la izquierda.")

    with tab2:
        if not df_asignable.empty:
            resumen = df_asignable["SUPERVISOR_ASIGNADO"].value_counts().reset_index()
            resumen.columns = ["Supervisor", "Cantidad"]
            st.plotly_chart(px.bar(resumen, x="
