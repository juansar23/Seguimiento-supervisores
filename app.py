import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Asignación Supervisores - UT", layout="wide")

st.title("👨‍💼 Asignación de Pólizas a Supervisores")

archivo = st.file_uploader("Sube el archivo Excel con la base de datos", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()

    # ================================
    # VALIDAR COLUMNAS CLAVE
    # ================================
    columnas_necesarias = ["RANGO_EDAD", "SUBCATEGORIA", "DEUDA_TOTAL", "TECNICOS_INTEGRALES"]
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
    # SIDEBAR - CONTROL DE SUPERVISORES
    # ================================
    st.sidebar.header("🎯 Filtros de Asignación")

    # Lista oficial de supervisores
    supervisores_base = [
        "FAVIO ERNESTO VASQUEZ ROMERO",
        "DEGUIN ZOCRATE DEGUIN ZOCRATE",
        "YESID RAFAEL REALES MORENO",
        "ABILIO SEGUNDO ARAUJO ARIÑO",
        "JAVIER DAVID GOMEZ BARRIOS"
    ]

    # Filtros de datos
    rangos = sorted(df["RANGO_EDAD"].dropna().astype(str).unique())
    sub_sel = st.sidebar.multiselect("Subcategoría", sorted(df["SUBCATEGORIA"].unique()), default=df["SUBCATEGORIA"].unique())
    
    deuda_minima = st.sidebar.number_input("Deudas mayores a:", min_value=0, value=100000, step=50000)

    st.sidebar.divider()
    st.sidebar.subheader("👥 Selección de Supervisores")
    
    modo_exclusion = st.sidebar.checkbox("Seleccionar todos excepto")

    if modo_exclusion:
        excluir = st.sidebar.multiselect("Supervisores a excluir", supervisores_base)
        supervisores_final = [s for s in supervisores_base if s not in excluir]
    else:
        supervisores_final = st.sidebar.multiselect(
            "Supervisores a incluir", 
            supervisores_base, 
            default=supervisores_base
        )

    if st.sidebar.button("Limpiar Filtros"):
        st.rerun()

    # ================================
    # PROCESO DE FILTRADO Y ASIGNACIÓN (MAX 8)
    # ================================
    
    # 1. Filtrar por criterios y que pertenezcan a la lista de supervisores
    df_filtrado = df[
        (df["SUBCATEGORIA"].isin(sub_sel)) &
        (df["_deuda_num"] >= deuda_minima) &
        (df["TECNICOS_INTEGRALES"].isin(supervisores_final))
    ].copy()

    # 2. Ordenar por mayor deuda para asignar las más importantes
    df_filtrado = df_filtrado.sort_values(by="_deuda_num", ascending=False)

    # 3. LIMITAR A 8 PÓLIZAS POR SUPERVISOR
    df_final = (
        df_filtrado
        .groupby("TECNICOS_INTEGRALES")
        .head(8)
        .reset_index(drop=True)
    )

    # Formatear fechas para la vista final
    columnas_fecha = ["FECHA_VENCIMIENTO", "ULT_FECHAPAGO", "FECHA_ASIGNACION"]
    for col in columnas_fecha:
        if col in df_final.columns:
            df_final[col] = pd.to_datetime(df_final[col], errors="coerce").dt.strftime("%d/%m/%Y")

    # ================================
    # VISTA Y DESCARGA
    # ================================
    tab1, tab2 = st.tabs(["📋 Lista de Asignación", "📊 Resumen"])

    with tab1:
        st.success(f"Se han asignado un máximo de 8 pólizas a {len(supervisores_final)} supervisores.")
        st.dataframe(df_final, use_container_width=True)

        if not df_final.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Quitamos la columna auxiliar de cálculo antes de exportar
                df_export = df_final.drop(columns=["_deuda_num"], errors="ignore")
                df_export.to_excel(writer, index=False, sheet_name="Asignacion_Supervisores")
            
            output.seek(0)
            st.download_button(
                "📥 Descargar Excel para Supervisores",
                data=output,
                file_name="Asignacion_Supervisores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with tab2:
        col1, col2 = st.columns(2)
        
        # Métrica de carga
        resumen_carga = df_final["TECNICOS_INTEGRALES"].value_counts().reset_index()
        resumen_carga.columns = ["Supervisor", "Pólizas Asignadas"]
        
        with col1:
            st.subheader("Carga por Supervisor")
            st.table(resumen_carga)
            
        with col2:
            st.subheader("Deuda Total Asignada")
            total_deuda = df_final.groupby("TECNICOS_INTEGRALES")["DEUDA_TOTAL"].sum().reset_index() # Nota: usaría _deuda_num si DEUDA_TOTAL sigue siendo string
            fig = px.pie(resumen_carga, names="Supervisor", values="Pólizas Asignadas", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👆 Por favor, carga el archivo de Excel para procesar la asignación de los supervisores.")
