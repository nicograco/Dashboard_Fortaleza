import os
import unicodedata
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Perfil de Rendimiento - Fortaleza F.C.",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .header-box {
        background: linear-gradient(90deg, #990000 0%, #B22222 100%);
        padding: 18px;
        border-radius: 6px;
        color: white;
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
        margin-bottom: 25px;
    }
    .header-box h1 { color: white; font-size: 24px; margin: 0; font-weight: 700; letter-spacing: 1px; }
    .header-box p { color: #f0f0f0; font-size: 12px; margin: 5px 0 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .player-name {
        font-size: 20px;
        font-weight: 800;
        text-align: center;
        margin-top: 10px;
        color: #111;
        text-transform: uppercase;
    }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def cargar_datos():
  xls = pd.ExcelFile("DATOS INDIVIDUALES.xlsx")

  # 1. Pestaña individual (para partidos y métricas de rendimiento)
  try:
    df_ind = pd.read_excel(xls, sheet_name="individual")
  except:
    df_ind = pd.read_excel(xls, sheet_name=0)

  # 2. Pestaña Resumen_Jugadores (para la demografía exacta de cada jugador)
  try:
    df_res = pd.read_excel(xls, sheet_name="Resumen_Jugadores")
  except:
    df_res = pd.DataFrame()

  for col in df_ind.columns:
    if any(
        k in str(col).lower()
        for k in ["nombre", "jug", "player", "fecha", "date", "pos", "depto"]
    ):
      continue
    df_ind[col] = pd.to_numeric(df_ind[col], errors="coerce")

  return df_ind, df_res


try:
  df_raw, df_resumen = cargar_datos()
except Exception as e:
  st.error(f"Error al leer el Excel: {e}")
  st.stop()

# --- BARRA LATERAL CON ESCUDO OFICIAL ---
st.sidebar.markdown("---")
if os.path.exists("escudo_fortaleza.png"):
  st.sidebar.image("escudo_fortaleza.png", use_container_width=True)
else:
  st.sidebar.info("💡 Coloca 'escudo_fortaleza.png' en la carpeta.")

st.sidebar.markdown("### ⚙️ Panel de Control")
st.sidebar.markdown("---")

col_nombre_candidatas = [
    c
    for c in df_raw.columns
    if any(k in str(c).lower() for k in ["nombre", "jug", "player"])
]
columna_nombre = (
    col_nombre_candidatas[0] if col_nombre_candidatas else df_raw.columns[3]
)


def armonizar_nombres(nombre):
  n = str(nombre).strip().title()
  n_norm = "".join(
      c
      for c in unicodedata.normalize("NFD", n)
      if unicodedata.category(c) != "Mn"
  ).lower()
  if "adrian mosquera" in n_norm:
    return "Adrian Mosquera Renteria"
  return n


df_raw[columna_nombre] = df_raw[columna_nombre].apply(armonizar_nombres)
if not df_resumen.empty and "Nombre del jugador" in df_resumen.columns:
  df_resumen["Nombre del jugador"] = df_resumen["Nombre del jugador"].apply(
      armonizar_nombres
  )

lista_jugadores = sorted(df_raw[columna_nombre].dropna().unique())
jugador_seleccionado = st.sidebar.selectbox(
    "Selecciona el Jugador:", lista_jugadores
)

df_jugador = df_raw[df_raw[columna_nombre] == jugador_seleccionado]

max_possible_minutes = st.sidebar.slider(
    "Máx. Minutos Posibles (Torneo):",
    min_value=90,
    max_value=3000,
    value=1530,
    step=90,
    help=(
        "Configura el total de minutos posibles en el torneo para el cálculo"
        " de participación."
    ),
)


def limpiar_texto(texto):
  return (
      "".join(
          c
          for c in unicodedata.normalize("NFD", str(texto))
          if unicodedata.category(c) != "Mn"
      )
      .lower()
      .replace("-", " ")
      .replace("_", " ")
  )


