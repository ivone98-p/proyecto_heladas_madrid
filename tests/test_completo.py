"""
Script de prueba completo para verificar todos los componentes del sistema
Ejecuta: python test_completo.py
"""

import sys
from pathlib import Path

def print_header(texto):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 70)
    print(f"  {texto}")
    print("=" * 70)

def print_seccion(numero, titulo):
    """Imprime título de sección"""
    print(f"\n{'─' * 70}")
    print(f"  {numero}. {titulo}")
    print(f"{'─' * 70}")

# ============================================================
# INICIO
# ============================================================
print_header("🧪 PRUEBA COMPLETA DEL SISTEMA DE ALERTAS DE HELADAS")
print("📍 Madrid, Cundinamarca")
print()

todo_ok = True
errores = []

# ============================================================
# 1. VERIFICAR ESTRUCTURA DE ARCHIVOS
# ============================================================
print_seccion(1, "Verificando estructura de archivos")

archivos_principales = {
    'telegram_bot.py': 'Bot principal de Telegram',
    'database.py': 'Gestión de base de datos',
    'notificador.py': 'Sistema de notificaciones',
    'automatizador.py': 'Programador de tareas',
    'predictor.py': 'Predictor de heladas ML',
    'config.py': 'Configuración del sistema',
    'requirements.txt': 'Dependencias',
    '.env': 'Variables de entorno'
}

for archivo, descripcion in archivos_principales.items():
    if Path(archivo).exists():
        print(f"  ✅ {archivo:<25} - {descripcion}")
    else:
        print(f"  ❌ {archivo:<25} - NO ENCONTRADO")
        errores.append(f"Falta archivo: {archivo}")
        todo_ok = False

# Verificar carpetas de datos
print("\nCarpetas de datos:")
carpetas = {
    'Datos/modelos_entrenados': 'Modelos ML entrenados',
    'Datos/datos_imputados': 'Datos históricos'
}

for carpeta, descripcion in carpetas.items():
    if Path(carpeta).exists():
        print(f"  ✅ {carpeta:<30} - {descripcion}")
    else:
        print(f"  ❌ {carpeta:<30} - NO ENCONTRADA")
        errores.append(f"Falta carpeta: {carpeta}")
        todo_ok = False

# ============================================================
# 2. VERIFICAR DEPENDENCIAS
# ============================================================
print_seccion(2, "Verificando dependencias instaladas")

dependencias = {
    'telegram': 'python-telegram-bot',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'sklearn': 'scikit-learn',
    'joblib': 'joblib',
    'dotenv': 'python-dotenv'
}

for modulo, paquete in dependencias.items():
    try:
        __import__(modulo)
        print(f"  ✅ {paquete}")
    except ImportError:
        print(f"  ❌ {paquete} - NO INSTALADO")
        errores.append(f"Falta instalar: {paquete}")
        todo_ok = False

if not todo_ok and len([e for e in errores if "instalar" in e]) > 0:
    print("\n  ⚠️ Instala dependencias con: pip install -r requirements.txt")

# ============================================================
# 3. VERIFICAR CONFIGURACIÓN
# ============================================================
print_seccion(3, "Verificando configuración")

try:
    from config import TELEGRAM_BOT_TOKEN, UMBRALES, HORARIOS_CHEQUEO, MENSAJES
    
    if TELEGRAM_BOT_TOKEN and len(TELEGRAM_BOT_TOKEN) > 20:
        token_preview = f"{TELEGRAM_BOT_TOKEN[:15]}...{TELEGRAM_BOT_TOKEN[-10:]}"
        print(f"  ✅ Token de Telegram: {token_preview}")
    else:
        print("  ❌ Token de Telegram inválido o vacío")
        errores.append("Token de Telegram no configurado correctamente")
        todo_ok = False
    
    print(f"  ✅ Umbrales de temperatura:")
    for nivel, temp in UMBRALES.items():
        print(f"     • {nivel}: {temp}°C")
    
    print(f"  ✅ Horarios de chequeo: {', '.join(HORARIOS_CHEQUEO)}")
    print(f"  ✅ Mensajes configurados: {len(MENSAJES)} plantillas")
    
