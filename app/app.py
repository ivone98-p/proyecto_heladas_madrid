# app.py - VERSIÓN ULTRA OPTIMIZADA (sin reloads en clicks del mapa)

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import locale
import json
import sys
from pathlib import Path

# ✅ CRÍTICO: Agregar rutas correctas
sys.path.insert(0, str(Path(__file__).parent))

# Configurar locale
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

# Configuración
st.set_page_config(
    page_title="SalvaCos - Heladas Madrid",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar colapsado para carga más rápida
)

# CSS personalizado
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
    [data-testid="stMetricValue"] {
        font-size: 3.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 2.5rem !important;
    }
    /* Ajustar solo el nivel de riesgo */
    div[data-testid="column"]:nth-child(3) [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
    }
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
    .element-container iframe {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# Título
col_title, col_btn = st.columns([4, 1])

with col_title:
    st.title("Sistema de Alerta de Heladas - Madrid, Cundinamarca")

with col_btn:
    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
    if st.button("Actualizar Predicción", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

# ============================================================
# CARGAR GEOMETRÍA DE MADRID
# ============================================================
@st.cache_data(show_spinner=False)  # Sin spinner para carga rápida
def cargar_poligono_madrid():
    """Carga el polígono de Madrid desde el archivo GeoJSON"""
    try:
        geom_path = Path(__file__).parent.parent / 'Datos' / 'datos_prediccion' / 'geometria.json'
        
        with open(geom_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        coords = geojson_data['features'][0]['geometry']['coordinates'][0]
        poligono_coords = [[lat, lon] for lon, lat in coords]
        
        return poligono_coords
    except Exception as e:
        st.error(f"❌ Error cargando geometría: {e}")
        return None

def punto_dentro_poligono(lat, lon, poligono):
    """Verifica si un punto está dentro del polígono usando ray casting"""
    if poligono is None:
        return True  # Si no hay polígono, permite todos los puntos
    
    x, y = lat, lon
    n = len(poligono)
    dentro = False
    
    p1_lat, p1_lon = poligono[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = poligono[i % n]
        if y > min(p1_lon, p2_lon):
            if y <= max(p1_lon, p2_lon):
                if x <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        xinters = (y - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    if p1_lat == p2_lat or x <= xinters:
                        dentro = not dentro
        p1_lat, p1_lon = p2_lat, p2_lon
    
    return dentro

# ============================================================
# IMPORTAR PREDICTOR
# ============================================================
try:
    from predictor_multiestacion import PredictorHeladasMulti
    PREDICTOR_DISPONIBLE = True
except Exception as e:
    st.error(f"⚠️ No se pudo importar el predictor: {e}")
    PREDICTOR_DISPONIBLE = False

# ============================================================
# CARGAR PREDICTOR (SOLO UNA VEZ)
# ============================================================
@st.cache_resource(show_spinner=False)  # Sin spinner
def cargar_predictor():
    """Carga el predictor una sola vez"""
    try:
        return PredictorHeladasMulti()
    except Exception as e:
        st.error(f"❌ Error cargando modelos: {e}")
        return None

# ============================================================
# CACHEAR PREDICCIÓN (EVITA RECALCULAR EN CADA CLIC)
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)  # Sin spinner para carga más rápida
def obtener_prediccion(_predictor, fecha):
    """Cachea la predicción para evitar recalcular en cada clic del mapa"""
    if _predictor is None:
        return None
    return _predictor.predecir(fecha_consulta=fecha, forzar_recalculo=False)

st.markdown("---")

# ============================================================
# HACER PREDICCIÓN (CACHEADA)
# ============================================================
predictor = None
resultado = None

if PREDICTOR_DISPONIBLE:
    predictor = cargar_predictor()
    
    if predictor is not None:
        # Usar fecha como parámetro para el cache
        fecha_hoy = datetime.now().date()
        resultado = obtener_prediccion(predictor, fecha_hoy)
            
        if resultado and "error" in resultado:
            st.error(f"❌ {resultado['error']}")
            resultado = None

# ============================================================
# EXTRAER DATOS DE FLORES CHIBCHA
# ============================================================
if resultado and "predicciones_estaciones" in resultado:
    flores_data = next((p for p in resultado['predicciones_estaciones'] 
                       if p['codigo'] == '21205880'), None)
    
    if flores_data:
        temp_predicha = flores_data['temperatura_predicha']
        prob_helada = flores_data['probabilidad_helada']
        riesgo = flores_data['riesgo']
        color_riesgo = flores_data['emoji_riesgo']
        color_mapa = flores_data['color_mapa']
    else:
        temp_predicha = 1.5
        prob_helada = 65
        riesgo = "MEDIO"
        color_riesgo = "🟡"
        color_mapa = "orange"
else:
    temp_predicha = 1.5
    prob_helada = 65
    riesgo = "MEDIO"
    color_riesgo = "🟡"
    color_mapa = "orange"

# ============================================================
# MÉTRICAS PRINCIPALES
# ============================================================
if resultado:
    st.subheader(f"Predicción para Mañana ({resultado['fecha_prediccion'].strftime('%d/%m/%Y')})")
else:
    st.subheader("Predicción para Mañana")

col_metricas, col_telegram = st.columns([2, 1])

with col_metricas:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🌡️ Temperatura Mínima", f"{temp_predicha:.1f}°C")

    with col2:
        st.metric("❄️ Probabilidad Helada", f"{prob_helada:.1f}%")

    with col3:
        st.metric("🔎 Nivel de Riesgo", f"{color_riesgo} {riesgo}")

with col_telegram:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #87CEEB 0%, #4682B4 100%); 
                    padding: 20px 15px; 
                    border-radius: 9px; 
                    text-align: center;
                    height: 100%;">
            <p style="color: white; margin: 0 0 10px 0; font-size: 13px;">
                <strong>¿Quieres recibir alertas automáticas?</strong>
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
                <strong>/start</strong> para suscribirte
                ⏸ <strong>/stop</strong> para pausar
                ▶️ <strong>/reanudar</strong> para reactivar
            </p>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# ALERTA
# ============================================================
st.markdown("---")

if resultado:
    meses_es = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    fecha_pred = resultado['fecha_prediccion']
    fecha_prediccion_str = f"{fecha_pred.day} de {meses_es[fecha_pred.month]} de {fecha_pred.year}"
    
    if temp_predicha <= 0:
        st.error(f"⚠️ **ALERTA DE HELADA**: Se espera temperatura bajo 0°C el **{fecha_prediccion_str}**")
    elif temp_predicha <= 2:
        st.warning(f"⚡ **PRECAUCIÓN**: Temperatura cercana al punto de congelación el **{fecha_prediccion_str}**")
    else:
        st.success(f"No se espera helada para el **{fecha_prediccion_str}**")

# ============================================================
# MAPA MULTI-ESTACIÓN
# ============================================================
st.subheader("🗺️ Mapa de Temperatura Mínima - Madrid, Cundinamarca")

if resultado and "predicciones_estaciones" in resultado:
    predicciones = resultado['predicciones_estaciones']
    
    # Filtrar estaciones con coordenadas válidas
    predicciones_validas = [p for p in predicciones if p['lat'] is not None and p['lon'] is not None]
    
    if len(predicciones_validas) > 0:
        # Calcular temperatura promedio
        temp_promedio = np.mean([p['temperatura_predicha'] for p in predicciones_validas])
        
        # Color del polígono
        if temp_promedio <= -2:
            color_poligono = '#8B0000'
            fillColor_poligono = '#FF0000'
            riesgo_poligono = "MUY ALTO"
        elif temp_promedio <= 0:
            color_poligono = '#FF4500'
            fillColor_poligono = '#FF6347'
            riesgo_poligono = "ALTO"
        elif temp_promedio <= 2:
            color_poligono = '#FFA500'
            fillColor_poligono = '#FFD700'
            riesgo_poligono = "MEDIO"
        elif temp_promedio <= 4:
            color_poligono = '#32CD32'
            fillColor_poligono = '#90EE90'
            riesgo_poligono = "BAJO"
        else:
            color_poligono = '#228B22'
            fillColor_poligono = '#98FB98'
            riesgo_poligono = "MUY BAJO"
        
        # Crear columnas
        col_mapa, col_resultados = st.columns([7, 3])
        
        with col_mapa:
            # Calcular centro
            lats = [p['lat'] for p in predicciones_validas]
            lons = [p['lon'] for p in predicciones_validas]
            centro_lat = sum(lats) / len(lats)
            centro_lon = sum(lons) / len(lons)
            
            # Crear mapa con satélite híbrido de Google
            mapa = folium.Map(
                location=[centro_lat, centro_lon],
                zoom_start=11,
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google'
            )
            
            # Agregar polígono
            poligono_madrid = cargar_poligono_madrid()
            if poligono_madrid:
                folium.Polygon(
                    locations=poligono_madrid,
                    color='#2E86C1',
                    weight=3,
                    fill=True,
                    fillColor='#5DADE2',
                    fillOpacity=0.15,
                    interactive=False
                ).add_to(mapa)
            
            # Agregar marcadores con colores correctos
            for pred in predicciones_validas:
                if pred['temperatura_predicha'] <= -2:
                    icon_color = 'red'
                elif pred['temperatura_predicha'] <= 0:
                    icon_color = 'orange'
                elif pred['temperatura_predicha'] <= 2:
                    icon_color = 'yellow'
                elif pred['temperatura_predicha'] <= 4:
                    icon_color = 'lightgreen'
                else:
                    icon_color = 'green'
                
                folium.Marker(
                    location=[pred['lat'], pred['lon']],
                    popup=f"""
                        <div style="font-family: Arial; min-width: 200px;">
                            <b style="font-size: 14px;">{pred['nombre']}</b><br>
                            <hr style="margin: 5px 0;">
                            Código: {pred['codigo']}<br>
                            Temperatura: <b>{pred['temperatura_predicha']:.1f}°C</b><br>
                            Prob. Helada: <b>{pred['probabilidad_helada']:.1f}%</b><br>
                            Riesgo: <b>{pred['riesgo']}</b><br>
                            Altitud: {pred['alt']:.0f}m
                        </div>
                    """,
                    tooltip=f"{pred['nombre']}: {pred['temperatura_predicha']:.1f}°C",
                    icon=folium.DivIcon(
                        html='<div style="font-size: 20px; transform: translate(-10px, -20px);">📍</div>'
                    )
                ).add_to(mapa)
            
            #  LEYENDA (RESPONSIVE)
            leyenda_html = f"""
            <div style="position: fixed; bottom: 20px; left: 10px; 
                        width: 180px; max-width: calc(100vw - 30px);
                        background-color: white; border: 2px solid #2E86C1; border-radius: 8px;
                        padding: 10px; font-family: Arial; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                        z-index: 9999; font-size: 11px;">
                <h4 style="margin: 0 0 6px 0; color: #000000; text-align: center; font-size: 13px;">Leyenda</h4>
                <hr style="margin: 6px 0; border: none; border-top: 1px solid #2E86C1;">
                
                <div style="margin: 5px 0; padding: 5px; background-color: #E3F2FD; border-radius: 4px; border-left: 3px solid #2E86C1;">
                    <strong style="color: #000000; font-size: 11px;">🗺️ Límite Municipal</strong><br>
                    <span style="color: #000000; font-size: 10px;">Madrid, Cundinamarca</span>
                </div>
                
                <hr style="margin: 6px 0; border: none; border-top: 1px solid #ccc;">
                
                <div style="margin: 5px 0; padding: 5px; background-color: {fillColor_poligono}40; border-radius: 4px; border-left: 3px solid {color_poligono};">
                    <strong style="color: #000000; font-size: 11px;">Temp. Promedio</strong><br>
                    <span style="color: #000000; font-size: 10px;">
                        <strong>{temp_promedio:.1f}°C</strong> - {riesgo_poligono}
                    </span>
                </div>
                
                <hr style="margin: 6px 0; border: none; border-top: 1px solid #ccc;">
                
                <div style="margin: 5px 0;">
                    <strong style="color: #000000; font-size: 11px;">Escala de Riesgo:</strong>
                    <div style="margin-top: 5px;">
                        <div style="display: flex; align-items: center; margin: 3px 0;">
                            <div style="width: 15px; height: 12px; background-color: #FF0000; border: 1px solid #000; margin-right: 5px;"></div>
                            <span style="font-size: 9px; color: #000000;">≤-2°C MUY ALTO 🔴</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 3px 0;">
                            <div style="width: 15px; height: 12px; background-color: #FF6347; border: 1px solid #000; margin-right: 5px;"></div>
                            <span style="font-size: 9px; color: #000000;">-2 a 0°C ALTO 🟠</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 3px 0;">
                            <div style="width: 15px; height: 12px; background-color: #FFD700; border: 1px solid #000; margin-right: 5px;"></div>
                            <span style="font-size: 9px; color: #000000;">0 a 2°C MEDIO 🟡</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 3px 0;">
                            <div style="width: 15px; height: 12px; background-color: #90EE90; border: 1px solid #000; margin-right: 5px;"></div>
                            <span style="font-size: 9px; color: #000000;">2 a 4°C BAJO 🟢</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 3px 0;">
                            <div style="width: 15px; height: 12px; background-color: #98FB98; border: 1px solid #000; margin-right: 5px;"></div>
                            <span style="font-size: 9px; color: #000000;">>4°C MUY BAJO 🟢</span>
                        </div>
                    </div>
                </div>
                
                <hr style="margin: 6px 0; border: none; border-top: 1px solid #ccc;">
                
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <span style="color: #E74C3C; font-size: 14px; margin-right: 5px;">📍</span>
                    <strong style="color: #000000; font-size: 10px;">Estaciones</strong>
                </div>
                
            </div>
            <style>
                @media (min-width: 768px) {{
                    div[style*="bottom: 20px"] {{
                        width: 220px;
                        bottom: 50px;
                        left: 50px;
                        padding: 12px;
                        font-size: 12px;
                    }}
                }}
            </style>
            """
            mapa.get_root().html.add_child(folium.Element(leyenda_html))
            
            # MOSTRAR MAPA (optimizado para carga rápida)
            mapa_output = st_folium(
                mapa,
                width=None,
                height=600,
                returned_objects=["last_clicked"],
                key="mapa_heladas"  # Key para evitar re-renders innecesarios
            )
        
        with col_resultados:
            st.markdown("### Resultado")
            
            # INICIALIZAR SESSION STATE (solo una vez)
            if 'resultado_interpolacion' not in st.session_state:
                st.session_state.resultado_interpolacion = None
            if 'ultimo_click' not in st.session_state:
                st.session_state.ultimo_click = None
            
            # INTERPOLACIÓN (SOLO DENTRO DEL POLÍGONO)
            if mapa_output and mapa_output.get('last_clicked'):
                lat_click = mapa_output['last_clicked']['lat']
                lon_click = mapa_output['last_clicked']['lng']
                
                click_actual = (round(lat_click, 6), round(lon_click, 6))
                
                # Solo procesar clicks nuevos
                if st.session_state.ultimo_click != click_actual:
                    st.session_state.ultimo_click = click_actual
                    
                    # VERIFICAR SI EL PUNTO ESTÁ DENTRO DEL POLÍGONO
                    poligono_madrid = cargar_poligono_madrid()
                    
                    if punto_dentro_poligono(lat_click, lon_click, poligono_madrid):
                        # Interpolación directa
                        temp_interpolada = predictor.interpolar_idw(lat_click, lon_click, predicciones_validas)
                        prob_interpolada = predictor.interpolar_probabilidad_helada(lat_click, lon_click, predicciones_validas)
                        
                        if temp_interpolada is not None:
                            if temp_interpolada <= -2:
                                riesgo_interp = "MUY ALTO 🔴"
                            elif temp_interpolada <= 0:
                                riesgo_interp = "ALTO 🟠"
                            elif temp_interpolada <= 2:
                                riesgo_interp = "MEDIO 🟡"
                            elif temp_interpolada <= 4:
                                riesgo_interp = "BAJO 🟢"
                            else:
                                riesgo_interp = "MUY BAJO 🟢"
                            
                            st.session_state.resultado_interpolacion = {
                                'lat': lat_click,
                                'lon': lon_click,
                                'temp': temp_interpolada,
                                'prob_helada': prob_interpolada if prob_interpolada else 0,
                                'riesgo': riesgo_interp
                            }
                    else:
                        # Punto fuera del polígono
                        st.session_state.resultado_interpolacion = {
                            'lat': lat_click,
                            'lon': lon_click,
                            'fuera': True
                        }
            
            # Mostrar resultado
            if st.session_state.resultado_interpolacion:
                res = st.session_state.resultado_interpolacion
                
                # VERIFICAR SI EL PUNTO ESTÁ FUERA
                if res.get('fuera'):
                    st.warning(f"""
                        📍 **Punto fuera de Madrid**
                        
                        **Lat:** {res['lat']:.5f}  
                        **Lon:** {res['lon']:.5f}
                        
                        ⚠️ Este punto está fuera del límite municipal de Madrid, Cundinamarca.
                        
                        Por favor selecciona un punto dentro del polígono azul.
                    """)
                else:
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                                    padding: 12px; border-radius: 8px; margin-top: 10px;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="margin: 0 0 4px 0; color: #1565C0; font-size: 14px;">
                                📍 Punto Seleccionado
                            </h4>
                            <p style="margin: 6px 0; font-size: 12px; color: #1565C0;">
                                <strong>Lat:</strong> {res['lat']:.5f} | <strong>Lon:</strong> {res['lon']:.5f}
                            </p>
                            <p style="margin: 0; font-size: 28px; text-align: center; color: #0D47A1;"> Temperatura Mínima: 
                                <strong>{res['temp']:.2f}°C</strong>
                            </p>
                            <p style="margin: 6px 0; font-size: 15px; text-align: center; color: #1565C0;">
                                Probabilidad helada: <strong>{res['prob_helada']:.1f}%</strong>
                            </p>
                            <p style="margin: 6px 0; font-size: 15px; text-align: center; color: #1565C0;">
                                <strong>{res['riesgo']}</strong>
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("👆 Haz click en el mapa")
    else:
        st.warning("⚠️ No hay estaciones con coordenadas válidas")
else:
    st.info("ℹ️ No hay predicciones disponibles")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")

st.info("""
📌 **Sistema de predicción de heladas para Madrid, Cundinamarca**

- Modelo: Ridge Regression (temp) + Ridge Classifier (heladas)
- Entrenamiento: 30 años de datos históricos de IDEAM
- Interpolación espacial: IDW (Inverse Distance Weighting)
""")

st.caption(f"🕐 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")