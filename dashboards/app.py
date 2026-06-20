"""
Dashboard interactivo NHANES - Evaluación Parcial N°3
Asignatura: Programación para la Ciencia de Datos (SCY1101)
Rol 2: Visualización
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyreadstat

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NHANES Health Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f, #2d6a9f);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value { font-size: 2.2rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; opacity: 0.85; }
    .audience-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .badge-exec { background: #1e3a5f; color: white; }
    .badge-tech { background: #1a5c38; color: white; }
    .badge-ops  { background: #6b3a1f; color: white; }
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e3a5f;
        border-bottom: 2px solid #2d6a9f;
        padding-bottom: 6px;
        margin: 20px 0 12px 0;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando datos de salud...")
def load_data() -> pd.DataFrame:
    """
    Carga los datos desde archivos .parquet (generados por Kedro) o desde
    los .xpt originales de NHANES como fallback de desarrollo.
    """
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── intento 1: parquet del pipeline Kedro ──
    parquet_demo = os.path.join(BASE, "data", "02_intermediate", "demo_clean.parquet")
    parquet_bpx  = os.path.join(BASE, "data", "02_intermediate", "bpx_clean.parquet")
    parquet_bmx  = os.path.join(BASE, "data", "02_intermediate", "bmx_clean.parquet")

    if all(os.path.exists(p) for p in [parquet_demo, parquet_bpx, parquet_bmx]):
        demo = pd.read_parquet(parquet_demo)
        bpx  = pd.read_parquet(parquet_bpx)
        bmx  = pd.read_parquet(parquet_bmx)
        source = "parquet"
    else:
        # ── intento 2: archivos .xpt en data/01_raw ──
        raw_dir = os.path.join(BASE, "data", "01_raw")
        demo, _ = pyreadstat.read_xport(os.path.join(raw_dir, "DEMO_J.xpt"))
        bpx,  _ = pyreadstat.read_xport(os.path.join(raw_dir, "BPX_J.xpt"))
        bmx,  _ = pyreadstat.read_xport(os.path.join(raw_dir, "BMX_J.xpt"))
        source = "xpt"

    # ── merge por SEQN ──
    df = demo.merge(bpx, on="SEQN", how="inner").merge(bmx, on="SEQN", how="inner")

    # ── columnas relevantes ──
    cols = {
        "SEQN":     "id",
        "RIAGENDR": "genero",
        "RIDAGEYR": "edad",
        "RIDRETH1": "etnia",
        "INDFMPIR": "indice_pobreza",
        "INDHHIN2": "ingreso_hogar",
        "BPXSY1":   "presion_sistolica",
        "BPXDI1":   "presion_diastolica",
        "BPXPLS":   "pulso",
        "BMXWT":    "peso_kg",
        "BMXHT":    "talla_cm",
        "BMXBMI":   "imc",
        "BMXWAIST": "cintura_cm",
    }
    df = df[[c for c in cols if c in df.columns]].rename(columns=cols)

    # ── decodificación de categóricas ──
    df["genero"] = df["genero"].map({1.0: "Masculino", 2.0: "Femenino"})
    df["etnia"]  = df["etnia"].map({
        1.0: "Mexicano-Americano",
        2.0: "Otro Hispano",
        3.0: "Blanco no hispano",
        4.0: "Negro no hispano",
        5.0: "Otro/Multirracial",
    })

    # ── clasificación IMC ──
    def clasif_imc(imc):
        if pd.isna(imc):  return None
        if imc < 18.5:    return "Bajo peso"
        if imc < 25.0:    return "Normal"
        if imc < 30.0:    return "Sobrepeso"
        return "Obesidad"

    df["categoria_imc"] = df["imc"].apply(clasif_imc)

    # ── clasificación presión arterial ──
    def clasif_presion(s):
        if pd.isna(s):    return None
        if s < 120:       return "Normal"
        if s < 130:       return "Elevada"
        if s < 140:       return "Hipertensión I"
        return "Hipertensión II"

    df["categoria_presion"] = df["presion_sistolica"].apply(clasif_presion)

    # ── grupos de edad ──
    bins  = [0, 17, 35, 50, 65, 150]
    labels = ["<18", "18-35", "36-50", "51-65", "65+"]
    df["grupo_edad"] = pd.cut(df["edad"], bins=bins, labels=labels, right=True)

    df["_source"] = source
    return df.dropna(subset=["imc", "presion_sistolica", "genero"])


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/DuocUC_logo.svg/400px-DuocUC_logo.svg.png",
        width=160,
    )
    st.sidebar.markdown("## 🏥 NHANES Health Dashboard")
    st.sidebar.markdown("---")

    audiencia = st.sidebar.radio(
        "👥 Selecciona audiencia",
        ["📊 Ejecutiva", "🔬 Técnica", "🗂️ Operativa"],
        index=0,
    )

    st.sidebar.markdown("### 🔍 Filtros")

    generos = ["Todos"] + sorted(df["genero"].dropna().unique().tolist())
    sel_genero = st.sidebar.selectbox("Género", generos)

    edad_min, edad_max = int(df["edad"].min()), int(df["edad"].max())
    sel_edad = st.sidebar.slider("Rango de edad", edad_min, edad_max, (edad_min, edad_max))

    etnias = ["Todas"] + sorted(df["etnia"].dropna().unique().tolist())
    sel_etnia = st.sidebar.selectbox("Etnia", etnias)

    categorias_imc = ["Todas"] + ["Bajo peso", "Normal", "Sobrepeso", "Obesidad"]
    sel_imc = st.sidebar.selectbox("Categoría IMC", categorias_imc)

    # ── aplicar filtros ──
    mask = (df["edad"] >= sel_edad[0]) & (df["edad"] <= sel_edad[1])
    if sel_genero != "Todos":  mask &= df["genero"] == sel_genero
    if sel_etnia  != "Todas":  mask &= df["etnia"]  == sel_etnia
    if sel_imc    != "Todas":  mask &= df["categoria_imc"] == sel_imc

    df_f = df[mask].copy()

    st.sidebar.markdown("---")
    st.sidebar.metric("Registros filtrados", f"{len(df_f):,}")
    if df["_source"].iloc[0] == "xpt":
        st.sidebar.warning("⚠️ Leyendo desde XPT.\nEjecuta `kedro run` para usar parquet.")

    return df_f, audiencia


# ─────────────────────────────────────────────
# VISTA EJECUTIVA
# ─────────────────────────────────────────────
def vista_ejecutiva(df: pd.DataFrame):
    st.markdown('<span class="audience-badge badge-exec">VISTA EJECUTIVA</span>', unsafe_allow_html=True)
    st.title("📊 Resumen Ejecutivo — Salud Poblacional NHANES")
    st.caption("Indicadores de alto nivel para toma de decisiones estratégicas en salud pública.")

    # ── KPIs ──
    pct_obesidad   = (df["categoria_imc"] == "Obesidad").mean() * 100
    pct_hiper      = df["categoria_presion"].isin(["Hipertensión I", "Hipertensión II"]).mean() * 100
    imc_medio      = df["imc"].mean()
    presion_media  = df["presion_sistolica"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{pct_obesidad:.1f}%</div>
            <div class="metric-label">Prevalencia de Obesidad</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{pct_hiper:.1f}%</div>
            <div class="metric-label">Hipertensión (I + II)</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{imc_medio:.1f}</div>
            <div class="metric-label">IMC Promedio Poblacional</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{presion_media:.0f} mmHg</div>
            <div class="metric-label">Presión Sistólica Media</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    # ── Donut IMC ──
    with col_a:
        st.markdown('<div class="section-title">Distribución IMC Poblacional</div>', unsafe_allow_html=True)
        imc_counts = df["categoria_imc"].value_counts().reset_index()
        imc_counts.columns = ["Categoría", "Cantidad"]
        orden = ["Bajo peso", "Normal", "Sobrepeso", "Obesidad"]
        imc_counts["Categoría"] = pd.Categorical(imc_counts["Categoría"], categories=orden, ordered=True)
        imc_counts = imc_counts.sort_values("Categoría")
        colores = ["#4a90d9", "#27ae60", "#f39c12", "#e74c3c"]
        fig = px.pie(
            imc_counts, values="Cantidad", names="Categoría",
            color_discrete_sequence=colores, hole=0.45,
        )
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # ── Barras presión por género ──
    with col_b:
        st.markdown('<div class="section-title">Hipertensión por Género</div>', unsafe_allow_html=True)
        hip_genero = (
            df.groupby(["genero", "categoria_presion"])
            .size().reset_index(name="n")
        )
        total_g = df.groupby("genero").size().reset_index(name="total")
        hip_genero = hip_genero.merge(total_g, on="genero")
        hip_genero["pct"] = hip_genero["n"] / hip_genero["total"] * 100
        fig2 = px.bar(
            hip_genero, x="categoria_presion", y="pct", color="genero",
            barmode="group", text_auto=".1f",
            labels={"categoria_presion": "Categoría", "pct": "% Población", "genero": "Género"},
            color_discrete_map={"Masculino": "#2d6a9f", "Femenino": "#e05c8a"},
        )
        fig2.update_layout(margin=dict(t=20, b=20), legend_title="Género")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tendencia IMC por edad ──
    st.markdown('<div class="section-title">IMC Promedio por Grupo de Edad y Género</div>', unsafe_allow_html=True)
    imc_edad = (
        df.groupby(["grupo_edad", "genero"], observed=True)["imc"]
        .mean().reset_index()
    )
    fig3 = px.line(
        imc_edad, x="grupo_edad", y="imc", color="genero", markers=True,
        labels={"grupo_edad": "Grupo de edad", "imc": "IMC Promedio", "genero": "Género"},
        color_discrete_map={"Masculino": "#2d6a9f", "Femenino": "#e05c8a"},
    )
    fig3.add_hline(y=30, line_dash="dash", line_color="red",
                   annotation_text="Umbral obesidad (30)", annotation_position="top left")
    fig3.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────
# VISTA TÉCNICA
# ─────────────────────────────────────────────
def vista_tecnica(df: pd.DataFrame):
    st.markdown('<span class="audience-badge badge-tech">VISTA TÉCNICA</span>', unsafe_allow_html=True)
    st.title("🔬 Análisis Estadístico y Correlaciones — NHANES")
    st.caption("Exploración estadística detallada para investigadores y analistas de datos.")

    # ── Matriz de correlación ──
    st.markdown('<div class="section-title">Mapa de Correlaciones entre Variables Clínicas</div>', unsafe_allow_html=True)
    num_cols = ["edad", "imc", "presion_sistolica", "presion_diastolica", "pulso", "cintura_cm", "indice_pobreza"]
    num_cols_exist = [c for c in num_cols if c in df.columns]
    labels_map = {
        "edad": "Edad", "imc": "IMC",
        "presion_sistolica": "Presión Sistólica", "presion_diastolica": "Presión Diastólica",
        "pulso": "Pulso", "cintura_cm": "Cintura (cm)", "indice_pobreza": "Índice Pobreza",
    }
    corr = df[num_cols_exist].corr()
    corr.index   = [labels_map.get(c, c) for c in corr.index]
    corr.columns = [labels_map.get(c, c) for c in corr.columns]
    fig_corr = px.imshow(
        corr, text_auto=".2f", aspect="auto",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
    )
    fig_corr.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # ── Scatter IMC vs Presión ──
    with col1:
        st.markdown('<div class="section-title">IMC vs Presión Sistólica</div>', unsafe_allow_html=True)
        muestra = df.sample(min(1500, len(df)), random_state=42)
        fig_sc = px.scatter(
            muestra, x="imc", y="presion_sistolica",
            color="categoria_imc", opacity=0.55,
            trendline="ols",
            labels={"imc": "IMC", "presion_sistolica": "Presión Sistólica (mmHg)", "categoria_imc": "Categoría IMC"},
            color_discrete_map={
                "Bajo peso": "#4a90d9", "Normal": "#27ae60",
                "Sobrepeso": "#f39c12", "Obesidad": "#e74c3c",
            },
        )
        fig_sc.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig_sc, use_container_width=True)

    # ── Box plot distribución IMC por etnia ──
    with col2:
        st.markdown('<div class="section-title">Distribución IMC por Etnia</div>', unsafe_allow_html=True)
        fig_box = px.box(
            df.dropna(subset=["etnia"]), x="etnia", y="imc", color="etnia",
            labels={"etnia": "Etnia", "imc": "IMC"},
            points=False,
        )
        fig_box.update_xaxes(tickangle=20)
        fig_box.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Histograma presión sistólica ──
    st.markdown('<div class="section-title">Distribución de Presión Sistólica por Género</div>', unsafe_allow_html=True)
    fig_hist = px.histogram(
        df.dropna(subset=["genero"]),
        x="presion_sistolica", color="genero", barmode="overlay",
        nbins=50, opacity=0.70,
        labels={"presion_sistolica": "Presión Sistólica (mmHg)", "genero": "Género"},
        color_discrete_map={"Masculino": "#2d6a9f", "Femenino": "#e05c8a"},
    )
    fig_hist.add_vline(x=130, line_dash="dash", line_color="orange",
                       annotation_text="Hipertensión elevada (130)")
    fig_hist.add_vline(x=140, line_dash="dash", line_color="red",
                       annotation_text="Hipertensión I (140)")
    fig_hist.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_hist, use_container_width=True)

    # ── Estadísticas descriptivas ──
    st.markdown('<div class="section-title">Estadísticas Descriptivas</div>', unsafe_allow_html=True)
    desc = df[num_cols_exist].describe().T
    desc.index = [labels_map.get(c, c) for c in desc.index]
    st.dataframe(desc.style.format("{:.2f}"), use_container_width=True)


# ─────────────────────────────────────────────
# VISTA OPERATIVA
# ─────────────────────────────────────────────
def vista_operativa(df: pd.DataFrame):
    st.markdown('<span class="audience-badge badge-ops">VISTA OPERATIVA</span>', unsafe_allow_html=True)
    st.title("🗂️ Panel Operativo — Exploración de Datos")
    st.caption("Herramienta de consulta y filtrado detallado para equipos de campo y clínicos.")

    # ── Resumen rápido ──
    c1, c2, c3 = st.columns(3)
    c1.metric("Total registros", f"{len(df):,}")
    c2.metric("IMC promedio", f"{df['imc'].mean():.1f}")
    c3.metric("Presión sistólica media", f"{df['presion_sistolica'].mean():.0f} mmHg")

    st.markdown("---")

    # ── Prevalencia de obesidad por etnia ──
    st.markdown('<div class="section-title">Prevalencia de Obesidad por Etnia y Género</div>', unsafe_allow_html=True)
    ob_etnia = (
        df.groupby(["etnia", "genero"], observed=True)
        .apply(lambda x: (x["categoria_imc"] == "Obesidad").mean() * 100)
        .reset_index(name="pct_obesidad")
    )
    fig_ob = px.bar(
        ob_etnia.dropna(), x="etnia", y="pct_obesidad", color="genero",
        barmode="group", text_auto=".1f",
        labels={"etnia": "Etnia", "pct_obesidad": "% con Obesidad", "genero": "Género"},
        color_discrete_map={"Masculino": "#2d6a9f", "Femenino": "#e05c8a"},
    )
    fig_ob.update_xaxes(tickangle=20)
    fig_ob.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_ob, use_container_width=True)

    # ── Heatmap presión sistólica media por edad y etnia ──
    st.markdown('<div class="section-title">Presión Sistólica Media por Grupo de Edad y Etnia</div>', unsafe_allow_html=True)
    heat = (
        df.groupby(["grupo_edad", "etnia"], observed=True)["presion_sistolica"]
        .mean().unstack("etnia")
    )
    fig_heat = px.imshow(
        heat, text_auto=".0f", aspect="auto",
        color_continuous_scale="YlOrRd",
        labels={"x": "Etnia", "y": "Grupo de Edad", "color": "mmHg"},
    )
    fig_heat.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── Tabla descargable ──
    st.markdown('<div class="section-title">Tabla de Datos Filtrados</div>', unsafe_allow_html=True)
    cols_tabla = [
        "id", "genero", "edad", "grupo_edad", "etnia",
        "imc", "categoria_imc", "peso_kg", "talla_cm", "cintura_cm",
        "presion_sistolica", "presion_diastolica", "categoria_presion",
        "pulso", "indice_pobreza",
    ]
    cols_tabla_exist = [c for c in cols_tabla if c in df.columns]
    df_tabla = df[cols_tabla_exist].copy()
    df_tabla["id"] = df_tabla["id"].astype(int)

    st.dataframe(
        df_tabla.head(500).style.format({
            "imc": "{:.1f}", "peso_kg": "{:.1f}",
            "talla_cm": "{:.1f}", "cintura_cm": "{:.1f}",
            "presion_sistolica": "{:.0f}", "presion_diastolica": "{:.0f}",
            "indice_pobreza": "{:.2f}",
        }),
        use_container_width=True,
        height=350,
    )

    csv = df_tabla.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar datos filtrados (CSV)",
        data=csv,
        file_name="nhanes_filtrado.csv",
        mime="text/csv",
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    df = load_data()
    df_filtrado, audiencia = render_sidebar(df)

    if "Ejecutiva" in audiencia:
        vista_ejecutiva(df_filtrado)
    elif "Técnica" in audiencia:
        vista_tecnica(df_filtrado)
    elif "Operativa" in audiencia:
        vista_operativa(df_filtrado)


if __name__ == "__main__":
    main()