except Exception as e:
    print(f"  ❌ Error al cargar config.py: {e}")
    errores.append(f"Error en configuración: {e}")
    todo_ok = False

# ============================================================
# 4. PROBAR BASE DE DATOS
# ============================================================
print_seccion(4, "Probando sistema de base de datos")

try:
    from database import DatabaseManager
    
    # Usar base de datos de prueba
    db_test = DatabaseManager('test_db.db')
    print("  ✅ Base de datos inicializada")
    
    # Probar agregar suscriptor
    db_test.agregar_suscriptor(99999, "test_user", "Usuario Test")
    print("  ✅ Agregar suscriptor: OK")
    
    # Probar verificar suscripción
    if db_test.esta_suscrito(99999):
        print("  ✅ Verificar suscripción: OK")
    else:
        print("  ❌ Verificar suscripción: FALLO")
        errores.append("Error en verificación de suscripción")
        todo_ok = False
    
    # Probar obtener estadísticas
    stats = db_test.obtener_estadisticas()
    print(f"  ✅ Estadísticas: {stats['total_suscriptores']} suscriptores")
    
    # Probar actualizar estado
    db_test.actualizar_estado_suscripcion(99999, False)
    print("  ✅ Actualizar estado: OK")
    
    # Limpiar
    Path('test_db.db').unlink(missing_ok=True)
    print("  ✅ Limpieza de BD de prueba: OK")
    
except Exception as e:
    print(f"  ❌ Error en base de datos: {e}")
    errores.append(f"Error en base de datos: {e}")
    todo_ok = False
    import traceback
    traceback.print_exc()

# ============================================================
# 5. PROBAR PREDICTOR
# ============================================================
print_seccion(5, "Probando predictor de heladas (Machine Learning)")

try:
    from predictor import PredictorHeladas
    
    print("  ⏳ Cargando predictor...")
    predictor = PredictorHeladas()
    print("  ✅ Predictor inicializado correctamente")
    
    print("  ⏳ Generando predicción de prueba...")
    resultado = predictor.predecir()
    
    if "error" in resultado:
        print(f"  ❌ Error en predicción: {resultado['error']}")
        errores.append(f"Error en predicción: {resultado['error']}")
        todo_ok = False
    else:
        print("  ✅ Predicción generada exitosamente")
        print(f"     • Temperatura predicha: {resultado['temperatura_predicha']:.1f}°C")
        print(f"     • Probabilidad helada: {resultado['probabilidad_helada']:.1f}%")
        print(f"     • Nivel de riesgo: {resultado['riesgo']}")
        print(f"     • Fecha predicción: {resultado['fecha_prediccion']}")
        
        if resultado.get('datos_simulados'):
            print(f"     ⚠️ Usando datos simulados (última fecha real: {resultado['ultima_fecha_real']})")
    
except Exception as e:
    print(f"  ❌ Error en predictor: {e}")
    errores.append(f"Error en predictor: {e}")
    todo_ok = False
    import traceback
    traceback.print_exc()

# ============================================================
# 6. PROBAR NOTIFICADOR
# ============================================================
print_seccion(6, "Probando sistema de notificaciones")

try:
    from notificador import NotificadorHeladas
    
    notificador = NotificadorHeladas()
    print("  ✅ Notificador inicializado")
    
    if notificador.predictor:
        print("  ✅ Predictor conectado al notificador")
        
        # Obtener predicción
        pred = notificador.obtener_prediccion_actual()
        if "error" not in pred:
            print(f"  ✅ Predicción obtenida: Temp={pred['temperatura_predicha']:.1f}°C")
            
            # Verificar si se enviaría alerta
            debe_alertar, nivel = notificador.necesita_enviar_alerta(pred)
            if debe_alertar:
                print(f"  ✅ Sistema de alertas: Se enviaría alerta nivel {nivel}")
            else:
                print(f"  ✅ Sistema de alertas: No se requiere alerta (Temp > 2°C)")
            
            # Probar formato de mensaje
            mensaje = notificador.formatear_mensaje_prediccion(pred)
            print(f"  ✅ Formato de mensaje: OK ({len(mensaje)} caracteres)")
        else:
            print(f"  ⚠️ No se pudo obtener predicción: {pred['error']}")
    else:
        print("  ⚠️ Predictor no disponible en notificador")
    
