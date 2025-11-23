"""
Bot de Telegram para alertas de heladas - Madrid, Cundinamarca
Archivo principal que maneja los comandos del bot
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

from database import DatabaseManager
from notificador import NotificadorHeladas
from config import TELEGRAM_BOT_TOKEN, MENSAJES, DB_PATH

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


# ============================================================
# COMANDOS DEL BOT
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Suscribir usuario"""
    chat_id = update.effective_chat.id
    
    # Verificar si ya está suscrito
    if db.esta_suscrito(chat_id):
        await update.message.reply_text(MENSAJES['ya_suscrito'])
        logger.info(f"Usuario ya suscrito intentó /start: {chat_id}")
        return
    
    # Agregar suscriptor (SIN datos personales para privacidad)
    if db.agregar_suscriptor(chat_id):
        await update.message.reply_text(MENSAJES['bienvenida'])
        await update.message.reply_text(MENSAJES['suscripcion_exitosa'])
        logger.info(f"✅ Nuevo suscriptor: {chat_id}")
    else:
        await update.message.reply_text("❌ Error al suscribirte. Intenta de nuevo.")
        logger.error(f"Error al agregar suscriptor: {chat_id}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stop - Pausar alertas"""
    chat_id = update.effective_chat.id
    
    if not db.esta_suscrito(chat_id):
        await update.message.reply_text(MENSAJES['no_suscrito'])
        return
    
    if db.actualizar_estado_suscripcion(chat_id, False):
        await update.message.reply_text(MENSAJES['pausado'])
        logger.info(f"⏸️ Usuario pausado: {chat_id}")
    else:
        await update.message.reply_text("❌ Error al pausar alertas.")


async def reanudar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /reanudar - Reactivar alertas"""
    chat_id = update.effective_chat.id
    
    info = db.obtener_info_suscriptor(chat_id)
    if not info:
        await update.message.reply_text(MENSAJES['no_suscrito'])
        return
    
    if db.actualizar_estado_suscripcion(chat_id, True):
        await update.message.reply_text(MENSAJES['reanudado'])
        logger.info(f"▶️ Usuario reactivado: {chat_id}")
    else:
        await update.message.reply_text("❌ Error al reanudar alertas.")


async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estado - Ver estado de suscripción"""
    chat_id = update.effective_chat.id
    
    info = db.obtener_info_suscriptor(chat_id)
    
    if not info:
        await update.message.reply_text(MENSAJES['no_suscrito'])
        return
    
    estado_texto = "✅ ACTIVO" if info['activo'] else "⏸️ PAUSADO"
    
    mensaje = f"""
📊 **Tu Estado de Suscripción**

Estado: {estado_texto}
📅 Fecha de registro: {info['fecha_registro'][:10]}
🔔 Alertas recibidas: {info['alertas_recibidas']}
"""
    
    if info['ultima_alerta']:
        mensaje += f"📆 Última alerta: {info['ultima_alerta'][:10]}\n"
    
    await update.message.reply_text(mensaje)
    logger.info(f"Usuario consultó estado: {chat_id}")


async def prediccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /prediccion - Mostrar predicción actual"""
    chat_id = update.effective_chat.id
    
    # Enviar mensaje de espera
    mensaje_espera = await update.message.reply_text("🔮 Generando predicción, espera un momento...")
    
    try:
        # Obtener predicción actual
        resultado = notificador.obtener_prediccion_actual()
        
        if "error" in resultado:
            await mensaje_espera.edit_text(f"❌ Error: {resultado['error']}")
            logger.error(f"Error en predicción: {resultado['error']}")
            return
        
        # Formatear mensaje
        mensaje = notificador.formatear_mensaje_prediccion(resultado)
        
        await mensaje_espera.edit_text(mensaje)
        logger.info(f"Usuario consultó predicción: {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ Error en comando /prediccion: {e}")
        await mensaje_espera.edit_text("❌ Error al generar predicción. Intenta de nuevo.")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /info - Información del sistema"""
    await update.message.reply_text(MENSAJES['info'])
    logger.info(f"Usuario consultó info: {update.effective_chat.id}")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda - Mostrar ayuda"""
    await update.message.reply_text(MENSAJES['ayuda'])
    logger.info(f"Usuario consultó ayuda: {update.effective_chat.id}")


async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estadisticas - Estadísticas del sistema (admin)"""
    chat_id = update.effective_chat.id
    
    # Opcional: Restringir a administradores
    # ADMINS = [12345678]  # Reemplaza con tu chat_id
    # if chat_id not in ADMINS:
    #     return
    
    stats = db.obtener_estadisticas()
    
    mensaje = f"""
📊 **Estadísticas del Sistema**

👥 **Suscriptores:**
• Total: {stats['total_suscriptores']}
• Activos: {stats['suscriptores_activos']}

📤 **Alertas:**
• Total enviadas: {stats['total_alertas_enviadas']}
"""
    
    if stats['ultima_alerta']:
        ua = stats['ultima_alerta']
        mensaje += f"""
📆 **Última alerta:**
• Fecha: {ua['fecha_envio'][:16]}
• Riesgo: {ua['nivel_riesgo']}
• Usuarios notificados: {ua['usuarios_notificados']}
"""
    
    await update.message.reply_text(mensaje)
    logger.info(f"Admin consultó estadísticas: {chat_id}")


# ============================================================
# INICIALIZACIÓN DEL BOT
# ============================================================

def iniciar_bot():
    """Inicializa y ejecuta el bot de Telegram"""
    
    logger.info("=" * 60)
    logger.info("🤖 Iniciando Bot de Alertas de Heladas")
    logger.info("📍 Madrid, Cundinamarca")
    logger.info("=" * 60)
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("reanudar", reanudar))
    application.add_handler(CommandHandler("estado", estado))
    application.add_handler(CommandHandler("prediccion", prediccion))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("estadisticas", estadisticas))
    
    logger.info("✅ Comandos registrados correctamente")
    logger.info("🚀 Bot listo para recibir mensajes")
    logger.info("=" * 60)
    
    # Iniciar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        iniciar_bot()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()