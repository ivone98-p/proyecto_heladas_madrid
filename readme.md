# 🌡️ Sistema de Alertas de Heladas - Madrid, Cundinamarca

Sistema automatizado de predicción y alertas de heladas usando Machine Learning y notificaciones por Telegram.

## 📁 Estructura del Proyecto

```
proyecto_heladas_Madrid/
├── bot/                      # Bot de Telegram
│   ├── telegram_bot.py       # Bot principal
│   ├── database.py           # Gestión de BD
│   ├── notificador.py        # Sistema de notificaciones
│   ├── automatizador.py      # Tareas programadas
│   └── config.py             # Configuración
│
├── app/                      # Aplicación Streamlit
│   ├── app.py                # Interfaz web
│   └── predictor.py          # Motor de predicción ML
│
├── notebooks/                # Análisis y desarrollo
│   ├── 01_consolidacion.ipynb
│   ├── 02_imputacion_y_validacion.ipynb
│   └── 03_modelado_predictivo.ipynb
│
├── Datos/                    # Datos y modelos
│   ├── datos_crudos/         # Datos originales IDEAM
│   ├── datos_consolidados/   # Datos procesados
│   ├── datos_imputados/      # Datos limpios
│   ├── datos_prediccion/     # Resultados
│   └── modelos_entrenados/   # Modelos ML (.pkl)
│
├── Visualizaciones/          # Gráficos y análisis
├── tests/                    # Scripts de prueba
├── .env                      # Variables de entorno (NO SUBIR)
├── .gitignore                # Archivos ignorados
├── requirements.txt          # Dependencias Python
└── README.md                 # Este archivo
```

## 🚀 Instalación

### 1. Clonar repositorio
```bash
git clone <tu-repo>
cd proyecto_heladas_Madrid
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Crear archivo .env en la raíz
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

## 🤖 Ejecutar Bot de Telegram

```bash
cd bot
python telegram_bot.py
```

El bot revisará automáticamente las predicciones en estos horarios:
- 🌅 06:00 AM
- 🌆 06:00 PM
- 🌙 10:00 PM

## 📊 Ejecutar App Streamlit

```bash
cd app
streamlit run app.py
```

Abre tu navegador en: http://localhost:8501

## 🧪 Ejecutar Pruebas

```bash
cd tests
python test_completo.py
```

## 📱 Comandos del Bot

- `/start` - Suscribirte a las alertas
- `/prediccion` - Ver predicción actual
- `/estado` - Ver tu estado de suscripción
- `/stop` - Pausar alertas temporalmente
- `/reanudar` - Reactivar alertas
- `/ayuda` - Mostrar ayuda

## 🔧 Tecnologías

- **Machine Learning**: Ridge Regression + Ridge Classifier
- **Bot**: python-telegram-bot
- **Web**: Streamlit
- **Datos**: 30+ años de datos IDEAM
- **Base de datos**: SQLite

## 📊 Modelos

El sistema utiliza dos modelos:
1. **Predicción de temperatura**: Ridge Regression
2. **Clasificación de heladas**: Ridge Classifier

Entrenados con 30 años de datos históricos del IDEAM.

## 🌡️ Niveles de Riesgo

- 🔴 **MUY ALTO**: Temp ≤ -2°C
- 🟠 **ALTO**: Temp ≤ 0°C
- 🟡 **MEDIO**: Temp ≤ 2°C
- 🟢 **BAJO**: Temp ≤ 4°C
- 🟢 **MUY BAJO**: Temp > 4°C

## 📝 Licencia

MIT

## 👨‍💻 Autor

Proyecto desarrollado para el municipio de Madrid, Cundinamarca.
