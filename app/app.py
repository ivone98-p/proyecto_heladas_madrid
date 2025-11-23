# ============================================================
#  APP DE HELADAS - VERSIÓN SIMPLIFICADA
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import locale

# Configurar locale para español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass  # Si no funciona, continuará en inglés

# Configuración
st.set_page_config(
    page_title="SalvaCos - Heladas Madrid",
    page_icon="❄️",
    layout="wide"
)

# CSS personalizado para el botón azul, métricas más grandes y título centrado
st.markdown("""
    <style>
    .stButton > button {
        background: linear-gradient(135deg, #87CEEB 0%, #4682B4 100%);
        color: white;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4682B4 0%, #1E90FF 100%);
        border: none;
    }
    /* Hacer las métricas más grandes */
    [data-testid="stMetricValue"] {
        font-size: 3.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 2.5rem !important;
    }
    /* Título centrado en el header */
    header[data-testid="stHeader"] {
        background: linear-gradient(135deg, #87CEEB 0%, #4682B4 100%);
    }
    header[data-testid="stHeader"]::before {
        content: "SalvaCos";
        display: block;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        color: white;
        padding: 15px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Título con botón de actualizar a la derecha
col_title, col_btn = st.columns([4, 1])

with col_title:
    st.title("❄️ Sistema de Alerta de Heladas - Madrid, Cundinamarca")

with col_btn:
    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar Predicción", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# Descripción del sistema
st.markdown("""
    <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 4px solid #4682B4; margin-bottom: 20px;">
        <p style="margin: 0; color: #1565C0; font-size: 15px;">
            <strong>Sistema de predicción de heladas</strong> para el municipio de Madrid, Cundinamarca. 
            Utiliza <strong>Machine Learning</strong> con 30 años de datos históricos del IDEAM para predecir 
            temperaturas y riesgo de heladas con 24 horas de anticipación.
        </p>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# IMPORTAR PREDICTOR
# ============================================================
try:
    from predictor import PredictorHeladas
    PREDICTOR_DISPONIBLE = True
except Exception as e:
    st.error(f"⚠️ No se pudo importar el predictor: {e}")
    PREDICTOR_DISPONIBLE = False

# ============================================================
# CARGAR PREDICTOR
# ============================================================
@st.cache_resource
def cargar_predictor():
    """Carga el predictor una sola vez"""
    try:
        return PredictorHeladas()
    except Exception as e:
        st.error(f"❌ Error cargando modelos: {e}")
        return None

st.markdown("---")

# ============================================================
# HACER PREDICCIÓN
# ============================================================
if not PREDICTOR_DISPONIBLE:
    st.warning("⚠️ Predictor no disponible. Usando valores por defecto.")
    temp_predicha = 1.5
    prob_helada = 65
    riesgo = "MEDIO"
    color_riesgo = "🟡"
    color_mapa = "orange"
    resultado = None
    predicciones_7dias = []
else:
    predictor = cargar_predictor()
    
    if predictor is None:
        st.error("⚠️ No se pudo cargar el predictor. Usando valores por defecto.")
        temp_predicha = 1.5
        prob_helada = 65
        riesgo = "MEDIO"
        color_riesgo = "🟡"
        color_mapa = "orange"
        resultado = None
    else:
        # Hacer predicción para MAÑANA (usando fecha actual del sistema)
        with st.spinner("🔮 Generando predicción..."):
            resultado = predictor.predecir()
        
        if "error" in resultado:
            st.error(f"❌ Error en predicción: {resultado['error']}")
            temp_predicha = 1.5
            prob_helada = 65
            riesgo = "MEDIO"
            color_riesgo = "🟡"
            color_mapa = "orange"
        else:
            # Extraer resultados del PRIMER DÍA (mañana)
            temp_predicha = resultado['temperatura_predicha']
            prob_helada = resultado['probabilidad_helada']
            riesgo = resultado['riesgo']
            color_riesgo = resultado['emoji_riesgo']
            color_mapa = resultado['color_mapa']

# ============================================================
# MÉTRICAS PRINCIPALES (SOLO MAÑANA)
# ============================================================
if resultado:
    st.subheader(f"🌡️ Predicción para Mañana ({resultado['fecha_prediccion'].strftime('%d/%m/%Y')})")
else:
    st.subheader("🌡️ Predicción para Mañana")

# Columnas para métricas y botón de Telegram
col_metricas, col_telegram = st.columns([2, 1])

with col_metricas:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🌡️ Temperatura Predicha", 
            f"{temp_predicha:.1f}°C"
        )

    with col2:
        st.metric("❄️ Probabilidad Helada", f"{prob_helada:.1f}%")

    with col3:
        st.metric("🔎 Nivel de Riesgo", f"{color_riesgo} {riesgo}")

