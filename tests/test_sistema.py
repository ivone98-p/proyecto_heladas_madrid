"""
Script de prueba para verificar que todos los componentes funcionen
"""

import sys
from pathlib import Path

print("=" * 60)
print("🧪 PRUEBA DEL SISTEMA DE ALERTAS DE HELADAS")
print("=" * 60)

# ============================================================
# 1. VERIFICAR ESTRUCTURA DE ARCHIVOS
# ============================================================
print("\n📂 1. Verificando estructura de archivos...")

archivos_necesarios = [
    'bot.py',
    'config.py',
    'database.py',
    'predictor.py',
    'requirements.txt',
    '.env'
]

carpetas_necesarias = [
    'Datos/modelos_entrenados',
    'Datos/datos_imputados'
]

todo_ok = True

for archivo in archivos_necesarios:
    if Path(archivo).exists():
        print(f"  ✅ {archivo}")
    else:
        print(f"  ❌ {archivo} - NO ENCONTRADO")
        todo_ok = False

for carpeta in carpetas_necesarias:
    if Path(carpeta).exists():
        print(f"  ✅ {carpeta}/")
    else:
        print(f"  ❌ {carpeta}/ - NO ENCONTRADA")
        todo_ok = False

if not todo_ok:
    print("\n⚠️ Faltan archivos o carpetas necesarios")
    sys.exit(1)

# ============================================================
# 2. VERIFICAR DEPENDENCIAS
# ============================================================
print("\n📦 2. Verificando dependencias instaladas...")

dependencias = [
    'telegram',
    'pandas',
    'numpy',
    'sklearn',
    'joblib',
    'dotenv'
]

for dep in dependencias:
    try:
        __import__(dep)
        print(f"  ✅ {dep}")
    except ImportError:
        print(f"  ❌ {dep} - NO INSTALADO")
        print(f"     Ejecuta: pip install {dep}")
        todo_ok = False

if not todo_ok:
    print("\n⚠️ Instala las dependencias con: pip install -r requirements.txt")
    sys.exit(1)

# ============================================================
# 3. VERIFICAR CONFIGURACIÓN
# ============================================================
print("\n⚙️ 3. Verificando configuración...")

try:
    from config import TELEGRAM_BOT_TOKEN, UMBRALES, HORARIOS_CHEQUEO
    
    if TELEGRAM_BOT_TOKEN and len(TELEGRAM_BOT_TOKEN) > 20:
        print("  ✅ Token de Telegram configurado")
    else:
        print("  ❌ Token de Telegram inválido o vacío")
        print("     Verifica el archivo .env")
        todo_ok = False
    
    print(f"  ✅ Umbrales configurados: {UMBRALES}")
    print(f"  ✅ Horarios de chequeo: {HORARIOS_CHEQUEO}")
    
except Exception as e:
    print(f"  ❌ Error al importar config.py: {e}")
    todo_ok = False

# ============================================================
# 4. PROBAR BASE DE DATOS
# ============================================================
print("\n💾 4. Probando base de datos...")

try:
    from database import DatabaseManager
    
    db = DatabaseManager('test_suscriptores.db')
    print("  ✅ Base de datos inicializada")
    
    # Probar operaciones básicas
    db.agregar_suscriptor(12345, "test_user", "Test User")
    print("  ✅ Agregar suscriptor funciona")
    
    esta_suscrito = db.esta_suscrito(12345)
    if esta_suscrito:
        print("  ✅ Verificar suscripción funciona")
    
    stats = db.obtener_estadisticas()
    print(f"  ✅ Estadísticas: {stats['total_suscriptores']} suscriptores")
    
    # Limpiar BD de prueba
    Path('test_suscriptores.db').unlink(missing_ok=True)
    print("  ✅ Base de datos de prueba eliminada")
    
except Exception as e:
    print(f"  ❌ Error en base de datos: {e}")
    todo_ok = False

# ============================================================
# 5. PROBAR PREDICTOR
# ============================================================
print("\n🔮 5. Probando predictor de heladas...")

try:
    from predictor import PredictorHeladas
    
    predictor = PredictorHeladas()
    print("  ✅ Predictor inicializado")
    
    # Hacer predicción de prueba
    print("  ⏳ Generando predicción de prueba...")
    resultado = predictor.predecir()
    
    if "error" in resultado:
        print(f"  ❌ Error en predicción: {resultado['error']}")
        todo_ok = False
    else:
        print(f"  ✅ Predicción generada exitosamente")
        print(f"     • Temperatura: {resultado['temperatura_predicha']:.1f}°C")
        print(f"     • Probabilidad helada: {resultado['probabilidad_helada']:.1f}%")
        print(f"     • Riesgo: {resultado['riesgo']}")
        print(f"     • Fecha predicción: {resultado['fecha_prediccion']}")
    
except Exception as e:
    print(f"  ❌ Error en predictor: {e}")
    import traceback
    traceback.print_exc()
    todo_ok = False

# ============================================================
# 6. VERIFICAR MODELOS ML
# ============================================================
print("\n🤖 6. Verificando modelos de Machine Learning...")

modelos_dir = Path('Datos/modelos_entrenados')
modelos_necesarios = [
    'modelo_temperatura_ridge.pkl',
    'modelo_helada_ridge.pkl',
    'scaler_temperatura.pkl',
    'scaler_helada.pkl',
    'features_temperatura.pkl',
    'features_helada.pkl'
]

for modelo in modelos_necesarios:
    ruta_modelo = modelos_dir / modelo
    if ruta_modelo.exists():
        print(f"  ✅ {modelo}")
    else:
        print(f"  ❌ {modelo} - NO ENCONTRADO")
        todo_ok = False

# ============================================================
# 7. VERIFICAR DATOS
# ============================================================
print("\n📊 7. Verificando datos históricos...")

csv_path = Path('Datos/datos_imputados/cundinamarca_imputado_v1.csv')
if csv_path.exists():
    print(f"  ✅ {csv_path}")
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"     • Registros: {len(df)}")
        print(f"     • Columnas: {len(df.columns)}")
    except Exception as e:
        print(f"  ⚠️ No se pudo leer el CSV: {e}")
else:
    print(f"  ❌ {csv_path} - NO ENCONTRADO")
    todo_ok = False

# ============================================================
# RESUMEN FINAL
# ============================================================
print("\n" + "=" * 60)
if todo_ok:
    print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("=" * 60)
    print("\n🚀 El sistema está listo para usar")
    print("\nPara iniciar el bot, ejecuta:")
    print("   python bot.py")
    print("\nPara probar en Telegram, busca: @MadridHeladasBot")
else:
    print("❌ ALGUNAS PRUEBAS FALLARON")
    print("=" * 60)
    print("\n⚠️ Revisa los errores anteriores antes de iniciar el bot")

print()