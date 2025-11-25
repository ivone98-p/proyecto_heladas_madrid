# ============================================================
#  APP DE HELADAS - MAPA MULTI-ESTACIÓN (ANCHO COMPLETO)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import locale
import json

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
    layout="wide"  # ← IMPORTANTE: Layout ancho
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
    /* Hacer el mapa de ancho completo */
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
        st.cache_resource.clear()
        st.rerun()

# ============================================================
# CARGAR GEOMETRÍA DE MADRID
# ============================================================
@st.cache_data
def cargar_poligono_madrid():
    """Carga el polígono de Madrid desde el archivo GeoJSON"""
    try:
        with open('Datos/datos_prediccion/geometria.json', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Extraer las coordenadas del polígono
        # El GeoJSON tiene estructura: features[0].geometry.coordinates[0]
        coords = geojson_data['features'][0]['geometry']['coordinates'][0]
        
        # Convertir de [lon, lat] a [lat, lon] para Folium
        poligono_coords = [[lat, lon] for lon, lat in coords]
        
        return poligono_coords
    except Exception as e:
        st.error(f"❌ Error cargando geometría de Madrid: {e}")
        return None

# ============================================================
# IMPORTAR PREDICTOR MULTI-ESTACIÓN
# ============================================================
try:
    from predictor_multiestacion import PredictorHeladasMulti
    PREDICTOR_DISPONIBLE = True
except Exception as e:
    st.error(f"⚠️ No se pudo importar el predictor: {e}")
    PREDICTOR_DISPONIBLE = False

# ============================================================
# CARGAR PREDICTOR (CON CACHÉ)
# ============================================================
@st.cache_resource
def cargar_predictor():
    """Carga el predictor una sola vez"""
    try:
        return PredictorHeladasMulti()
    except Exception as e:
        st.error(f"❌ Error cargando modelos: {e}")
        return None

st.markdown("---")

# ============================================================
# HACER PREDICCIÓN
# ============================================================
predictor = None
resultado = None

if PREDICTOR_DISPONIBLE:
    predictor = cargar_predictor()
    
    if predictor is not None:
        with st.spinner("Generando predicción"):
            resultado = predictor.predecir()

# ============================================================
# EXTRAER DATOS DE FLORES CHIBCHA
# ============================================================
if resultado and "predicciones_estaciones" in resultado:
    flores_data = next((p for p in resultado['predicciones_estaciones'] 
                       if 'FLORES' in p['nombre'].upper() or p['codigo'] == '21205880'), None)
    
    if flores_data:
        temp_predicha = flores_data['temperatura_predicha']
        riesgo = flores_data['riesgo']
        color_riesgo = flores_data['emoji_riesgo']
        color_mapa = flores_data['color_mapa']
        
        # Calcular probabilidad
        if temp_predicha <= 0:
            prob_helada = 85.0
        elif temp_predicha <= 1:
            prob_helada = 70.0
        elif temp_predicha <= 2:
            prob_helada = 45.0
        else:
            prob_helada = 10.0
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
# MÉTRICAS PRINCIPALES (FLORES CHIBCHA)
# ============================================================
if resultado:
    st.subheader(f"Predicción para Mañana ({resultado['fecha_prediccion'].strftime('%d/%m/%Y')})")
else:
    st.subheader("🌡️ Predicción para Mañana")

col_metricas, col_telegram = st.columns([2, 1])

with col_metricas:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🌡️ Temperatura Mínima Predicha", f"{temp_predicha:.1f}°C")

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
                👉 Presiona <strong>/start</strong> para suscribirte
                ❌ Envía <strong>/stop</strong> para pausar
                ▶️ Envía <strong>/reanudar</strong> para reactivar</p>
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
        st.success(f"✅ No se espera helada para el **{fecha_prediccion_str}**")
else:
    if temp_predicha <= 0:
        st.error(f"⚠️ **ALERTA DE HELADA**: Se espera temperatura bajo 0°C")
    elif temp_predicha <= 2:
        st.warning(f"⚡ **PRECAUCIÓN**: Temperatura cercana al punto de congelación")
    else:
        st.success(f"✅ No se espera helada")

# ============================================================
# MAPA MULTI-ESTACIÓN (ANCHO COMPLETO CON COLUMNAS)
# ============================================================
st.subheader("🗺️ Mapa de Temperatura Mínima - Madrid, Cundinamarca")

if resultado and "predicciones_estaciones" in resultado:
    predicciones = resultado['predicciones_estaciones']
    
    if len(predicciones) > 0:
    
        # CALCULAR TEMPERATURA PROMEDIO PARA COLOR DEL POLÍGONO
        temp_promedio = np.mean([p['temperatura_predicha'] for p in predicciones])
        
        # DETERMINAR COLOR DEL POLÍGONO SEGÚN TEMPERATURA PROMEDIO
        if temp_promedio <= -2:
            color_poligono = '#8B0000'
            fillColor_poligono = '#FF0000'
            riesgo_poligono = "MUY ALTO"
            opacity_poligono = 0.25
        elif temp_promedio <= 0:
            color_poligono = '#FF4500'
            fillColor_poligono = '#FF6347'
            riesgo_poligono = "ALTO"
            opacity_poligono = 0.20
        elif temp_promedio <= 2:
            color_poligono = '#FFA500'
            fillColor_poligono = '#FFD700'
            riesgo_poligono = "MEDIO"
            opacity_poligono = 0.15
        elif temp_promedio <= 4:
            color_poligono = '#32CD32'
            fillColor_poligono = '#90EE90'
            riesgo_poligono = "BAJO"
            opacity_poligono = 0.12
        else:
            color_poligono = '#228B22'
            fillColor_poligono = '#98FB98'
            riesgo_poligono = "MUY BAJO"
            opacity_poligono = 0.10
        
        # CREAR COLUMNAS: Mapa (70%) | Resultados (30%)
        col_mapa, col_resultados = st.columns([7, 3])
        
        with col_mapa:
            # Calcular centro del mapa
            lats = [p['lat'] for p in predicciones if p['lat'] is not None]
            lons = [p['lon'] for p in predicciones if p['lon'] is not None]
            
            if lats and lons:
                centro_lat = sum(lats) / len(lats)
                centro_lon = sum(lons) / len(lons)
            else:
                centro_lat = 4.75
                centro_lon = -74.26
            
            # Crear mapa
            mapa = folium.Map(
                location=[centro_lat, centro_lon],
                zoom_start=11,
                tiles='OpenStreetMap'
            )
            
            # CARGAR Y AGREGAR POLÍGONO DE MADRID CON COLOR DINÁMICO
            poligono_madrid = cargar_poligono_madrid()
            
            if poligono_madrid:
                folium.Polygon(
                    locations=poligono_madrid,
                    color='#2E86C1',
                    weight=3,
                    fill=True,
                    fillColor='#5DADE2',
                    fillOpacity=0.15,
                    popup=None,
                    tooltip=None,
                    interactive=False 
                ).add_to(mapa)
            
            # Agregar TODAS las estaciones
            for pred in predicciones:
                if pred['lat'] is None or pred['lon'] is None:
                    continue
                
                # Determinar color del icono según temperatura
                if pred['temperatura_predicha'] <= 0:
                    icon_color = 'red'
                elif pred['temperatura_predicha'] <= 2:
                    icon_color = 'orange'
                elif pred['temperatura_predicha'] <= 4:
                    icon_color = 'lightblue'
                else:
                    icon_color = 'lightgreen'
                
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
                        html="""
                        <div style="
                        font-size: 20px;      
                        line-height: 20px;
                        transform: translate(-10px, -20px);
                     ">📍</div>
                    """
               )   
            ).add_to(mapa)
                    
                
            
            # LEYENDA DEL MAPA CON ESCALA DE COLORES
            leyenda_html = f"""
            <div style="position: fixed; 
                        bottom: 50px; 
                        left: 50px; 
                        width: 270px; 
                        background-color: white; 
                        border: 2px solid #2E86C1;
                        border-radius: 10px;
                        padding: 15px;
                        font-family: Arial;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                        z-index: 9999;">
                <h4 style="margin: 0 0 10px 0; color: #2E86C1; text-align: center;">
                    Leyenda
                </h4>
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #2E86C1;">
                
                <!-- Límite municipal -->
                <div style="margin: 8px 0; padding: 8px; background-color: #E3F2FD; border-radius: 5px; border-left: 4px solid #2E86C1;">
                    <strong style="color: #000;">🗺️ Límite Municipal</strong><br>
                    <span style="color: #333; font-size: 12px;">
                        Madrid, Cundinamarca
                    </span>
                </div>
                
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #ccc;">
                
                <!-- Información del polígono -->
                <div style="margin: 8px 0; padding: 8px; background-color: {fillColor_poligono}40; border-radius: 5px; border-left: 4px solid {color_poligono};">
                    <strong style="color: #000;">📊 Temperatura Promedio</strong><br>
                    <span style="color: #333; font-size: 12px;">
                        Temp. Promedio: <strong>{temp_promedio:.1f}°C</strong><br>
                        Riesgo General: <strong>{riesgo_poligono}</strong>
                    </span>
                </div>
                
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #ccc;">
                
                <!-- Escala de colores -->
                <div style="margin: 8px 0;">
                    <strong style="color: #000; font-size: 13px;">🌡️ Escala de Riesgo:</strong>
                    <div style="margin-top: 8px;">
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 20px; height: 15px; background-color: #FF0000; border: 1px solid #8B0000; margin-right: 8px;"></div>
                            <span style="font-size: 11px; color: #000;">≤ -2°C (MUY ALTO)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 20px; height: 15px; background-color: #FF6347; border: 1px solid #FF4500; margin-right: 8px;"></div>
                            <span style="font-size: 11px; color: #000;">-2°C a 0°C (ALTO)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 20px; height: 15px; background-color: #FFD700; border: 1px solid #FFA500; margin-right: 8px;"></div>
                            <span style="font-size: 11px; color: #000;">0°C a 2°C (MEDIO)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 20px; height: 15px; background-color: #ADD8E6; border: 1px solid #87CEEB; margin-right: 8px;"></div>
                            <span style="font-size: 11px; color: #000;">2°C a 4°C (BAJO)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 20px; height: 15px; background-color: #90EE90; border: 1px solid #32CD32; margin-right: 8px;"></div>
                            <span style="font-size: 11px; color: #000;">> 4°C (MUY BAJO)</span>
                        </div>
                    </div>
                </div>
                
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #ccc;">
                
                <div style="margin: 8px 0; color: #000000;">
                    <span style="color: #E74C3C; font-size: 18px; margin-right: 8px;">📍</span>
                    <strong>Estaciones Meteorológicas</strong>
                </div>
            </div>
            """
            mapa.get_root().html.add_child(folium.Element(leyenda_html))
            
            # Guardar el estado del click
            if 'ultimo_click' not in st.session_state:
                st.session_state.ultimo_click = None
            
            # MOSTRAR MAPA
            mapa_output = st_folium(
                mapa,
                width=None,
                height=600,
                key="mapa_madrid_multiestacion",
                returned_objects=["last_clicked"]
            )
        
        # COLUMNA DERECHA: RESULTADOS DE INTERPOLACIÓN (MÁS COMPACTA)
        with col_resultados:
            st.markdown("### Resultado")
            
            # Placeholder inicial
            if 'resultado_interpolacion' not in st.session_state:
                st.session_state.resultado_interpolacion = None
            
            # PROCESAMIENTO DE CLICKS
            if mapa_output and mapa_output.get('last_clicked'):
                lat_click = mapa_output['last_clicked']['lat']
                lon_click = mapa_output['last_clicked']['lng']
                
                # Evitar procesar el mismo click múltiples veces
                click_actual = (lat_click, lon_click)
                if st.session_state.ultimo_click != click_actual:
                    st.session_state.ultimo_click = click_actual
                    
                    # Función para verificar si el punto está dentro del polígono
                    def punto_en_poligono(lat, lon, poligono):
                        """Verifica si un punto está dentro de un polígono usando ray-casting"""
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
                    
                    # Verificar si el click está dentro de Madrid
                    if poligono_madrid and punto_en_poligono(lat_click, lon_click, poligono_madrid):
                        # INTERPOLAR TEMPERATURA
                        temp_interpolada = predictor.interpolar_idw(lat_click, lon_click, predicciones, potencia=2)
                        
                        # INTERPOLAR PROBABILIDAD DE HELADA
                        prob_helada_interpolada = predictor.interpolar_probabilidad_helada(lat_click, lon_click, predicciones, potencia=2)
                        
                        if temp_interpolada is not None:
                            # Determinar riesgo
                            if temp_interpolada <= -2:
                                riesgo_interp = "MUY ALTO 🔴"
                                color_interp = "#FF0000"
                            elif temp_interpolada <= 0:
                                riesgo_interp = "ALTO 🟠"
                                color_interp = "#FF8C00"
                            elif temp_interpolada <= 2:
                                riesgo_interp = "MEDIO 🟡"
                                color_interp = "#FFD700"
                            elif temp_interpolada <= 4:
                                riesgo_interp = "BAJO 🟢"
                                color_interp = "#32CD32"
                            else:
                                riesgo_interp = "MUY BAJO 🟢"
                                color_interp = "#32CD32"
                            
                            # Guardar resultado en session_state
                            st.session_state.resultado_interpolacion = {
                                'lat': lat_click,
                                'lon': lon_click,
                                'temp': temp_interpolada,
                                'prob_helada': prob_helada_interpolada if prob_helada_interpolada else 0,
                                'riesgo': riesgo_interp,
                                'color': color_interp,
                                'num_estaciones': len(predicciones)
                            }
                        else:
                            st.session_state.resultado_interpolacion = None
                            st.error("❌ No se pudo calcular la temperatura")
                    else:
                        st.session_state.resultado_interpolacion = None
                        st.warning("⚠️ Fuera del límite municipal")
            
            # MOSTRAR RESULTADO GUARDADO (VERSIÓN COMPACTA)
            if st.session_state.resultado_interpolacion:
                res = st.session_state.resultado_interpolacion
                
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                                padding: 12px; 
                                border-radius: 8px; 
                                border-left: 5px solid #2196F3;
                                margin-top: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 4px 0; color: #1565C0; font-size: 14px;">
                            Punto Seleccionado
                        <p style="margin: 6px 0; font-size: 12px; color: #1565C0; line-height: 1.4;">
                            <strong>Lat:</strong> {res['lat']:.5f} | <strong>Lon:</strong> {res['lon']:.5f}
                        </h4>
                        <p style="margin: 0px 0; font-size: 28px; text-align: center; color: #0D47A1;">
                            <strong>Temperatura Mínima: {res['temp']:.2f}°C</strong>
                        </p>
                        <p style="margin: 6px 0; font-size: 15px; text-align: center; color: #1565C0;">
                            <strong>Probabilidad Helada: {res['prob_helada']:.1f}%</strong>
                        </p>
                        <p style="margin: 6px 0; font-size: 15px; text-align: center; color: #1565C0;">
                            <strong>{res['riesgo']}</strong>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("👆 Haz click en el mapa para ver la temperatura en ese punto")

else:
    # Fallback: Mapa simple con Flores Chibcha
    madrid_lat = 4.789722222
    madrid_lon = -74.26477778
    
    mapa = folium.Map(
        location=[madrid_lat, madrid_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    folium.Marker(
        location=[madrid_lat, madrid_lon],
        popup=f"<b>Flores Chibcha</b><br>Temperatura: <b>{temp_predicha:.1f}°C</b><br>Riesgo: <b>{riesgo}</b>",
        tooltip=f"{temp_predicha:.1f}°C - {riesgo}",
        icon=folium.Icon(
            color='red' if temp_predicha <= 0 else 'orange' if temp_predicha <= 2 else 'blue',
            icon='thermometer-half', 
            prefix='fa'
        )
    ).add_to(mapa)
    
    st_folium(mapa, width=None, height=600, key="mapa_fallback")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")

st.info("""
📌 **Sistema de predicción de heladas para Madrid, Cundinamarca**

- Modelo: Ridge Regression (temp) + Ridge Classifier (heladas)
- Entrenamiento: 30 años de datos históricos de IDEAM
- 7 modelos independientes (uno por estación)
- Interpolación espacial: IDW (Inverse Distance Weighting)
""")

st.caption(f"🕐 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")