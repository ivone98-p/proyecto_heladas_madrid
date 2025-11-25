"""
Módulo de notificaciones - Envío de alertas de heladas
Integrado con el predictor de Machine Learning
"""

import logging
from datetime import datetime

# ============================================================
# IMPORT CORREGIDO PARA QUE FUNCIONE EN TODAS LAS PLATAFORMAS
# ============================================================
try:
    # Esta es la línea mágica que funciona en Railway, Render, local, etc.
    from app.predictor import PredictorHeladas
except ImportError as e:
    # Mensaje claro para saber qué pasó
    raise ImportError(
        "No se pudo importar PredictorHeladas. "
        "Verifica que el archivo predictor.py esté dentro de la carpeta 'app/'. "
        f"Error original: {e}"
    )

from config import UMBRALES

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificadorHeladas:
    """
    Clase que gestiona las notificaciones de heladas
    """
    
    def __init__(self):
        """Inicializa el notificador y el predictor"""
        try:
            self.predictor = PredictorHeladas()
            logger.info("Predictor de heladas inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar predictor: {e}")
            self.predictor = None
    
    def obtener_prediccion_actual(self):
        """Obtiene la predicción más reciente"""
        if self.predictor is None:
            return {"error": "Predictor no disponible"}
        
        try:
            return self.predictor.predecir()
        except Exception as e:
            logger.error(f"Error al obtener predicción: {e}")
            return {"error": str(e)}
    
    def necesita_enviar_alerta(self, prediccion):
        """Determina si hay que mandar alerta"""
        if "error" in prediccion:
            return False, None
        
        temp = prediccion['temperatura_predicha']
        
        if temp <= UMBRALES['alto']:      # ≤ 0°C → ALTO
            return True, "ALTO"
        elif temp <= UMBRALES['medio']:   # ≤ 2°C → MEDIO
            return True, "MEDIO"
        else:
            return False, None
    
    def formatear_mensaje_alerta(self, prediccion):
        """Mensaje grande para alertas automáticas"""
        temp = prediccion['temperatura_predicha']
        prob = prediccion['probabilidad_helada']
        riesgo = prediccion['riesgo']
        emoji = prediccion['emoji_riesgo']
        fecha = prediccion['fecha_prediccion']
        
        meses = {1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                 5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'}
        
        fecha_texto = f"{fecha.day} de {meses[fecha.month]} de {fecha.year}"
        
        return f"""
{emoji} **¡ALERTA DE HELADA!** {emoji}

**Madrid, Cundinamarca**

**Fecha**: {fecha_texto}
**Temperatura mínima prevista**: **{temp:.1f}°C**
**Probabilidad de helada**: {prob:.1f}%
**Nivel de riesgo**: **{riesgo}**

Protege tus cultivos esta noche
"""

    def formatear_mensaje_prediccion(self, prediccion):
        """Mensaje para el comando /prediccion"""
        if "error" in prediccion:
            return f"Error: {prediccion['error']}"
        
        temp = prediccion['temperatura_predicha']
        prob = prediccion['probabilidad_helada']
        riesgo = prediccion['riesgo']
        emoji = prediccion['emoji_riesgo']
        fecha = prediccion['fecha_prediccion']
        
        meses = {1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                 5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'}
        
        fecha_texto = f"{fecha.day} de {meses[fecha.month]} de {fecha.year}"
        
        return f"""
{emoji} **Predicción de Heladas**

**Madrid, Cundinamarca**  
**Fecha**: {fecha_texto}

**Temperatura mínima**: **{temp:.1f}°C**  
**Probabilidad de helada**: {prob:.1f}%  
**Nivel de riesgo**: {riesgo}

Actualizado: {datetime.now().strftime('%H:%M:%S')}
"""

    def generar_resumen_diario(self, prediccion):
        """Resumen corto para logs"""
        if "error" in prediccion:
            return f"Error: {prediccion['error']}"
        return f"{prediccion['fecha_prediccion']} | {prediccion['temperatura_predicha']:.1f}°C | {prediccion['riesgo']}"


# ============================================================
# PRUEBA LOCAL
# ============================================================
def probar_notificador():
    print("Probando notificador...")
    n = NotificadorHeladas()
    pred = n.obtener_prediccion_actual()
    print(n.formatear_mensaje_prediccion(pred))

if __name__ == "__main__":
    probar_notificador()