with col_telegram:
    # Botón de Telegram al lado de las métricas
    st.markdown("""
        <div style="background: linear-gradient(135deg, #87CEEB 0%, #4682B4 100%); 
                    padding: 20px 15px; 
                    border-radius: 9px; 
                    text-align: center;
                    height: 100%;">
            <p style="color: white; margin: 0 0 10px 0; font-size: 13px;">
                📱 <strong>¿Quieres recibir alertas automáticas cuando haya riesgo de helada?</strong>
            </p>
            <a href="https://t.me/MadridHeladasBot" target="_blank" style="text-decoration: none;">
                <button style="
                    background: white;
                    color: #4682B4;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    width: 100%;
                ">
                    🔔 Activar Alerta de Heladas
                </button>
            </a>
            <p style="color: white; margin: 10px 0 5px 0; font-size: 11px; opacity: 0.9;">
                👉 Se abrirá Telegram → Presiona <strong>/start</strong> para suscribirte
            </p>
            <p style="color: white; margin: 5px 0; font-size: 10px; opacity: 0.85;">
                ❌ Envía <strong>/stop</strong> para pausar
            </p>
            <p style="color: white; margin: 0; font-size: 10px; opacity: 0.85;">
                ▶️ Envía <strong>/reanudar</strong> para reactivar
            </p>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# ALERTA (SOLO MAÑANA)
# ============================================================
st.markdown("---")
if resultado:
    # Convertir mes a español manualmente
    meses_es = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    fecha_pred = resultado['fecha_prediccion']
    dia = fecha_pred.day
    mes = meses_es[fecha_pred.month]
    anio = fecha_pred.year
    fecha_prediccion_str = f"{dia} de {mes} de {anio}"
    
    if temp_predicha <= 0:
        st.error(f"⚠️ **ALERTA DE HELADA**: Se espera temperatura bajo 0°C el **{fecha_prediccion_str}**")
    elif temp_predicha <= 2:
        st.warning(f"⚡ **PRECAUCIÓN**: Temperatura cercana al punto de congelación el **{fecha_prediccion_str}**")
    else:
        st.success(f"✅ No se espera helada para el **{fecha_prediccion_str}**")
else:
    if temp_predicha <= 0:
        st.error(f"⚠️ **ALERTA DE HELADA**: Se espera temperatura bajo 0°C")
    elif temp_predicha <= 2:
        st.warning(f"⚡ **PRECAUCIÓN**: Temperatura cercana al punto de congelación")
    else:
        st.success(f"✅ No se espera helada")

# ============================================================
# MAPA INTERACTIVO CON POLÍGONO DE MADRID
# ============================================================
st.subheader("Mapa de Temperatura Mínima - Madrid, Cundinamarca")

# --- QUITA LAS COLUMNAS (esto era lo que lo desalineaba) ---
# Elimina esta línea: col_mapa, col_alerta = st.columns([3, 1])
# Y quita el "with col_mapa:" de abajo

# Coordenadas de Madrid, Cundinamarca
madrid_lat = 4.7333
madrid_lon = -74.2667

# Crear mapa
mapa = folium.Map(
    location=[madrid_lat, madrid_lon],
    zoom_start=13,
    tiles='OpenStreetMap'
)

# Círculo de zona de influencia
folium.Circle(
    location=[madrid_lat, madrid_lon],
    radius=3000,
    color=color_mapa,
    weight=3,
    fill=True,
    fillColor=color_mapa,
    fillOpacity=0.3,
    popup=f"<b>Madrid, Cundinamarca</b><br>Temp. predicha: {temp_predicha:.1f}°C<br>Riesgo: {riesgo}",
    tooltip="Madrid, Cundinamarca"
).add_to(mapa)

# Marcador con icono de termómetro
folium.Marker(
    location=[madrid_lat, madrid_lon],
    popup=f"<b>Madrid, Cundinamarca</b><br>Temperatura predicha: <b>{temp_predicha:.1f}°C</b><br>Probabilidad helada: <b>{prob_helada:.1f}%</b><br>Riesgo: <b>{riesgo}</b><br>Fecha: {resultado['fecha_prediccion'] if resultado else 'N/A'}",
    tooltip=f"{temp_predicha:.1f}°C - {riesgo}",
    icon=folium.Icon(
        color='red' if temp_predicha <= 0 else 'orange' if temp_predicha <= 2 else 'blue',
        icon='thermometer-half', 
        prefix='fa'
    )
).add_to(mapa)

# MOSTRAR EL MAPA CENTRADO Y GRANDE (esto es lo importante)
st_folium(
    mapa,
    width=725,      # ← 725 es el ancho máximo que Streamlit centra perfecto
    height=550,
    key="mapa_madrid_centrado"
)

# ============================================================
# INFORMACIÓN Y FOOTER
# ============================================================
st.markdown("---")

st.info("""
📍 **Sistema de predicción de heladas para Madrid, Cundinamarca**

- 🤖 Modelos: Ridge Regression (temperatura) + Ridge Classifier (heladas)
- 📊 Entrenamiento: 30 años de datos históricos de IDEAM
""")

st.caption(f"🕐 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")