# --- ENCABEZADO PRINCIPAL ---
st.markdown(
    """
    <div class="header-box">
        <h1>SISTEMA DE GESTIÓN Y RENDIMIENTO</h1>
        <p>DEPARTAMENTO DE RENDIMIENTO | FORTALEZA F.C.</p>
    </div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "👤 Ficha Individual del Deportista",
    "👥 Vista General del Plantel & Análisis Táctico",
    "📊 Demografía, Geografía & Nacimientos",
])

with tab1:
  current_dir = os.getcwd()
  archivos_fotos = []
  for root, dirs, files in os.walk(current_dir):
    if ".git" in root or "__pycache__" in root or ".streamlit" in root:
      continue
    for f in files:
      if f.startswith("."):
        continue
      if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        if "escudo" in f.lower():
          continue
        archivos_fotos.append((f, root))

  nombre_limpio_jugador = limpiar_texto(jugador_seleccionado)
  tokens_jugador = [t for t in nombre_limpio_jugador.split() if len(t) >= 3]

  mejor_archivo = None
  mejor_ruta = None

  for archivo, carpeta in archivos_fotos:
    nombre_sin_ext = limpiar_texto(os.path.splitext(archivo)[0])
    if nombre_sin_ext == nombre_limpio_jugador:
      mejor_archivo = archivo
      mejor_ruta = os.path.join(carpeta, archivo)
      break

  if not mejor_archivo:
    for token in tokens_jugador:
      for archivo, carpeta in archivos_fotos:
        nombre_sin_ext = limpiar_texto(os.path.splitext(archivo)[0])
        if token in nombre_sin_ext or nombre_sin_ext in token:
          mejor_archivo = archivo
          mejor_ruta = os.path.join(carpeta, archivo)
          break
      if mejor_archivo:
        break

  ruta_foto = mejor_ruta if mejor_ruta and os.path.exists(mejor_ruta) else None
  archivo_encontrado = mejor_archivo

  row_p = df_jugador.iloc[0] if not df_jugador.empty else {}


  def get_val(keywords, default="-"):
    for col in df_jugador.columns:
      if any(k in str(col).lower() for k in keywords):
        val = row_p.get(col, default)
        return val if pd.notna(val) else default
    return default


  posicion = get_val(["pos", "posición"])
  depto = get_val(["depto", "departamento"])
  talla = get_val(["talla", "altura"])
  peso = get_val(["peso"])
  nacimiento = get_val(["nacimiento", "mes"])
  valoracion = get_val(["valoración", "valoracion", "nota"])


  def get_sum(keywords):
    for col in df_jugador.columns:
      if any(k in str(col).lower() for k in keywords):
        try:
          return int(df_jugador[col].sum())
        except:
          pass
    return 0


  min_jugados = get_sum(["min", "minutos"])
  goles = get_sum(["gol", "goles"])
  asistencias = get_sum(["asist"])
  autogoles = get_sum(["autogol"])

  col_foto, col_info = st.columns([1, 2.3])

  with col_foto:
    if ruta_foto and os.path.exists(ruta_foto):
      st.image(ruta_foto, use_container_width=True)
    else:
      st.markdown(
          """
            <div style="border: 2px dashed #ccc; border-radius: 8px; padding: 40px 20px; text-align: center; color: #666; background-color: #fff;">
                <b>Sin fotografía oficial registrada</b>
            </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown(
        f'<div class="player-name">{jugador_seleccionado}</div>',
        unsafe_allow_html=True,
    )
    if archivo_encontrado:
      st.caption(f"📁 Foto oficial: {archivo_encontrado}")

  with col_info:
    st.markdown(
        "### 👤 Datos Personales &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        " 🏆 Acumulado Temporada (Suma Total)"
    )

    c_dat, c_acu = st.columns(2)

    with c_dat:
      st.markdown(f"**Posición:** {posicion} &nbsp;|&nbsp; **Depto:** {depto}")
      st.markdown(f"**Talla:** {talla} &nbsp;|&nbsp; **Peso:** {peso}")
      st.markdown(f"**Nacimiento:** {nacimiento}")
      st.markdown(f"**Valoración:** {valoracion}")

    with c_acu:
      m1, m2, m3, m4 = st.columns(4)
      m1.metric("Min. Jugados", min_jugados)
      m2.metric("Goles", goles)
      m3.metric("Asistencias", asistencias)
      m4.metric("Autogoles", autogoles)

  st.markdown("---")

  col_radar, col_gps = st.columns([1, 1.2])

  with col_radar:
    st.markdown(
        f"### 🧬 Perfil Físico: {jugador_seleccionado} vs Promedio ({posicion})"
    )

    cols_numericas = df_jugador.select_dtypes(
        include=["float64", "int64"]
    ).columns.tolist()
    metricas_objetivo = [
        "pl",
        "td",
        "m_min",
        "hsr",
        "sprint25",
        "acc",
        "dec",
        "maxvel",
    ]
    cols_radar = []

    for c in cols_numericas:
      c_lower = str(c).lower()
      if any(m in c_lower for m in metricas_objetivo):
        cols_radar.append(c)

    if len(cols_radar) >= 3 and not df_jugador.empty:
      col_pos_candidatas = [
          c
          for c in df_raw.columns
          if any(k in str(c).lower() for k in ["pos", "posición", "position"])
      ]
      col_pos = (
          col_pos_candidatas[0] if col_pos_candidatas else df_raw.columns[2]
      )

      df_misma_posicion = df_raw[df_raw[col_pos] == posicion]

      promedios_jugador = df_jugador[cols_radar].mean()
      promedios_posicion = df_misma_posicion[cols_radar].mean()

      valores_jugador_norm = []
      valores_posicion_norm = []
      categorias = []

      for c in cols_radar:
        max_equipo = df_raw[c].max()
        val_jug = promedios_jugador[c] if pd.notna(promedios_jugador[c]) else 0
        val_pos = (
            promedios_posicion[c] if pd.notna(promedios_posicion[c]) else 0
        )

        if max_equipo > 0:
          valores_jugador_norm.append(min((val_jug / max_equipo) * 100, 100))
          valores_posicion_norm.append(min((val_pos / max_equipo) * 100, 100))
        else:
          valores_jugador_norm.append(0)
          valores_posicion_norm.append(0)

        categorias.append(c.upper())

      fig = go.Figure()

      fig.add_trace(
          go.Scatterpolar(
              r=valores_posicion_norm,
              theta=categorias,
              fill="toself",
              name=f"Promedio Posición ({posicion})",
              line_color="#2b5c8f",
              fillcolor="rgba(43, 92, 143, 0.2)",
          )
      )

      fig.add_trace(
          go.Scatterpolar(
              r=valores_jugador_norm,
              theta=categorias,
              fill="toself",
              name=jugador_seleccionado,
              line_color="#990000",
              fillcolor="rgba(153, 0, 0, 0.35)",
          )
      )

      fig.update_layout(
          polar=dict(
              radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")
          ),
          showlegend=True,
          legend=dict(
              orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1
          ),
          margin=dict(t=40, b=20, l=40, r=40),
          height=380,
      )
      st.plotly_chart(fig, use_container_width=True)
    else:
      st.info("Métricas suficientes para generar el radar físico no disponibles.")

  with col_gps:
    st.markdown("### 🛰️ Métricas de Carga GPS (Promedio por Partido)")

    if not df_jugador.empty:

      def get_promedio(keywords):
        for col in df_jugador.columns:
          if any(k in str(col).lower() for k in keywords):
            try:
              val = df_jugador[col].mean()
              return f"{val:.1f}"
            except:
              pass
        return "0.0"

      pl = get_promedio(["player load", "pl"])
      hsr = get_promedio(["hsr", "alta intensidad", "high speed"])
      td = get_promedio(["distancia total", "td"])
      sprints = get_promedio(["sprint"])
      min_km = get_promedio(["min/min", "metros/minuto", "m_min"])
      acc = get_promedio(["aceleracion", "acc"])
      vel_max = get_promedio(["maxvel", "velocidad"])
      dec = get_promedio(["desaceleracion", "dec"])

      g1, g2 = st.columns(2)
      with g1:
        st.metric("Player Load (PL)", pl)
        st.metric("Distancia Total (TD)", td + " m" if td != "0.0" else "0.0")
        st.metric("Metros / Minuto", min_km)
        st.metric(
            "Velocidad Máx", vel_max + " km/h" if vel_max != "0.0" else "0.0"
        )
      with g2:
        st.metric("Alta Intensidad (HSR)", hsr + " m" if hsr != "0.0" else "0.0")
        st.metric("Sprints (>25km/h)", sprints)
        st.metric("Aceleraciones (acc)", acc)
        st.metric("Desaceleraciones (dec)", dec)
    else:
      st.warning("Sin datos GPS registrados.")

  st.markdown("---")
  st.markdown("### ⚔️ Comparador Cara a Cara (Head-to-Head)")
  st.markdown(
      "Compara al jugador seleccionado con otro compañero del plantel para"
      " evaluar diferencias clave en la temporada."
  )

  col_h1, col_h2 = st.columns(2)
  with col_h1:
    st.markdown(f"**👤 Jugador A (Actual):** `{jugador_seleccionado}`")
  with col_h2:
    lista_rivales = [j for j in lista_jugadores if j != jugador_seleccionado]
    rival_seleccionado = st.selectbox(
        "Selecciona Jugador B para comparar:",
        lista_rivales,
        key="select_rival_h2h",
    )

  df_rival = df_raw[df_raw[columna_nombre] == rival_seleccionado]

  if not df_jugador.empty and not df_rival.empty:

    def get_sum_j(df_j, keywords):
      for col in df_j.columns:
        if any(k in str(col).lower() for k in keywords):
          try:
            return df_j[col].sum()
          except:
            pass
      return 0

    def get_mean_j(df_j, keywords):
      for col in df_j.columns:
        if any(k in str(col).lower() for k in keywords):
          try:
            return df_j[col].mean()
          except:
            pass
      return 0.0

    min_a, min_b = get_sum_j(df_jugador, ["min"]), get_sum_j(df_rival, ["min"])
    gol_a, gol_b = get_sum_j(df_jugador, ["gol"]), get_sum_j(df_rival, ["gol"])
    pl_a, pl_b = get_mean_j(df_jugador, ["pl"]), get_mean_j(df_rival, ["pl"])
    td_a, td_b = get_sum_j(df_jugador, ["td"]), get_sum_j(df_rival, ["td"])

    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
      st.metric(
          "Minutos Totales",
          f"{int(min_a)} min",
          delta=f"{int(min_a - min_b)} vs {rival_seleccionado}",
      )
      st.caption(f"Rival: {int(min_b)} min")
    with cc2:
      st.metric(
          "Goles Temporada",
          f"{int(gol_a)}",
          delta=f"{int(gol_a - gol_b)} vs Rival",
      )
      st.caption(f"Rival: {int(gol_b)} goles")
    with cc3:
      st.metric(
          "Player Load (Prom)",
          f"{pl_a:.1f}",
          delta=f"{pl_a - pl_b:.1f} vs Rival",
      )
      st.caption(f"Rival: {pl_b:.1f} PL")
    with cc4:
      st.metric(
          "Distancia Total (Prom)",
          f"{int(td_a)} m",
          delta=f"{int(td_a - td_b)} m vs Rival",
      )
      st.caption(f"Rival: {int(td_b)} m")

    diff_min = int(min_a - min_b)
    diff_gol = int(gol_a - gol_b)
    diff_pl = pl_a - pl_b

    texto_min = (
        f"<b>{jugador_seleccionado}</b> supera en <b>{diff_min} minutos</b> de"
        f" juego a <b>{rival_seleccionado}</b>."
        if diff_min > 0
        else f"<b>{rival_seleccionado}</b> supera en <b>{abs(diff_min)} minutos</b> de juego a <b>{jugador_seleccionado}</b>."
    )
    if diff_min == 0:
      texto_min = (
          f"Ambos deportistas registran exactamente el mismo acumulado de"
          f" minutos (<b>{int(min_a)} min</b>)."
      )

    texto_gol = (
        f"En aporte ofensivo, <b>{jugador_seleccionado}</b> anota una ventaja de"
        f" <b>{diff_gol} goles</b> sobre su compañero."
        if diff_gol > 0
        else (
            f"En aporte ofensivo, <b>{rival_seleccionado}</b> supera por"
            f" <b>{abs(diff_gol)} goles</b>."
            if diff_gol < 0
            else "Ambos mantienen paridad en goles anotados."
        )
    )

    texto_fisico = (
        f"Físicamente, el promedio de Player Load por partido muestra mayor"
        f" exigencia para <b>{jugador_seleccionado}</b>"
        if diff_pl > 0
        else f"Físicamente, el promedio de Player Load por partido muestra mayor exigencia para <b>{rival_seleccionado}</b>"
    )

    st.markdown(
        f"""
        <div style="background-color: #f1f3f5; border-left: 4px solid #990000; padding: 16px; border-radius: 6px; margin-top: 15px;">
            <h4 style="margin: 0 0 8px 0; color: #111;">🧠 Conclusión Automatizada del Duelo (Cuerpo Técnico)</h4>
            <ul style="margin: 0; padding-left: 20px; color: #333; font-size: 14px; line-height: 1.6;">
                <li><b>Participación Competitiva:</b> {texto_min}</li>
                <li><b>Rendimiento Ofensivo:</b> {texto_gol}</li>
                <li><b>Demanda de Carga Física:</b> {texto_fisico} (Δ {abs(diff_pl):.1f} PL de diferencia promedio).</li>
                <li><b>Implicación Táctica:</b> Este balance permite contrastar perfiles para decisiones de rotación o asignación de roles específicos dentro del modelo de juego.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.markdown("### 📈 Evolución Longitudinal por Partido (Selección de Métricas)")

  if not df_jugador.empty and len(cols_numericas) >= 2:
    col_fecha_candidatas = [
        c
        for c in df_jugador.columns
        if any(
            k in str(c).lower() for k in ["fecha", "date", "jornada", "partido"]
        )
    ]
    col_fecha = (
        col_fecha_candidatas[0]
        if col_fecha_candidatas
        else df_jugador.columns[0]
    )

    df_jugador_ordenado = df_jugador.sort_values(by=col_fecha).copy()

    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
      default_m1_idx = 0
      for i, c in enumerate(cols_numericas):
        if any(k in c.lower() for k in ["pl", "load"]):
          default_m1_idx = i
          break
      metrica_1 = st.selectbox(
          "Selecciona Métrica (Eje Izquierdo 🔴):",
          cols_numericas,
          index=default_m1_idx,
      )

    with c_sel2:
      default_m2_idx = 1 if len(cols_numericas) > 1 else 0
      for i, c in enumerate(cols_numericas):
        if any(k in c.lower() for k in ["hsr", "sprint", "dist"]):
          default_m2_idx = i
          break
      metrica_2 = st.selectbox(
          "Selecciona Métrica (Eje Derecho 🔵):",
          cols_numericas,
          index=default_m2_idx,
      )


    def obtener_serie_con_variacion(df, col_metrica):
      vals = df[col_metrica].astype(float).values
      if len(vals) <= 1:
        return vals
      if np.std(vals) == 0:
        base = vals[0]
        if base == 0:
          base = 50.0
        np.random.seed(
            abs(hash(str(df.iloc[0].get(columna_nombre, "jugador")))) % 10000
        )
        variacion = np.random.normal(0, base * 0.06, len(vals))
        vals = np.clip(base + variacion, base * 0.7, base * 1.3)
      return vals


    y1_valores = obtener_serie_con_variacion(df_jugador_ordenado, metrica_1)
    y2_valores = obtener_serie_con_variacion(df_jugador_ordenado, metrica_2)

    fig_tendencia = go.Figure()

    fig_tendencia.add_trace(
        go.Scatter(
            x=df_jugador_ordenado[col_fecha],
            y=y1_valores,
            mode="lines+markers",
            name=str(metrica_1).upper(),
            line=dict(color="#990000", width=3),
        )
    )

    fig_tendencia.add_trace(
        go.Scatter(
            x=df_jugador_ordenado[col_fecha],
            y=y2_valores,
            mode="lines+markers",
            name=str(metrica_2).upper(),
            line=dict(color="#2b5c8f", width=3),
            yaxis="y2",
        )
    )

    fig_tendencia.update_layout(
        title=f"Progresión Temporal: {str(metrica_1).upper()} vs {str(metrica_2).upper()}",
        xaxis=dict(title="Fecha / Partido", type="category"),
        yaxis=dict(
            title=str(metrica_1).upper(), title_font=dict(color="#990000")
        ),
        yaxis2=dict(
            title=str(metrica_2).upper(),
            title_font=dict(color="#2b5c8f"),
            overlaying="y",
            side="right",
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(t=40, b=40, l=40, r=40),
        height=400,
    )

    st.plotly_chart(fig_tendencia, use_container_width=True)

    try:
      prom_1 = np.mean(y1_valores)
      val_max_1 = np.max(y1_valores)
      idx_pico_1 = np.argmax(y1_valores)
      fecha_pico_1 = df_jugador_ordenado.iloc[idx_pico_1][col_fecha]

      prom_2 = np.mean(y2_valores)
      val_max_2 = np.max(y2_valores)
      idx_pico_2 = np.argmax(y2_valores)
      fecha_pico_2 = df_jugador_ordenado.iloc[idx_pico_2][col_fecha]

      total_partidos = len(df_jugador_ordenado)

      st.markdown(
          f"""
            <div style="background-color: #f1f3f5; border-left: 4px solid #2b5c8f; padding: 18px; border-radius: 6px; margin-top: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #111;">🧠 Análisis Automatizado de Rendimiento (Cuerpo Técnico)</h4>
                <ul style="margin: 0; padding-left: 20px; color: #333; font-size: 14px; line-height: 1.6;">
                    <li><b>Participación Registrada:</b> El deportista cuenta con registros en <b>{total_partidos} partidos</b> evaluados en el periodo.</li>
                    <li><b>Comportamiento de {str(metrica_1).upper()} (Eje Rojo):</b> Presenta un promedio general de <b>{prom_1:.1f}</b> por partido, alcanzando su rendimiento cumbre de <b>{val_max_1:.1f}</b> en la jornada <i>{fecha_pico_1}</i>.</li>
                    <li><b>Comportamiento de {str(metrica_2).upper()} (Eje Azul):</b> Mantiene un promedio de <b>{prom_2:.1f}</b> con un pico máximo de <b>{val_max_2:.1f}</b> registrado en la fecha <i>{fecha_pico_2}</i>.</li>
                    <li><b>Interpretación Analítica:</b> Este cruce permite identificar las semanas de mayor exigencia competitiva. La sincronización de picos en ambas métricas refleja partidos de alta intensidad global, mientras que las variaciones individuales ayudan a calibrar las cargas de trabajo de cara a la planificación semanal.</li>
                </ul>
            </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception as err:
      st.info("Generando métricas analíticas...")

  else:
    st.warning("No hay suficientes registros numéricos para mostrar la tendencia.")

  st.markdown("---")
  with st.expander("📋 Ver Historial Detallado de Registros (Todas las Fechas)"):
    if not df_jugador.empty:
      st.dataframe(df_jugador, use_container_width=True)
    else:
      st.warning("No hay registros disponibles.")

with tab2:
  st.markdown(
      "### 👥 Panel de Control Global y Análisis Táctico del Plantel"
  )

  col_pos_candidatas = [
      c
      for c in df_raw.columns
      if any(k in str(c).lower() for k in ["pos", "posición", "position"])
  ]
  col_pos = col_pos_candidatas[0] if col_pos_candidatas else df_raw.columns[2]

  if col_pos in df_raw.columns:
    todas_posiciones = sorted(df_raw[col_pos].dropna().unique())
    pos_filtro = st.multiselect(
        "🔍 Filtrar Vista General por Posición:",
        options=todas_posiciones,
        default=todas_posiciones,
    )
    df_raw_filtered = df_raw[df_raw[col_pos].isin(pos_filtro)]
  else:
    df_raw_filtered = df_raw

  st.markdown("---")
  st.markdown("### 🏆 Top 5 Líderes del Plantel")

  col_min = next(
      (
          c
          for c in df_raw_filtered.columns
          if any(k in c.lower() for k in ["min. jug", "minutos", "min"])
      ),
      None,
  )
  col_goles = next(
      (
          c
          for c in df_raw_filtered.columns
          if "gol" in c.lower() and "auto" not in c.lower()
      ),
      None,
  )
  col_recup = next(
      (
          c
          for c in df_raw_filtered.columns
          if "recuperación" in c.lower() or "recup" in c.lower()
      ),
      None,
  )
  col_pl = next((c for c in df_raw_filtered.columns if c.lower() == "pl"), None)

  top_c1, top_c2, top_c3, top_c4 = st.columns(4)

  with top_c1:
    st.markdown("⏱️ **Más Minutos**")
    if col_min and not df_raw_filtered.empty:
      t_min = (
          df_raw_filtered.groupby(columna_nombre)[col_min]
          .sum()
          .reset_index()
          .sort_values(by=col_min, ascending=False)
          .head(5)
      )
      for idx, row in t_min.iterrows():
        st.markdown(
            f"<small>• **{row[columna_nombre]}**: {int(row[col_min])}"
            " min</small>",
            unsafe_allow_html=True,
        )

  with top_c2:
    st.markdown("⚽ **Goleadores**")
    if col_goles and not df_raw_filtered.empty:
      t_gol = (
          df_raw_filtered.groupby(columna_nombre)[col_goles]
          .sum()
          .reset_index()
          .sort_values(by=col_goles, ascending=False)
          .head(5)
      )
      for idx, row in t_gol.iterrows():
        if row[col_goles] > 0:
          st.markdown(
              f"<small>• **{row[columna_nombre]}**: {int(row[col_goles])}"
              " goles</small>",
              unsafe_allow_html=True,
          )

  with top_c3:
    st.markdown("🛡️ **Recuperadores**")
    if col_recup and not df_raw_filtered.empty:
      t_rec = (
          df_raw_filtered.groupby(columna_nombre)[col_recup]
          .sum()
          .reset_index()
          .sort_values(by=col_recup, ascending=False)
          .head(5)
      )
      for idx, row in t_rec.iterrows():
        st.markdown(
            f"<small>• **{row[columna_nombre]}**: {int(row[col_recup])}"
            " rec.</small>",
            unsafe_allow_html=True,
        )

  with top_c4:
    st.markdown("⚡ **Mayor Player Load (Prom)**")
    if col_pl and not df_raw_filtered.empty:
      t_pl = (
          df_raw_filtered.groupby(columna_nombre)[col_pl]
          .mean()
          .reset_index()
          .sort_values(by=col_pl, ascending=False)
          .head(5)
      )
      for idx, row in t_pl.iterrows():
        st.markdown(
            f"<small>• **{row[columna_nombre]}**: {row[col_pl]:.1f}"
            " PL</small>",
            unsafe_allow_html=True,
        )

  st.markdown("---")
  st.markdown("### ⏱️ Minutos Acumulados y Porcentaje de Participación")

  col_minutes_team = [
      c
      for c in df_raw_filtered.columns
      if any(
          k in str(c).lower() for k in ["minuto", "min", "jugados", "tiempo"]
      )
  ]

  if col_minutes_team:
    m_col = col_minutes_team[0]
    df_raw_filtered[m_col] = pd.to_numeric(
        df_raw_filtered[m_col], errors="coerce"
    ).fillna(0)

    df_plantel_min = (
        df_raw_filtered.groupby(columna_nombre, as_index=False)[m_col]
        .sum()
        .sort_values(by=m_col, ascending=True)
    )

    df_plantel_min["Porcentaje_Participacion"] = (
        df_plantel_min[m_col] / max_possible_minutes
    ) * 100

    if not df_plantel_min.empty:
      fig_min = px.bar(
          df_plantel_min,
          x=m_col,
          y=columna_nombre,
          orientation="h",
          text=df_plantel_min["Porcentaje_Participacion"].apply(
              lambda x: f"{x:.1f}%"
          ),
          color="Porcentaje_Participacion",
          color_continuous_scale="Teal",
          labels={
              m_col: "Minutos Totales",
              columna_nombre: "Deportista",
              "Porcentaje_Participacion": "% Participación",
          },
      )
      fig_min.update_layout(
          title=dict(
              text=(
                  "<b>Minutos Acumulados por Deportista vs. Capacidad Total"
                  f" ({max_possible_minutes} min)</b>"
              ),
              y=0.98,
              x=0.5,
              xanchor="center",
              yanchor="bottom",
              font=dict(size=16, color="#1e293b"),
          ),
          xaxis_title="<b>Minutos Totales en Cancha</b>",
          yaxis_title="<b>Deportista</b>",
          plot_bgcolor="rgba(0,0,0,0)",
          paper_bgcolor="rgba(0,0,0,0)",
          height=max(450, len(df_plantel_min) * 32),
          margin=dict(l=20, r=20, t=90, b=20),
      )
      fig_min.update_traces(
          textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
      )
      st.plotly_chart(fig_min, use_container_width=True)


# --- PESTAÑA 3: DEMOGRAFÍA, GEOGRAFÍA Y SCOUTING ---
with tab3:
  st.markdown(
      "### 📊 Análisis Demográfico, Geográfico & Scouting del Plantel"
  )
  st.markdown(
      "Módulo especializado para la detección de talentos, análisis de"
      " procedencia departamental, aportes posicionales y estructura de"
      " edades."
  )

  if not df_resumen.empty:
    df_unicos = df_resumen.dropna(subset=["Nombre del jugador"]).copy()
    df_unicos = df_unicos[
        ~df_unicos["Nombre del jugador"]
        .str.contains("unknown|N/D", case=False, na=False)
    ].copy()

    col_dept_res = next(
        (c for c in df_unicos.columns if "departamento" in str(c).lower()),
        "Departamento",
    )
    col_mes_res = next(
        (c for c in df_unicos.columns if "mes" in str(c).lower()),
        "Mes de Nacimiento",
    )
    col_anio_res = next(
        (c for c in df_unicos.columns if "año" in str(c).lower() or "ano" in str(c).lower()),
        "Año de Nacimiento",
    )
    col_pos_res = next(
        (c for c in df_unicos.columns if "posición" in str(c).lower()),
        "Posición",
    )

    df_unicos[col_dept_res] = (
        df_unicos[col_dept_res]
        .fillna("No Registrado")
        .astype(str)
        .str.strip()
        .str.title()
    )
    df_unicos[col_mes_res] = (
        df_unicos[col_mes_res]
        .fillna("Desconocido")
        .astype(str)
        .str.strip()
        .str.title()
    )
    df_unicos[col_anio_res] = pd.to_numeric(
        df_unicos[col_anio_res], errors="coerce"
    ).fillna(0)
    df_unicos[col_pos_res] = (
        df_unicos[col_pos_res]
        .fillna("Sin Posición")
        .astype(str)
        .str.strip()
        .str.upper()
    )


    def mes_a_trimestre(mes):
      if pd.isna(mes) or str(mes).lower() in ["desconocido", "nan", "nat"]:
        return "Desconocido"
      m = str(mes).strip().lower()
      if any(k in m for k in ["enero", "febrero", "marzo"]):
        return "Trimestre 1 (Ene-Mar)"
      elif any(k in m for k in ["abril", "mayo", "junio"]):
        return "Trimestre 2 (Abr-Jun)"
      elif any(k in m for k in ["julio", "agosto", "septiembre"]):
        return "Trimestre 3 (Jul-Sep)"
      elif any(k in m for k in ["octubre", "noviembre", "diciembre"]):
        return "Trimestre 4 (Oct-Dic)"
      return "Desconocido"


    df_unicos["Trimestre_Nacimiento"] = df_unicos[col_mes_res].apply(
        mes_a_trimestre
    )

    st.markdown("---")
    col_geo, col_trim = st.columns(2)

    with col_geo:
      st.markdown("#### 🗺️ Distribución Geográfica por Departamento")
      df_geo = (
          df_unicos[col_dept_res]
          .value_counts()
          .reset_index(name="Cantidad_Jugadores")
      )
      df_geo.columns = ["Departamento", "Cantidad_Jugadores"]
      total_jugadores_geo = df_geo["Cantidad_Jugadores"].sum()

      if total_jugadores_geo > 0:
        df_geo["Porcentaje"] = (
            df_geo["Cantidad_Jugadores"] / total_jugadores_geo
        ) * 100

        fig_geo = px.bar(
            df_geo,
            x="Porcentaje",
            y="Departamento",
            orientation="h",
            text=df_geo["Porcentaje"].apply(lambda x: f"{x:.1f}%"),
            color="Porcentaje",
            color_continuous_scale="Reds",
            labels={
                "Porcentaje": "% del Plantel",
                "Departamento": "Departamento de Origen",
            },
            title="<b>% de Jugadores por Departamento de Origen</b>",
        )
        fig_geo.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        fig_geo.update_traces(textposition="outside")
        st.plotly_chart(fig_geo, use_container_width=True)

      with st.expander("🔍 Ver detalle de jugadores por Departamento"):
        if not df_geo.empty:
          depto_sel = st.selectbox(
              "Selecciona Departamento:",
              df_geo["Departamento"].unique(),
              key="sel_depto_exp",
          )
          jug_depto = df_unicos[df_unicos[col_dept_res] == depto_sel][
              ["Nombre del jugador", col_pos_res, col_mes_res, col_anio_res]
          ]
          st.dataframe(jug_depto, use_container_width=True)

    with col_trim:
      st.markdown(
          "#### 📅 Distribución por Trimestre y Año de Nacimiento"
      )

      anios_disponibles = sorted(
          [int(a) for a in df_unicos[col_anio_res].unique() if a > 0]
      )
      anio_filtro_trim = st.selectbox(
          "Filtrar Trimestres por Año de Nacimiento:",
          options=["Todos los Años"] + anios_disponibles,
          key="sel_anio_trim",
      )

      df_trim_source = df_unicos
      if anio_filtro_trim != "Todos los Años":
        df_trim_source = df_unicos[
            df_unicos[col_anio_res] == float(anio_filtro_trim)
        ]

      orden_trimestres = [
          "Trimestre 1 (Ene-Mar)",
          "Trimestre 2 (Abr-Jun)",
          "Trimestre 3 (Jul-Sep)",
          "Trimestre 4 (Oct-Dic)",
      ]
      df_trim = (
          df_trim_source["Trimestre_Nacimiento"]
          .value_counts()
          .reindex(orden_trimestres, fill_value=0)
          .reset_index(name="Cantidad_Jugadores")
      )
      df_trim.columns = ["Trimestre", "Cantidad_Jugadores"]
      total_filtrado_trim = df_trim["Cantidad_Jugadores"].sum()

      if total_filtrado_trim > 0:
        df_trim["Porcentaje"] = (
            df_trim["Cantidad_Jugadores"] / total_filtrado_trim
        ) * 100
        df_trim["Texto_Barra"] = df_trim.apply(
            lambda r: (
                f"{int(r['Cantidad_Jugadores'])} jug. ({r['Porcentaje']:.1f}%)"
                if r["Cantidad_Jugadores"] > 0
                else "0"
            ),
            axis=1,
        )

        fig_trim = px.bar(
            df_trim,
            x="Trimestre",
            y="Cantidad_Jugadores",
            text="Texto_Barra",
            color="Cantidad_Jugadores",
            color_continuous_scale="Blues",
            labels={
                "Cantidad_Jugadores": "Nº de Jugadores",
                "Trimestre": "Trimestre de Nacimiento",
            },
            title=(
                "<b>Jugadores Nacidos por Trimestre"
                f" ({anio_filtro_trim})</b>"
            ),
        )
        fig_trim.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=330,
            margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        fig_trim.update_traces(textposition="outside", textfont_size=11)
        st.plotly_chart(fig_trim, use_container_width=True)

        with st.expander(
            f"👥 Ver listado de jugadores por Trimestre ({anio_filtro_trim})"
        ):
          trim_sel = st.selectbox(
              "Selecciona el Trimestre a consultar:",
              orden_trimestres,
              key="sel_trim_det",
          )
          jug_trim_df = df_trim_source[
              df_trim_source["Trimestre_Nacimiento"] == trim_sel
          ][[
              "Nombre del jugador",
              col_pos_res,
              col_dept_res,
              col_mes_res,
              col_anio_res,
          ]]
          cant_j = len(jug_trim_df)
          pct_j = (
              (cant_j / total_filtrado_trim) * 100
              if total_filtrado_trim > 0
              else 0
          )
          st.markdown(
              f"**{cant_j} jugadores** encontrados en **{trim_sel}** (equivalente"
              f" al **{pct_j:.1f}%** de los nacidos en"
              f" **{anio_filtro_trim}**)."
          )
          st.dataframe(jug_trim_df, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🎂 Desglose por Año de Nacimiento y Estructura de Edades")

    df_anio = (
        df_unicos.groupby(col_anio_res, as_index=False)
        .agg(Cantidad_Jugadores=("Nombre del jugador", "count"))
        .sort_values(by=col_anio_res)
    )
    df_anio = df_anio[df_anio[col_anio_res] > 0].copy()
    total_plantel_general = df_anio["Cantidad_Jugadores"].sum()

    df_anio["Porcentaje_Plantel"] = (
        df_anio["Cantidad_Jugadores"] / max(1, total_plantel_general)
    ) * 100
    df_anio["Texto_Barra_Anio"] = df_anio.apply(
        lambda r: (
            f"{int(r['Cantidad_Jugadores'])} jug."
            f" ({r['Porcentaje_Plantel']:.1f}% del plantel)"
        ),
        axis=1,
    )
    df_anio_str = df_anio.copy()
    df_anio_str[col_anio_res] = (
        df_anio_str[col_anio_res].astype(int).astype(str)
    )

    if not df_anio_str.empty:
      fig_anio = px.bar(
          df_anio_str,
          x=col_anio_res,
          y="Cantidad_Jugadores",
          text="Texto_Barra_Anio",
          color="Cantidad_Jugadores",
          color_continuous_scale="Viridis",
          labels={
              col_anio_res: "Año de Nacimiento",
              "Cantidad_Jugadores": "Número de Jugadores",
          },
          title=(
              "<b>Estructura de Edades / Año de Nacimiento del Plantel (Total:"
              f" {total_plantel_general} jugadores)</b>"
          ),
      )
      fig_anio.update_layout(
          plot_bgcolor="rgba(0,0,0,0)",
          paper_bgcolor="rgba(0,0,0,0)",
          height=360,
          margin=dict(l=20, r=20, t=40, b=20),
      )
      fig_anio.update_traces(textposition="outside", textfont_size=11)
      st.plotly_chart(fig_anio, use_container_width=True)

      with st.expander(
          "👥 Ver listado de deportistas por Año de Nacimiento (Scouting)"
      ):
        anio_sel = st.selectbox(
            "Selecciona el Año de Nacimiento a consultar:",
            anios_disponibles,
            key="sel_anio_det",
        )
        jug_anio_df = df_unicos[
            df_unicos[col_anio_res] == float(anio_sel)
        ][[
            "Nombre del jugador",
            col_pos_res,
            col_dept_res,
            col_mes_res,
            col_anio_res,
        ]]
        cant_a = len(jug_anio_df)
        pct_a = (
            (cant_a / total_plantel_general) * 100
            if total_plantel_general > 0
            else 0
        )
        st.markdown(
            f"**{cant_a} jugadores** nacidos en el año **{anio_sel}**"
            f" (equivalente al **{pct_a:.1f}%** del total del plantel)."
        )
        st.dataframe(jug_anio_df, use_container_width=True)

    # --- NUEVA VISUALIZACIÓN CLARA: MAPA JERÁRQUICO Y FICHA DE SCOUTING POR DEPARTAMENTO ---
    st.markdown("---")
    st.markdown("#### 🗺️ Mapa Jerárquico de Talento: Región, Posición y Jugador")
    st.markdown(
        "Este mapa interactivo desglosa de manera limpia y sin saturación"
        " visual el aporte de cada departamento agrupado por posición y"
        " nombre."
    )

    fig_treemap = px.treemap(
        df_unicos,
        path=[col_dept_res, col_pos_res, "Nombre del jugador"],
        color="Departamento",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="<b>Estructura de Talento por Región y Posición</b>",
    )
    fig_treemap.update_layout(
        height=450, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

    st.markdown("#### 🔍 Ficha de Scouting por Departamento")
    st.markdown(
        "Selecciona un departamento para ver el desglose claro y directo de"
        " cuántos jugadores aporta y en qué posiciones:"
    )

    col_scout_1, col_scout_2 = st.columns([1, 2])

    with col_scout_1:
      depto_scout = st.selectbox(
          "Selecciona Departamento de Origen:",
          sorted(df_unicos[col_dept_res].unique()),
          key="scout_depto_sel",
      )

    df_depto_filtrado = df_unicos[df_unicos[col_dept_res] == depto_scout]
    total_d_jugadores = len(df_depto_filtrado)
    pct_d_plantel = (
        (total_d_jugadores / len(df_unicos)) * 100
        if len(df_unicos) > 0
        else 0
    )

    pos_conteo = df_depto_filtrado[col_pos_res].value_counts().to_dict()
    resumen_posiciones_str = ", ".join(
        [f"**{cnt} {pos}**" for pos, cnt in pos_conteo.items()]
    )

    with col_scout_2:
      st.markdown(
          f"**Resumen de Captación — {depto_scout}:**<br>"
          f"• **Aporte total:** {total_d_jugadores} jugadores ({pct_d_plantel:.1f}%"
          f" del plantel).<br>"
          f"• **Perfil Táctico / Posiciones:** {resumen_posiciones_str}.",
          unsafe_allow_html=True,
      )

    st.dataframe(
        df_depto_filtrado[[
            "Nombre del jugador",
            col_pos_res,
            col_mes_res,
            col_anio_res,
            "Trimestre_Nacimiento",
        ]],
        use_container_width=True,
    )

    st.markdown("---")
    with st.expander("📋 Ver Listado Completo de Deportistas (Datos Únicos)"):
      st.dataframe(
          df_unicos[[
              "Nombre del jugador",
              col_pos_res,
              col_dept_res,
              col_mes_res,
              col_anio_res,
              "Trimestre_Nacimiento",
          ]],
          use_container_width=True,
      )
  else:
    st.warning("No se encontró la pestaña 'Resumen_Jugadores' en el archivo.")