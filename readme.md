# SalvaCos - Sistema de Predicción de Heladas

Sistema de predicción de heladas para Madrid, Cundinamarca, basado en machine learning y datos históricos de 30 años del IDEAM.


🌐 **Aplicación Web**: [salvacos.streamlit.app](https://salvacos.streamlit.app/)  
🤖 **Bot de Telegram**: [@MadridHeladasBot](https://t.me/MadridHeladasBot)  
📂 **Repositorio**: [github.com/ivone98-p/proyecto_heladas_madrid](https://github.com/ivone98-p/proyecto_heladas_madrid)

---

## Descripción

**SalvaCos** es una aplicación web diseñada para ayudar a agricultores y productores de Madrid, Cundinamarca a proteger sus cultivos mediante predicciones precisas de heladas con 24 horas de anticipación.

Este proyecto fue desarrollado como trabajo de grado para la **Especialización en Sistemas de Información Geográfica** de la **Universidad Distrital Francisco José de Caldas**.

### Características principales

- **Predicción precisa** de temperatura mínima para el día siguiente
- **Probabilidad de helada** calculada con modelos de clasificación
- **Mapa interactivo** con vista satelital de Google
- **Interpolación espacial** IDW para cualquier punto del municipio
- **Bot de Telegram** para alertas automáticas diarias
- **Interfaz responsive** optimizada para móvil y desktop
- **Sistema de caché** para carga rápida

---

## Arquitectura del Sistema

### Modelos de Predicción

El sistema utiliza una **arquitectura híbrida** de machine learning:

#### Modelo Dedicado para Madrid (Flores Chibcha - 21205880)

- **Algoritmo**: Ridge Regression + Ridge Classifier
- **Datos de entrenamiento**: 10,971 registros (1995-2025)
- **Split**: 80/20 (Train: 8,752 | Test: 2,188)

**Modelo de Temperatura:**
- Features: 52 variables
- R² = 0.4006
- RMSE = 2.12°C
- MAE = 1.69°C

**Modelo de Heladas:**
- Features: 78 variables (incluye precipitación y temperatura máxima)
- Accuracy = 93.6%
- Recall = 90.91% (detecta 20 de 22 heladas)
- Precision = 12.66%
- F1-Score = 0.22
- Falsas alarmas: 138
- Heladas perdidas: 2

#### Modelo Unificado para Otras Estaciones (6 estaciones)

- **Algoritmo**: Ridge Regression + Ridge Classifier
- **Estaciones incluidas**: 21206060, 21205420, 21205960, 21205980, 21205870, 21205940

**Métricas Promedio por Estación:**

| Estación | R² Temp | RMSE Temp | MAE Temp | Recall Helada | Falsas Alarmas | Heladas Perdidas |
|----------|---------|-----------|----------|---------------|----------------|------------------|
| 21205420 | 0.3371  | 2.17°C    | 1.76°C   | 84.62%        | 243            | 2                |
| 21205960 | 0.3182  | 2.07°C    | 1.66°C   | 90.91%        | 224            | 1                |
| 21205870 | 0.3074  | 1.68°C    | 1.37°C   | 100.00%       | 59             | 0                |
| 21206060 | 0.2502  | 1.83°C    | 1.39°C   | 83.33%        | 93             | 1                |
| 21205940 | 0.2326  | 2.14°C    | 1.74°C   | 80.00%        | 133            | 1                |
| 21205980 | 0.2115  | 2.18°C    | 1.77°C   | 71.43%        | 96             | 2                |

### Features del Modelo

**Variables Temporales:**
- Rezagos: 1, 2, 3, 7, 14, 21, 30 días
- Rolling statistics: media, std, min, max (ventanas de 3, 7, 14, 30 días)
- Variables cíclicas: sin/cos de mes, día del año, semana, día de la semana
- Diferencias: 1, 7, 30 días
- Tendencias: 7, 14, 30 días
- Aceleraciones

**Variables Adicionales (Modelo de Heladas):**
- Precipitación promedio y acumulada
- Temperatura máxima
- Rango térmico
- Variables binarias de precipitación

### Interpolación Espacial

- **Método**: IDW (Inverse Distance Weighting)
- **Potencia**: 2
- **Restricción**: Solo dentro del polígono municipal de Madrid

---

## Tecnologías

### Backend

- **Python 3.8+**
- **scikit-learn**: Modelos de machine learning
- **pandas**: Procesamiento de datos
- **numpy**: Cálculos numéricos
- **joblib**: Serialización de modelos

### Frontend

- **Streamlit**: Framework web
- **Folium**: Mapas interactivos
- **streamlit-folium**: Integración de mapas

### Bot y Automatización

- **python-telegram-bot**: Bot de Telegram
- **SQLite**: Base de datos de suscriptores
- **APScheduler**: Tareas programadas

### Infraestructura

- **pytz**: Manejo de zonas horarias (Colombia UTC-5)
- **Google Maps Tile API**: Imágenes satelitales

---

## Estructura del Proyecto
```
SalvaCos/
│
├── app/
│   ├── app.py                          # Aplicación Streamlit principal
│   └── predictor_multiestacion.py      # Motor de predicción
│
├── Datos/
│   ├── modelos_entrenados/             # Modelo dedicado de Madrid
│   │   ├── modelo_temperatura_ridge.pkl
│   │   ├── modelo_helada_ridge.pkl
│   │   ├── scaler_temperatura.pkl
│   │   ├── scaler_helada.pkl
│   │   ├── features_temperatura.pkl
│   │   └── features_helada.pkl
│   │
│   ├── modelo_unificado_SIN_MADRID/    # Modelo para otras estaciones
│   │   ├── modelo_temperatura_SIN_MADRID.pkl
│   │   ├── modelo_helada_SIN_MADRID.pkl
│   │   ├── scaler_temperatura_SIN_MADRID.pkl
│   │   ├── scaler_helada_SIN_MADRID.pkl
│   │   ├── features_temperatura_SIN_MADRID.pkl
│   │   └── features_helada_SIN_MADRID.pkl
│   │
│   ├── datos_imputados/                # Datos históricos procesados
│   │   └── cundinamarca_imputado_v1.csv
│   │
│   └── datos_prediccion/               # Metadata de estaciones
│       ├── geometria.json              # Polígono municipal
│       └── metadata_estaciones.csv     # Coordenadas de estaciones
│
├── notebooks/                # Análisis y desarrollo
│   ├── 01_consolidacion.ipynb
│   ├── 02_imputacion_y_validacion.ipynb
│   └── 03_modelado_predictivo.ipynb
│
├── bot/                      # Bot de Telegram
│   ├── telegram_bot.py       # Bot principal
│   ├── database.py           # Gestión de BD
│   ├── notificador.py        # Sistema de notificaciones
│   ├── automatizador.py      # Tareas programadas
│   └── config.py             # Configuración
│
├── Visualizaciones/          # Gráficos y análisis
├── tests/                    # Scripts de prueba
├── .env                      # Variables de entorno (NO SUBIR)
├── .gitignore                # Archivos ignorados
├── requirements.txt          # Dependencias Python
└── README.md                 # Este archivo
```

---

## Instalación

### Prerequisitos

- Python 3.8 o superior
- pip

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/ivone98-p/proyecto_heladas_madrid.git
cd proyecto_heladas_madrid
```

### Paso 2: Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### Paso 3: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno

Crea un archivo `.env` en la raíz:
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### Paso 5: Ejecutar la aplicación
```bash
cd app
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`

---

## Datos

### Fuente de Datos

- **Origen**: IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales)
- **Período**: 30 años de datos históricos (1995-2025)
- **Registros**: 10,971 observaciones diarias
- **Variables**: Temperatura mínima, máxima, precipitación
- **Frecuencia**: Diaria

### Estaciones Meteorológicas

| Código   | Nombre                  | Altitud | Latitud   | Longitud    |
|----------|-------------------------|---------|-----------|-------------|
| 21201070 | El Corazón Facatativá   | 2845m   | 4.8654    | -74.2894    |
| 21201210 | El Hato Tenjo           | 3378m   | 4.8664    | -74.1539    |
| 21205420 | Tibaitatá Mosquera      | 2543m   | 4.6887    | -74.2056    |
| 21205770 | Base Aérea Madrid       | 2550m   | 4.7288    | -74.2725    |
| 21205870 | El Salitre Bojacá       | 2570m   | 4.7389    | -74.3343    |
| 21205880 | **Flores Chibcha Madrid** | **2550m** | **4.7897** | **-74.2648** |
| 21205940 | Villa Inés Facatativá   | 2590m   | 4.8321    | -74.3806    |
| 21205960 | Tachi Subachoque        | 2650m   | 4.9391    | -74.1526    |
| 21205980 | Granja Providencia Tenjo| 2560m   | 4.7924    | -74.2009    |
| 21206060 | Casablanca Madrid       | 2575m   | 4.7171    | -74.2533    |
| 21206280 | Acapulco Bojacá         | 2680m   | 4.6482    | -74.3204    |

**Nota**: La estación principal (Flores Chibcha - 21205880) cuenta con un modelo dedicado optimizado.

---

## Uso

### Interfaz Web

**Accede a**: [salvacos.streamlit.app](https://salvacos.streamlit.app/)

**Vista Principal**: Muestra la predicción para mañana
- Temperatura mínima esperada
- Probabilidad de helada (0-100%)
- Nivel de riesgo (Muy Bajo, Bajo, Medio, Alto, Muy Alto)

**Mapa Interactivo**:
- Vista satelital de Google con relieve
- Haz clic en cualquier punto del mapa
- Obtén predicción interpolada para esa ubicación
- **Restricción**: Solo funciona dentro del límite municipal de Madrid

**Bot de Telegram**: [@MadridHeladasBot](https://t.me/MadridHeladasBot)
- `/start` - Suscribirse a alertas diarias
- `/stop` - Pausar alertas temporalmente
- `/reanudar` - Reactivar alertas
- **Alertas automáticas**: Recibe notificaciones diarias si hay riesgo de helada

### Niveles de Riesgo

| Temperatura | Riesgo      | Color | Emoji | Acción Recomendada |
|-------------|-------------|-------|-------|--------------------|
| ≤ -2°C      | MUY ALTO    | Rojo  | 🔴 | Protección urgente inmediata |
| -2°C a 0°C  | ALTO        | Naranja | 🟠 | Preparar sistemas de protección |
| 0°C a 2°C   | MEDIO       | Amarillo | 🟡 | Monitoreo cercano y prevención |
| 2°C a 4°C   | BAJO        | Verde claro | 🟢 | Vigilancia rutinaria |
| > 4°C       | MUY BAJO    | Verde | 🟢 | Sin riesgo significativo |

---

## Optimizaciones Implementadas

### Sistema de Caché Inteligente

- Predicciones cacheadas por 1 hora
- Evita recálculos innecesarios en cada interacción
- Carga instantánea después de la primera consulta

### Gestión de Zona Horaria

- Todas las fechas sincronizadas con hora de Colombia (UTC-5)
- Predicción alineada con el amanecer local

### Diseño Responsive

- Leyenda del mapa adaptativa (180px móvil / 220px desktop)
- Interfaz optimizada para diferentes tamaños de pantalla
- Mapa satelital de alta calidad con datos de Google

### Validación Geográfica

- Sistema de ray casting para verificar puntos dentro del municipio
- Interpolación IDW solo en área municipal válida
- Mensajes claros cuando se seleccionan puntos fuera de límites

---

## Configuración Avanzada

### Modificar Estaciones

Edita `Datos/datos_prediccion/metadata_estaciones.csv`:
```csv
CodigoEstacion,nombre,lat,lon,alt
21205880,Flores Chibcha Madrid,4.789722222,-74.26477778,2550
21206060,Casablanca Madrid,4.717111111,-74.25333333,2575
```

### Ajustar Parámetros de Interpolación

En `predictor_multiestacion.py`:
```python
def interpolar_idw(self, lat, lon, predicciones, potencia=2):
    # Cambia 'potencia' para ajustar la influencia de distancia
    # potencia=1: más suave
    # potencia=3: más localizado
```

### Personalizar Umbrales de Riesgo

En `app.py`:
```python
if temp_predicha <= -2:
    riesgo = "MUY ALTO"
elif temp_predicha <= 0:
    riesgo = "ALTO"
elif temp_predicha <= 2:
    riesgo = "MEDIO"
# Modifica estos valores según necesidades locales
```

---

## Interpretación de Métricas

### R² (Coeficiente de Determinación)

- **Madrid**: 0.40 → El modelo explica el 40% de la variabilidad
- **Rango típico**: 0.3-0.5 es común en predicción meteorológica a corto plazo

### RMSE y MAE

- **RMSE**: Error cuadrático medio (penaliza errores grandes)
- **MAE**: Error absoluto medio (más interpretable)
- **Madrid MAE = 1.69°C**: El modelo se equivoca en promedio ±1.7°C

### Recall vs Precision en Heladas

- **Recall alto (90.91%)**: Detecta 20 de 22 heladas reales (objetivo prioritario)
- **Precision baja (12.66%)**: Muchas falsas alarmas, pero es preferible a perder heladas
- **Filosofía**: Es mejor alertar de más que perder una helada crítica

---

## Bot de Telegram

### Funcionalidades

**Suscripción Automática**
- Solo se envían alertas cuando hay riesgo de helada

**Comandos Disponibles**
- `/start` - Activar alertas
- `/stop` - Pausar temporalmente
- `/reanudar` - Reactivar alertas
- `/estado` - Ver estado actual de suscripción

**Base de Datos**
- SQLite local para gestionar suscriptores
- Registro de fecha de suscripción y estado

---

## Notas Técnicas

### Limitaciones Conocidas

1. **Predicción a 1 día**: El modelo solo predice para mañana, no para días posteriores
2. **Falsas alarmas**: El sistema prioriza detectar heladas (alto recall) sobre precisión
3. **Dependencia de datos**: Requiere datos históricos actualizados mensualmente
4. **Área geográfica**: Solo válido para Madrid, Cundinamarca

### Actualización de Datos

Los datos deben actualizarse periódicamente:

1. Descargar nuevos datos del IDEAM
2. Ejecutar notebook `01_consolidacion.ipynb`
3. Ejecutar `02_imputacion_y_validacion.ipynb`
4. Re-entrenar modelos con `03_modelado_predictivo.ipynb`

---

## Roadmap Futuro

- Predicción a 3-5 días
- Integración con más estaciones del departamento
- Alertas por WhatsApp
- Dashboard de métricas históricas de aciertos
- Exportar reportes de predicción en PDF
- Recomendaciones específicas por tipo de cultivo
- Integración con sensores IoT locales

---

## Información Académica

**Proyecto de Grado**  
Especialización en Sistemas de Información Geográfica  
Universidad Distrital Francisco José de Caldas  
Bogotá, Colombia  
2025

---

## Contacto

- **Bot de Telegram**: [@MadridHeladasBot](https://t.me/MadridHeladasBot)
- **Aplicación Web**: [salvacos.streamlit.app](https://salvacos.streamlit.app/)
- **Repositorio**: [github.com/ivone98-p/proyecto_heladas_madrid](https://github.com/ivone98-p/proyecto_heladas_madrid)

---

## Agradecimientos

- **IDEAM** - Por proporcionar los datos meteorológicos históricos de calidad
- **Universidad Distrital Francisco José de Caldas** - Por el apoyo académico y técnico

---

**Desarrollado con ❤️ para proteger los cultivos de Madrid, Cundinamarca**

*Última actualización: Noviembre 2025*