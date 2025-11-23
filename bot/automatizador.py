"""
Automatizador de alertas - Programa y envía alertas automáticas
Se ejecuta en horarios específicos para revisar predicciones
"""

import logging
import asyncio
from datetime import time
from telegram.ext import Application
from telegram import Bot

from database import DatabaseManager
from notificador import NotificadorHeladas
from config import TELEGRAM_BOT_TOKEN, HORARIOS_CHEQUEO, DB_PATH

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs_alertas.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar componentes
db = DatabaseManager(DB_PATH)
notificador = NotificadorHeladas()


async def revisar_y_enviar_alertas(bot: Bot):
    """
    Revisa la predicción y envía alertas si hay riesgo
    Esta función se ejecuta automáticamente según HORARIOS_CHEQUEO
    """
    logger.info("=" * 60)
    logger.info("🔍 REVISIÓN AUTOMÁTICA DE HELADAS")
    logger.info("=" * 60)
    
    try:
        # Obtener predicción actual
        logger.info("🔮 Obteniendo predicción...")
        prediccion = notificador.obtener_prediccion_actual()
        
        if "error" in prediccion:
            logger.error(f"❌ Error en predicción: {prediccion['error']}")
            return
        
        temp = prediccion['temperatura_predicha']
        riesgo = prediccion['riesgo']
        fecha = prediccion['fecha_prediccion']
        
        logger.info(f"✅ Predicción obtenida: Temp={temp:.1f}°C | Riesgo={riesgo} | Fecha={fecha}")
        
        # Determinar si se debe enviar alerta
        debe_alertar, nivel_alerta = notificador.necesita_enviar_alerta(prediccion)
        
        if not debe_alertar:
            logger.info(f"✅ No hay riesgo de helada (Temp: {temp:.1f}°C)")
            logger.info("=" * 60)
            return
        
        logger.warning(f"⚠️ RIESGO DE HELADA DETECTADO: {riesgo} (Temp: {temp:.1f}°C)")
        
        # Obtener suscriptores activos
        suscriptores = db.obtener_suscriptores_activos()
        
        if not suscriptores:
            logger.info("📭 No hay suscriptores activos para notificar")
            logger.info("=" * 60)
            return
        
        logger.info(f"📤 Enviando alertas a {len(suscriptores)} suscriptores...")
        
        # Generar mensaje de alerta
        mensaje_alerta = notificador.formatear_mensaje_alerta(prediccion)
        
        # Enviar alertas a todos los suscriptores
        enviados = 0
        errores = 0
        
        for chat_id in suscriptores:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=mensaje_alerta,
                    parse_mode='Markdown'
                )
                
                # Incrementar contador de alertas del usuario
                db.incrementar_contador_alertas(chat_id)
                enviados += 1
                
                # Pequeña pausa para evitar rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error enviando alerta a {chat_id}: {e}")
                errores += 1
        
        # Registrar en historial
        db.registrar_alerta_enviada(
            nivel_riesgo=nivel_alerta,
            mensaje=mensaje_alerta[:200],  # Solo primeros 200 caracteres
            usuarios_notificados=enviados,
            exito=(errores == 0)
        )
        
        logger.info(f"✅ Alertas enviadas exitosamente: {enviados}")
        if errores > 0:
            logger.warning(f"⚠️ Errores al enviar: {errores}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error en revisión automática: {e}")
        import traceback
        traceback.print_exc()
        logger.info("=" * 60)


async def tarea_programada(context):
    """Callback para tareas programadas"""
    await revisar_y_enviar_alertas(context.bot)


def configurar_automatizacion(application: Application):
    """
    Configura las tareas programadas de alertas
    
    Args:
        application: Aplicación de Telegram
    """
    job_queue = application.job_queue
    
    logger.info("⏰ Configurando tareas programadas...")
    
    for horario in HORARIOS_CHEQUEO:
        try:
            hora, minuto = map(int, horario.split(':'))
            
            job_queue.run_daily(
                tarea_programada,
                time=time(hour=hora, minute=minuto),
                name=f"alerta_{horario}"
            )
            
            logger.info(f"   ✅ Alerta programada: {horario}")
            
        except Exception as e:
            logger.error(f"   ❌ Error programando {horario}: {e}")
    
    logger.info("✅ Tareas programadas configuradas correctamente")


async def ejecutar_revision_manual():
    """
    Ejecuta una revisión manual (para pruebas)
    Útil para probar el sistema sin esperar los horarios programados
    """
    logger.info("🧪 REVISIÓN MANUAL INICIADA")
    
    # Crear bot temporal
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Ejecutar revisión
    await revisar_y_enviar_alertas(bot)
    
    logger.info("✅ Revisión manual completada")


# ============================================================
# FUNCIONES DE PRUEBA
# ============================================================

def probar_automatizador():
    """Prueba el sistema de automatización"""
    print("🧪 Probando automatizador...")
    print()
    
    # Verificar configuración
    print(f"⏰ Horarios configurados: {HORARIOS_CHEQUEO}")
    print()
    
    # Verificar suscriptores
    suscriptores = db.obtener_suscriptores_activos()
    print(f"👥 Suscriptores activos: {len(suscriptores)}")
    print()
    
    # Verificar predictor
    if notificador.predictor is None:
        print("❌ Predictor no disponible")
        return
    
    print("✅ Predictor disponible")
    print()
    
    # Obtener predicción
    print("🔮 Obteniendo predicción de prueba...")
    prediccion = notificador.obtener_prediccion_actual()
    
    if "error" in prediccion:
        print(f"❌ Error: {prediccion['error']}")
        return
    
    print(f"✅ Temperatura: {prediccion['temperatura_predicha']:.1f}°C")
    print(f"✅ Riesgo: {prediccion['riesgo']}")
    print()
    
    # Verificar si se enviaría alerta
    debe_alertar, nivel = notificador.necesita_enviar_alerta(prediccion)
    print(f"📧 ¿Se enviaría alerta? {debe_alertar}")
    if debe_alertar:
        print(f"   Nivel: {nivel}")
    print()
    
    print("✅ Prueba del automatizador completada")
    print()
    print("💡 Para ejecutar una revisión manual real, usa:")
    print("   python automatizador.py manual")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Ejecutar revisión manual
        asyncio.run(ejecutar_revision_manual())
    else:
        # Ejecutar prueba
        probar_automatizador()