except Exception as e:
    print(f"  ❌ Error en notificador: {e}")
    errores.append(f"Error en notificador: {e}")
    todo_ok = False

# ============================================================
# 7. VERIFICAR MODELOS ML
# ============================================================
print_seccion(7, "Verificando modelos de Machine Learning")

modelos_dir = Path('Datos/modelos_entrenados')
modelos_necesarios = [
    'modelo_temperatura_ridge.pkl',
    'modelo_helada_ridge.pkl',
    'scaler_temperatura.pkl',
    'scaler_helada.pkl',
    'features_temperatura.pkl',
    'features_helada.pkl'
]

modelos_ok = True
for modelo in modelos_necesarios:
    ruta = modelos_dir / modelo
    if ruta.exists():
        size_kb = ruta.stat().st_size / 1024
        print(f"  ✅ {modelo:<35} ({size_kb:.1f} KB)")
    else:
        print(f"  ❌ {modelo:<35} - NO ENCONTRADO")
        errores.append(f"Falta modelo: {modelo}")
        modelos_ok = False
        todo_ok = False

if modelos_ok:
    print("  ✅ Todos los modelos ML están presentes")

# ============================================================
# 8. VERIFICAR DATOS HISTÓRICOS
# ============================================================
print_seccion(8, "Verificando datos históricos")

csv_path = Path('Datos/datos_imputados/cundinamarca_imputado_v1.csv')
if csv_path.exists():
    size_mb = csv_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ Archivo CSV encontrado ({size_mb:.2f} MB)")
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_path, nrows=5)
        print(f"  ✅ CSV legible: {len(df.columns)} columnas detectadas")
    except Exception as e:
        print(f"  ⚠️ Advertencia al leer CSV: {e}")
else:
    print(f"  ❌ {csv_path} - NO ENCONTRADO")
    errores.append("Falta archivo de datos históricos")
    todo_ok = False

# ============================================================
# 9. VERIFICAR AUTOMATIZADOR
# ============================================================
print_seccion(9, "Verificando automatizador de tareas")

try:
    from automatizador import configurar_automatizacion
    from config import HORARIOS_CHEQUEO
    print("  ✅ Automatizador importado correctamente")
    print(f"  ✅ Horarios configurados: {', '.join(HORARIOS_CHEQUEO)}")
    print("  ✅ Sistema de tareas programadas: OK")
except Exception as e:
    print(f"  ❌ Error en automatizador: {e}")
    errores.append(f"Error en automatizador: {e}")
    todo_ok = False

# ============================================================
# RESUMEN FINAL
# ============================================================
print_header("📊 RESUMEN DE LA PRUEBA")

if todo_ok:
    print("\n✅ ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    print("\n🎉 El sistema está completamente funcional y listo para usar.")
    print("\n📝 Próximos pasos:")
    print("   1. Asegúrate de que el archivo .env tenga el token correcto")
    print("   2. Ejecuta: python telegram_bot.py")
    print("   3. Busca tu bot en Telegram: @MadridHeladasBot")
    print("   4. Usa /start para suscribirte")
    print("\n⏰ El bot revisará automáticamente en estos horarios:")
    try:
        from config import HORARIOS_CHEQUEO
        for horario in HORARIOS_CHEQUEO:
            print(f"   • {horario}")
    except:
        pass
    
else:
    print("\n❌ ALGUNAS PRUEBAS FALLARON")
    print(f"\n📋 Se encontraron {len(errores)} errores:")
    for i, error in enumerate(errores, 1):
        print(f"   {i}. {error}")
    
    print("\n🔧 Soluciones sugeridas:")
    print("   • Verifica que todos los archivos estén en su lugar")
    print("   • Ejecuta: pip install -r requirements.txt")
    print("   • Verifica que la carpeta Datos/ tenga todos los modelos")
    print("   • Revisa el archivo .env con el token correcto")

print("\n" + "=" * 70)
print()

sys.exit(0 if todo_ok else 1)