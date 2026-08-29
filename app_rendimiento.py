import os
import unicodedata
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Rendimiento, Táctica y Antropometría - Fortaleza F.C.",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 18px;
        border-radius: 6px;
        color: white;
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
        margin-bottom: 25px;
    }
    .header-box h1 { color: white; font-size: 24px; margin: 0; font-weight: 700; letter-spacing: 1px; }
    .header-box p { color: #f0f0f0; font-size: 12px; margin: 5px 0 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def cargar_todos_los_datos():
  # Nombre exacto del archivo GPS/Eyeball en tu carpeta
  archivo_ind = "DATOS INDIVIDUALES.xlsx"
  df_ind, df_res = pd.DataFrame(), pd.DataFrame()
  if os.path.exists(archivo_ind):
    xls = pd.ExcelFile(archivo_ind)
    if "Resumen_Jugadores" in xls.sheet_names:
      df_res = pd.read_excel(xls, sheet_name="Resumen_Jugadores")
    if "individual" in xls.sheet_names:
      df_ind = pd.read_excel(xls, sheet_name="individual")

  archivo_ant = "Mediciones_Individuales. SUB-20 Fortaleza 2026-1.xlsx"
  df_ant = pd.DataFrame()
  if os.path.exists(archivo_ant):
    try:
      df_ant = pd.read_excel(
          archivo_ant, sheet_name="Mediciones Individuales", header=7
      )
    except Exception:
      pass

  return df_ind, df_res, df_ant


df_ind, df_res, df_ant = cargar_todos_los_datos()

if df_ind.empty:
  st.error(
      "⚠️ No se encontró o está vacío el archivo de datos individuales"
      " ('DATOS INDIVIDUALES.xlsx')."
  )
  st.stop()

st.sidebar.markdown("### ⚙️ Panel de Control — Rendimiento")
st.sidebar.markdown("---")

col_nombre_candidatas = [
    c
    for c in df_ind.columns
    if any(k in str(c).lower() for k in ["nombre", "jug", "player"])
]
columna_nombre = (
    col_nombre_candidatas[0] if col_nombre_candidatas else df_ind.columns[3]
)

lista_jugadores = sorted(df_ind[columna_nombre].dropna().unique())
jugador_seleccionado = st.sidebar.selectbox(
    "Selecciona Deportista:", lista_jugadores
)

df_jugador_matches = df_ind[df_ind[columna_nombre] == jugador_seleccionado]
df_jugador_resumen = (
    df_res[df_res[columna_nombre] == jugador_seleccionado]
    if not df_res.empty
    else pd.DataFrame()
)

if (
    not df_ant.empty
    and "Nombre" in df_ant.columns
    and "Apellidos" in df_ant.columns
):
  df_ant["Nombre Completo"] = (
      df_ant["Nombre"].astype(str).str.strip()
      + " "
      + df_ant["Apellidos"].astype(str).str.strip()
  )
  tokens = jugador_seleccionado.lower().split()
  df_jugador_ant = df_ant[
      df_ant["Nombre Completo"].apply(
          lambda x: all(t in x.lower() for t in tokens)
      )
  ]
else:
  df_jugador_ant = pd.DataFrame()

st.markdown(
    """
    <div class="header-box">
        <h1>DEPARTAMENTO DE RENDIMIENTO, TÁCTICA Y SALUD</h1>
        <p>CONTROL GPS, TÁCTICA (EYEBALL) & ANTROPOMETRÍA | FORTALEZA F.C.</p>
    </div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Perfil Antropométrico & Composición",
    "🛰️ Control de Carga Externa (GPS)",
    "📊 Rendimiento Táctico (Eyeball)",
    "🔬 Análisis Cruzado (Carga vs Precisión)",
])

with tab1:
  st.markdown(
      f"### 👤 Composición Corporal & Antropometría: {jugador_seleccionado}"
  )
  if not df_jugador_ant.empty:
    ant_row = df_jugador_ant.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Masa Corporal", f"{ant_row.get('Masa corporal (Kg)', 0):.1f} kg"
    )
    c2.metric("Talla", f"{ant_row.get('Talla (cm)', 0)} cm")
    c3.metric("IMC", f"{ant_row.get('IMC (kg/m²)', 0):.1f}")
    c4.metric(
        "% Grasa (Yuhasz)", f"{ant_row.get('Masa grasa Yuhasz (%)', 0):.1f}%"
    )
    c5.metric(
        "Tejido Muscular (Lee)",
        f"{ant_row.get('Tejido muscular (Lee, 2000) (kg)', 0):.1f} kg",
    )

    st.markdown("---")
    st.markdown("#### 📏 Perímetros y Pliegues Registrados")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric(
        "Perímetro Cintura", f"{ant_row.get('Perímetro de Cintura (cm)', 0)} cm"
    )
    p2.metric(
        "Perímetro Muslo Medio",
        f"{ant_row.get('Perímetro de Muslo medio', 0)} cm",
    )
    p3.metric("Perímetro Pierna", f"{ant_row.get('Perímetro de la Pierna', 0)} cm")
    p4.metric(
        "Sumatorio 6 Pliegues",
        f"{ant_row.get('Sumatorio de 6 pliegues', 0)} mm",
    )

    with st.expander("📋 Ver reporte antropométrico completo en tabla"):
      st.dataframe(df_jugador_ant, use_container_width=True)
  else:
    st.info(
        "No se encontraron registros antropométricos específicos para este"
        " jugador en el archivo."
    )

with tab2:
  st.markdown("### 🛰️ Métricas de Carga GPS (Promedio por Partido)")
  if not df_jugador_matches.empty:
    gps_cols = ["pl", "td", "m_min", "hsr", "sprint25", "acc", "dec", "maxvel"]
    exist_gps = [c for c in gps_cols if c in df_jugador_matches.columns]
    if exist_gps:
      promedios_gps = df_jugador_matches[exist_gps].mean()
      g1, g2, g3, g4 = st.columns(4)
      g1.metric("Player Load (PL) Prom", f"{promedios_gps.get('pl', 0):.1f}")
      g2.metric("Distancia Total Prom", f"{promedios_gps.get('td', 0):.1f} m")
      g3.metric(
          "Alta Intensidad (HSR)", f"{promedios_gps.get('hsr', 0):.1f} m"
      )
      g4.metric(
          "Velocidad Máxima", f"{df_jugador_matches['maxvel'].max():.1f} km/h"
      )

      st.markdown("---")
      st.dataframe(
          df_jugador_matches[["Fecha", "Min. jug."] + exist_gps],
          use_container_width=True,
      )
  else:
    st.warning("Sin registros GPS disponibles.")

with tab3:
  st.markdown("### 📊 Rendimiento Táctico (Eyeball)")
  if not df_jugador_matches.empty:
    eyeball_cols = [
        "Fecha",
        "Valoración",
        "Precisión de pase",
        "Recuperación",
        "Intercepciones",
        "Success Duelos terrestres",
        "Total Duelos terrestres",
    ]
    exist_eye = [c for c in eyeball_cols if c in df_jugador_matches.columns]
    st.dataframe(df_jugador_matches[exist_eye], use_container_width=True)
  else:
    st.info("Sin registros tácticos disponibles.")

with tab4:
  st.markdown("### 🔬 Correlación: Carga Física (GPS) vs Precisión de Pase")
  if (
      not df_jugador_matches.empty
      and "pl" in df_jugador_matches.columns
      and "Precisión de pase" in df_jugador_matches.columns
  ):
    fig_corr = px.scatter(
        df_jugador_matches,
        x="pl",
        y="Precisión de pase",
        text="Fecha",
        title="<b>Player Load vs. Precisión de Pase por Partido</b>",
        labels={
            "pl": "Player Load (Carga Física)",
            "Precisión de pase": "Precisión de Pase (%)",
        },
    )
    fig_corr.update_traces(textposition="top center")
    fig_corr.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
    )
    st.plotly_chart(fig_corr, use_container_width=True)
  else:
    st.info("Métricas insuficientes para generar el gráfico de correlación.")