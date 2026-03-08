import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Dashboard Ejecutivo UT - Supervisores", layout="wide")

st.title("📊 Dashboard Ejecutivo - Asignación Supervisores")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()

    # ================================
    # VALIDAR COLUMNAS Y LIMPIEZA
    # ================================
    columnas_necesarias = ["RANGO_EDAD", "SUBCATEGORIA", "DEUDA_TOTAL"]
    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(f"❌ Falta la columna necesaria: {col}")
            st.stop()

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
    sups_activos = st.sidebar.multiselect("Supervisores Activos", supervisores_base, default=supervisores_base)

    # ================================
    # PROCESO DE ASIGNACIÓN
    # ================================
    df_pool = df[
        (df["SUBCATEGORIA"].isin(sub_sel)) & 
        (df["_deuda_num"] >= deuda_minima)
    ].copy().sort_values(by="_deuda_num", ascending=False)

    if not df_pool.empty and sups_activos:
        total_a_asignar = len(sups_activos) * 8
        df_final = df_pool.head(total_a_asignar).copy()
        
        lista_nombres = []
        for s in sups_activos:
            lista_nombres.extend([s] * 8)
        
        df_final["SUPERVISOR_ASIGNADO"] = lista_nombres[:len(df_final)]
    else:
        df_final = pd.DataFrame()

    # ================================
    # PESTAÑAS (ESTILO DASHBOARD)
    # ================================
    tab1, tab2 = st.tabs(["📋 Lista de Asignación", "📊 Resumen Visual"])

    with tab1:
        if not df_final.empty:
            st.success(f"Se han asignado un máximo de 8 pólizas a {len(sups_activos)} supervisores.")
            st.dataframe(df_final, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_final.drop(columns=["_deuda_num"]).to_excel(writer, index=False, sheet_name="Asignacion")
            
            output.seek(0)
            st.download_button("📥 Descargar Reporte", output, "Asignacion_Supervisores.xlsx")

    with tab2:
        if not df_final.empty:
            # --- MÉTRICAS SUPERIORES ---
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Pólizas", len(df_final))
            m2.metric("Total Deuda", f"$ {df_final['_deuda_num'].sum():,.0f}")
            m3.metric("Supervisores Activos", df_final["SUPERVISOR_ASIGNADO"].nunique())

            st.divider()

            # --- TOP 10 (En este caso supervisores con más deuda asignada) ---
            st.subheader("🏆 Top Supervisores por Deuda Asignada")
            top_sup = df_final.groupby("SUPERVISOR_ASIGNADO")["_deuda_num"].sum().sort_values(ascending=False).reset_index()
            top_sup.columns = ["Supervisor", "Total Deuda"]
            top_sup["Total Deuda"] = top_sup["Total Deuda"].apply(lambda x: f"$ {x:,.0f}")
            st.table(top_sup)

            # --- GRÁFICO DE BARRAS (Rango Edad) ---
            st.subheader("📊 Pólizas por Rango de Edad")
            conteo_edad = df_final["RANGO_EDAD"].value_counts().reset_index()
            conteo_edad.columns = ["Rango Edad", "Cantidad"]
            fig_bar = px.bar(conteo_edad, x="Rango Edad", y="Cantidad", text_auto=True, color_discrete_sequence=['#87CEEB'])
            fig_bar.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)

            # --- GRÁFICO DE PASTEL (Subcategoría) ---
            st.subheader("🥧 Distribución por Subcategoría")
            conteo_sub = df_final["SUBCATEGORIA"].value_counts().reset_index()
            conteo_sub.columns = ["Subcategoría", "Cantidad"]
            fig_pie = px.pie(conteo_sub, names="Subcategoría", values="Cantidad", hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("No hay datos para mostrar en el dashboard.")
