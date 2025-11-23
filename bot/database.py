# database.py
"""
Sistema de gestión de base de datos para suscriptores del bot de Telegram
Usa SQLite para almacenar información de usuarios y sus suscripciones
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestor de base de datos para suscriptores"""
    
    def __init__(self, db_path: str = 'suscriptores.db'):
        """
        Inicializar conexión a la base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.crear_tablas()
    
    def conectar(self) -> sqlite3.Connection:
        """Crear conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
        return conn
    
    def crear_tablas(self):
        """Crear tablas necesarias si no existen"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Tabla de suscriptores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suscriptores (
                chat_id INTEGER PRIMARY KEY,
                username TEXT,
                nombre TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT 1,
                alertas_recibidas INTEGER DEFAULT 0,
                ultima_alerta TIMESTAMP
            )
        ''')
        
        # Tabla de historial de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nivel_riesgo TEXT,
                mensaje TEXT,
                usuarios_notificados INTEGER,
                exito BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    
    def agregar_suscriptor(self, chat_id: int, username: str = None, nombre: str = None) -> bool:
        """
        Agregar o actualizar un suscriptor
        
        Args:
            chat_id: ID del chat de Telegram
            username: Nombre de usuario de Telegram
            nombre: Nombre del usuario
            
        Returns:
            True si se agregó/actualizó correctamente
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO suscriptores (chat_id, username, nombre, activo)
                VALUES (?, ?, ?, 1)
            ''', (chat_id, username, nombre))
            
            conn.commit()
            conn.close()
            logger.info(f"Suscriptor {chat_id} agregado/actualizado")
            return True
        except Exception as e:
            logger.error(f"Error al agregar suscriptor: {e}")
            return False
    
    def esta_suscrito(self, chat_id: int) -> bool:
        """
        Verificar si un usuario está suscrito y activo
        
        Args:
            chat_id: ID del chat de Telegram
            
        Returns:
            True si está suscrito y activo
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT activo FROM suscriptores WHERE chat_id = ?
        ''', (chat_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        return resultado is not None and resultado['activo'] == 1
    
    def actualizar_estado_suscripcion(self, chat_id: int, activo: bool) -> bool:
        """
        Actualizar estado de suscripción de un usuario
        
        Args:
            chat_id: ID del chat de Telegram
            activo: True para activar, False para desactivar
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE suscriptores SET activo = ? WHERE chat_id = ?
            ''', (1 if activo else 0, chat_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Estado de suscripción actualizado para {chat_id}: {activo}")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar estado de suscripción: {e}")
            return False
    
    def obtener_suscriptores_activos(self) -> List[int]:
        """
        Obtener lista de chat_ids de suscriptores activos
        
        Returns:
            Lista de IDs de chat activos
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chat_id FROM suscriptores WHERE activo = 1
        ''')
        
        resultados = cursor.fetchall()
        conn.close()
        
        return [row['chat_id'] for row in resultados]
    
    def obtener_info_suscriptor(self, chat_id: int) -> Optional[Dict]:
        """
        Obtener información completa de un suscriptor
        
        Args:
            chat_id: ID del chat de Telegram
            
        Returns:
            Diccionario con información del suscriptor o None
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM suscriptores WHERE chat_id = ?
        ''', (chat_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return dict(resultado)
        return None
    
    def incrementar_contador_alertas(self, chat_id: int):
        """
        Incrementar contador de alertas recibidas por un usuario
        
        Args:
            chat_id: ID del chat de Telegram
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE suscriptores 
                SET alertas_recibidas = alertas_recibidas + 1,
                    ultima_alerta = CURRENT_TIMESTAMP
                WHERE chat_id = ?
            ''', (chat_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error al incrementar contador de alertas: {e}")
    
    def registrar_alerta_enviada(self, nivel_riesgo: str, mensaje: str, 
                                  usuarios_notificados: int, exito: bool = True):
        """
        Registrar una alerta enviada en el historial
        
        Args:
            nivel_riesgo: Nivel de riesgo de la alerta (alto, medio, bajo)
            mensaje: Contenido del mensaje enviado
            usuarios_notificados: Cantidad de usuarios notificados
            exito: Si el envío fue exitoso
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO historial_alertas 
                (nivel_riesgo, mensaje, usuarios_notificados, exito)
                VALUES (?, ?, ?, ?)
            ''', (nivel_riesgo, mensaje, usuarios_notificados, 1 if exito else 0))
            
            conn.commit()
            conn.close()
            logger.info(f"Alerta registrada en historial: {nivel_riesgo}")
        except Exception as e:
            logger.error(f"Error al registrar alerta en historial: {e}")
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtener estadísticas generales del sistema
        
        Returns:
            Diccionario con estadísticas
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Total de suscriptores
        cursor.execute('SELECT COUNT(*) as total FROM suscriptores')
        total_suscriptores = cursor.fetchone()['total']
        
        # Suscriptores activos
        cursor.execute('SELECT COUNT(*) as activos FROM suscriptores WHERE activo = 1')
        suscriptores_activos = cursor.fetchone()['activos']
        
        # Total de alertas enviadas
        cursor.execute('SELECT COUNT(*) as total_alertas FROM historial_alertas')
        total_alertas = cursor.fetchone()['total_alertas']
        
        # Última alerta enviada
        cursor.execute('''
            SELECT fecha_envio, nivel_riesgo, usuarios_notificados 
            FROM historial_alertas 
            ORDER BY fecha_envio DESC 
            LIMIT 1
        ''')
        ultima_alerta = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_suscriptores': total_suscriptores,
            'suscriptores_activos': suscriptores_activos,
            'total_alertas_enviadas': total_alertas,
            'ultima_alerta': dict(ultima_alerta) if ultima_alerta else None
        }
    
    def obtener_historial_alertas(self, limite: int = 10) -> List[Dict]:
        """
        Obtener historial de alertas recientes
        
        Args:
            limite: Cantidad máxima de registros a retornar
            
        Returns:
            Lista de diccionarios con información de alertas
        """
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM historial_alertas 
            ORDER BY fecha_envio DESC 
            LIMIT ?
        ''', (limite,))
        
        resultados = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in resultados]
    
    def eliminar_suscriptor(self, chat_id: int) -> bool:
        """
        Eliminar completamente un suscriptor de la base de datos
        
        Args:
            chat_id: ID del chat de Telegram
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM suscriptores WHERE chat_id = ?', (chat_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"Suscriptor {chat_id} eliminado de la base de datos")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar suscriptor: {e}")
            return False
    
    def limpiar_suscriptores_inactivos(self, dias: int = 90) -> int:
        """
        Eliminar suscriptores inactivos por más de X días
        
        Args:
            dias: Días de inactividad para considerar eliminación
            
        Returns:
            Cantidad de suscriptores eliminados
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM suscriptores 
                WHERE activo = 0 
                AND datetime(ultima_alerta) < datetime('now', '-' || ? || ' days')
            ''', (dias,))
            
            eliminados = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Eliminados {eliminados} suscriptores inactivos")
            return eliminados
        except Exception as e:
            logger.error(f"Error al limpiar suscriptores inactivos: {e}")
            return 0


# Función de prueba
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear instancia de la base de datos
    db = DatabaseManager()
    
    # Pruebas
    print("=== Pruebas de Base de Datos ===\n")
    
    # Agregar suscriptor de prueba
    db.agregar_suscriptor(12345, "usuario_prueba", "Usuario Test")
    print("✓ Suscriptor agregado")
    
    # Verificar suscripción
    esta_suscrito = db.esta_suscrito(12345)
    print(f"✓ ¿Está suscrito? {esta_suscrito}")
    
    # Obtener información
    info = db.obtener_info_suscriptor(12345)
    print(f"✓ Información del suscriptor: {info}")
    
    # Obtener estadísticas
    stats = db.obtener_estadisticas()
    print(f"\n✓ Estadísticas del sistema:")
    print(f"  - Total suscriptores: {stats['total_suscriptores']}")
    print(f"  - Suscriptores activos: {stats['suscriptores_activos']}")
    print(f"  - Total alertas enviadas: {stats['total_alertas_enviadas']}")
    
    print("\n✅ Todas las pruebas completadas exitosamente")