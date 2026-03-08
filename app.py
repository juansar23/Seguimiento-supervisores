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
    # VALIDAR COLUMNAS
    # ================================
    columnas_necesarias = ["RANGO_EDAD", "SUBCATEGORIA", "DEUDA_TOTAL"]
    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(f"❌ Falta la columna necesaria: {col}")
            st.stop()

    # Limpieza de deuda para ordenamiento
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

    sub_opciones = sorted(df["SUBCATEGORIA"].unique())
    sub_sel = st.sidebar.multiselect("Subcategoría", sub_opciones, default=sub_opciones)
    deuda_minima = st.sidebar.number_input("Deudas mayores a:", min_value=0, value=0)

    st.sidebar.divider()
    st.sidebar.subheader("👥 Supervisores Activos")
    sups_activos = st.sidebar.multiselect("Asignar a:", supervisores_base, default=supervisores_base)

    # ================================
    # PROCESO DE ASIGNACIÓN
    # ================================
    df_pool = df[
        (df["SUBCATEGORIA"].isin(sub_sel)) &
        (df["_deuda_num"] >= deuda_minima)
    ].copy()

    # Ordenar para entregar las de mayor deuda
    df_pool = df_pool.sort_values(by="_deuda_num", ascending=False)

    if not df_pool.empty and sups_activos:
        total_a_asignar = len(sups_activos) * 8
        df_asignable = df_pool.head(total_a_asignar).copy()

        # Generar lista de nombres repetidos 8 veces cada uno
        lista_nombres = []
        for s in sups_activos:
            lista_nombres.extend([s] * 8)
        
        # Recortar la lista si hay menos pólizas que el cupo total
        lista_nombres = lista_nombres[:len(df_asignable)]
        df_asignable["SUPERVISOR_ASIGNADO"] = lista_nombres
    else:
        df_asignable = pd.DataFrame()

    # ================================
    # VISTA Y DESCARGA
    # ================================
    tab1, tab2 = st.tabs(["📋 Lista de Asignación", "📊 Resumen"])

    with tab1:
        if not df_asignable.empty:
            st.success(f"Se han repartido {len(df_asignable)} pólizas entre los supervisores seleccionados.")
            st.dataframe(df_asignable, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_export = df_asignable.drop(columns=["_deuda_num"], errors="ignore")
                df_export.to_excel(writer, index=False, sheet_name="Asignacion")
            
            output.seek(0)
            st.download_button("📥 Descargar Reporte Excel", output, "Asignacion_Supervisores.xlsx")
        else:
            st.warning("No hay datos que coincidan con los filtros o no has seleccionado supervisores.")

    with tab2:
        if not df_asignable.empty:
            resumen = df_asignable["SUPERVISOR_ASIGNADO"].value_counts().reset_index()
            resumen.columns = ["Supervisor", "Cantidad"]
            
            fig = px.bar(
                resumen, 
                x="Supervisor", 
                y="Cantidad", 
                color="Supervisor",
                title="Pólizas Asignadas por Supervisor",
                text_auto=True
            )
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👆 Sube el archivo Excel para procesar la asignación.")
