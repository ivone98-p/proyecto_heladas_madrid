"""
Configuración del bot de alertas de heladas - Madrid, Cundinamarca
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================
# CONFIGURACIÓN DEL BOT
# ============================================================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8554319495:AAF3-CmsOZk9QiPsCUSziQk6DWz9gVwLshA')

# Base de datos
DB_PATH = '../suscriptores.db'

# ============================================================
# UMBRALES DE TEMPERATURA (según tu predictor.py)
# ============================================================
UMBRALES = {
    'muy_alto': -2,    # Temp <= -2°C
    'alto': 0,         # Temp <= 0°C
    'medio': 2,        # Temp <= 2°C
    'bajo': 4          # Temp <= 4°C
}

# ============================================================
# HORARIOS DE CHEQUEO AUTOMÁTICO
# ============================================================
# Horarios en formato 24h para revisar predicción y enviar alertas
HORARIOS_CHEQUEO = ['06:00', '18:00', '22:00']  # Mañana, tarde y noche

# ============================================================
# MENSAJES DEL BOT
# ============================================================
MENSAJES = {
    'bienvenida': """
❄️ ¡Bienvenido al Sistema de Alertas de Heladas! ❄️

📍 **Municipio**: Madrid, Cundinamarca

Este bot te enviará notificaciones automáticas cuando se detecte riesgo de heladas en la región.

**Comandos disponibles:**
/start - Suscribirte a las alertas
/stop - Pausar alertas temporalmente
/reanudar - Reactivar alertas
/estado - Ver tu estado de suscripción
/prediccion - Ver predicción actual
/info - Información del sistema
/ayuda - Mostrar ayuda

🌾 ¡Gracias por suscribirte! Te mantendremos informado.
    """,
    
    'ya_suscrito': """
✅ Ya estás suscrito a las alertas de heladas.

Usa /prediccion para ver la predicción actual.
    """,
    
    'suscripcion_exitosa': """
✅ ¡Suscripción exitosa!

Recibirás alertas automáticas cuando:
🔴 Temperatura ≤ 0°C (Riesgo ALTO)
🟡 Temperatura ≤ 2°C (Riesgo MEDIO)

Usa /prediccion para consultar en cualquier momento.
    """,
    
    'pausado': """
⏸️ Alertas pausadas temporalmente.

No recibirás notificaciones hasta que uses /reanudar
Tu suscripción sigue activa.
    """,
    
    'reanudado': """
▶️ ¡Alertas reactivadas!

Volverás a recibir notificaciones automáticas de heladas.
    """,
    
    'no_suscrito': """
❌ No estás suscrito al sistema de alertas.

Usa /start para suscribirte y recibir notificaciones.
    """,
    
    'info': """
ℹ️ **Sistema de Alertas de Heladas**

📍 **Ubicación**: Madrid, Cundinamarca
🤖 **Tecnología**: Machine Learning (Ridge Regression + Ridge Classifier)
📊 **Datos**: 30+ años de datos históricos IDEAM

**Niveles de alerta:**
🔴 MUY ALTO: Temp ≤ -2°C
🟠 ALTO: Temp ≤ 0°C  
🟡 MEDIO: Temp ≤ 2°C
🟢 BAJO: Temp ≤ 4°C
🟢 MUY BAJO: Temp > 4°C

**Horarios de revisión:**
🌅 06:00 AM - Revisión matutina
🌆 06:00 PM - Revisión vespertina
🌙 10:00 PM - Revisión nocturna

**Privacidad:**
Solo guardamos tu ID de chat (necesario para enviar mensajes).
No almacenamos datos personales como nombre o teléfono.

**Fuente de datos:**
IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales)
    """,
    
    'ayuda': """
🆘 **Ayuda - Comandos Disponibles**

**Gestión de suscripción:**
/start - Suscribirte a las alertas
/stop - Pausar notificaciones temporalmente  
/reanudar - Reactivar las notificaciones
/estado - Ver si estás activo/pausado

**Información:**
/prediccion - Ver predicción actual de temperatura
/info - Información del sistema de alertas
/ayuda - Mostrar este mensaje

**¿Cómo funciona?**
1. Te suscribes con /start
2. El sistema revisa la predicción 3 veces al día
3. Si hay riesgo de helada, recibes una alerta automática
4. Puedes consultar la predicción cuando quieras con /prediccion

**¿No recibes alertas?**
Verifica que:
✓ No hayas pausado las notificaciones (/stop)
✓ Tu chat esté activo con el bot
✓ Hayas usado /start para suscribirte

**Soporte:**
Para reportar problemas o sugerencias, contacta al administrador del sistema.
    """
}

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'