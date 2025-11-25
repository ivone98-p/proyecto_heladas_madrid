"""
Módulo de notificaciones - Envío de alertas de heladas
Integrado con el predictor de Machine Learning
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURAR PATH PARA IMPORTAR PREDICTOR (FUNCIONA EN RAILWAY)
# ============================================================
current_dir = Path(__file__).resolve().parent  # Carpeta bot/
parent_dir = current_dir.parent  # Carpeta raíz del proyecto

# Añadir la raíz del proyecto al path para que encuentre app/
sys.path.insert(0, str(parent_dir))

# Importar predictor desde app/
try:
    from predictor_multiestacion import PredictorHeladasMulti
except ImportError as e:
    raise ImportError(f"No se pudo importar predictor desde {parent_dir}: {e}")

from config import UMBRALES

logger = logging.getLogger(__name__)


class NotificadorHeladas:
    """
    Clase que gestiona las notificaciones de heladas
    Integrado con el sistema de predicción ML
    """
   
    def __init__(self):
        """Inicializa el notificador y el predictor"""
        try:
            self.predictor = PredictorHeladasMulti()
            logger.info("✅ Predictor de heladas inicializado")
        except Exception as e:
            logger.error(f"❌ Error al inicializar predictor: {e}")
            self.predictor = None
   
    def obtener_prediccion_actual(self):
        """
        Obtiene la predicción actual de heladas
       
        Returns:
            dict: Predicción con temperatura, probabilidad, riesgo, etc.
        """
        if self.predictor is None:
            return {"error": "Predictor no disponible"}
       
        try:
            resultado = self.predictor.predecir()
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al obtener predicción: {e}")
            return {"error": str(e)}
   
    def necesita_enviar_alerta(self, prediccion):
        """
        Determina si se debe enviar una alerta según la predicción
       
        Args:
            prediccion: dict con datos de predicción
           
        Returns:
            tuple: (debe_enviar: bool, nivel_alerta: str)
        """
        if "error" in prediccion:
            return False, None
       
        temp = prediccion['temperatura_predicha']
       
        # Enviar alerta solo si:
        # - Temperatura <= 0°C (ALTO)
        # - Temperatura <= 2°C (MEDIO)
       
        if temp <= UMBRALES['alto']: # <= 0°C
            return True, "ALTO"
        elif temp <= UMBRALES['medio']: # <= 2°C
            return True, "MEDIO"
        else:
            return False, None
   
    def formatear_mensaje_alerta(self, prediccion):
        """
        Formatea el mensaje de alerta para Telegram
       
        Args:
            prediccion: dict con datos de predicción
           
        Returns:
            str: mensaje formateado para enviar
        """
        temp = prediccion['temperatura_predicha']
        prob = prediccion['probabilidad_helada']
        riesgo = prediccion['riesgo']
        emoji = prediccion['emoji_riesgo']
        fecha = prediccion['fecha_prediccion']
       
        # Convertir fecha a texto legible
        meses_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
       
        dia = fecha.day
        mes = meses_es[fecha.month]
        anio = fecha.year
        fecha_texto = f"{dia} de {mes} de {anio}"
       
        # Mensaje base
        mensaje = f"""
{emoji} **ALERTA DE HELADA - Madrid, Cundinamarca**
📅 **Fecha**: {fecha_texto}
🌡️ **Temperatura predicha**: {temp:.1f}°C
❄️ **Probabilidad de helada**: {prob:.1f}%
🔎 **Nivel de riesgo**: {riesgo}
"""
       
        return mensaje
   
    def formatear_mensaje_prediccion(self, prediccion):
        """
        Formatea el mensaje de predicción para comando /prediccion
       
        Args:
            prediccion: dict con datos de predicción
           
        Returns:
            str: mensaje formateado
        """
        if "error" in prediccion:
            return f"❌ Error: {prediccion['error']}"
       
        temp = prediccion['temperatura_predicha']
        prob = prediccion['probabilidad_helada']
        riesgo = prediccion['riesgo']
        emoji = prediccion['emoji_riesgo']
        fecha = prediccion['fecha_prediccion']
       
        # Convertir fecha
        meses_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
       
        dia = fecha.day
        mes = meses_es[fecha.month]
        anio = fecha.year
        fecha_texto = f"{dia} de {mes} de {anio}"
       
        mensaje = f"""
{emoji} **Predicción de Heladas**
📍 Madrid, Cundinamarca
📅 **Fecha**: {fecha_texto}
🌡️ **Temperatura predicha**: {temp:.1f}°C
❄️ **Probabilidad de helada**: {prob:.1f}%
🔎 **Nivel de riesgo**: {riesgo}
📊 **Contexto:**
• Temperatura ayer: {prediccion['temp_ayer']:.1f}°C
• Promedio 7 días: {prediccion['temp_promedio_7d']:.1f}°C
• Mínima 7 días: {prediccion['temp_minima_7d']:.1f}°C
• Cambio esperado: {prediccion['cambio_esperado']:+.1f}°C
🕐 Actualizado: {datetime.now().strftime('%H:%M:%S')}
"""
       
        return mensaje
   
    def generar_resumen_diario(self, prediccion):
        """
        Genera un resumen breve para logs o reportes
       
        Args:
            prediccion: dict con datos de predicción
           
        Returns:
            str: resumen breve
        """
        if "error" in prediccion:
            return f"Error en predicción: {prediccion['error']}"
       
        temp = prediccion['temperatura_predicha']
        riesgo = prediccion['riesgo']
        fecha = prediccion['fecha_prediccion']
       
        return f"{fecha} | Temp: {temp:.1f}°C | Riesgo: {riesgo}"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def probar_notificador():
    """Función de prueba del notificador"""
    print("🧪 Probando notificador...")
   
    notificador = NotificadorHeladas()
   
    if notificador.predictor is None:
        print("❌ Predictor no disponible")
        return
   
    print("✅ Obteniendo predicción...")
    prediccion = notificador.obtener_prediccion_actual()
   
    if "error" in prediccion:
        print(f"❌ Error: {prediccion['error']}")
        return
   
    print(f"✅ Temperatura predicha: {prediccion['temperatura_predicha']:.1f}°C")
    print(f"✅ Riesgo: {prediccion['riesgo']}")
   
    debe_alertar, nivel = notificador.necesita_enviar_alerta(prediccion)
    print(f"✅ ¿Enviar alerta? {debe_alertar} (Nivel: {nivel})")
   
    if debe_alertar:
        mensaje = notificador.formatear_mensaje_alerta(prediccion)
        print("\n📧 Mensaje de alerta:")
        print(mensaje)
   
    print("\n✅ Prueba completada")


if __name__ == "__main__":
    # Configurar logging para pruebas
    logging.basicConfig(level=logging.INFO)
   
    # Ejecutar prueba
    probar_notificador()