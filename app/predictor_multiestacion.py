#============================================================
#  PREDICTOR MULTI-ESTACIÓN (7 modelos independientes)
#  Usa modelos entrenados en modelos_multiestacion/
# ============================================================

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime, timedelta

class PredictorHeladasMulti:
    """
    Predictor que carga 7 modelos independientes (uno por estación)
    Cada modelo usa la arquitectura validada de Flores Chibcha
    """
    
    def __init__(self, data_path=None):
        """Inicializa el predictor multi-estación"""
        if data_path is None:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            self.base_dir = project_root / 'Datos'
        else:
            self.base_dir = Path(data_path)
        
        # Usar carpeta de modelos multi-estación
        self.modelos_dir = self.base_dir / 'modelos_multiestacion'
        self.datos_dir = self.base_dir / 'datos_imputados'
        self.metadata_path = self.base_dir / 'datos_prediccion' / 'metadata_estaciones.csv'
        
        print(f"📂 Directorio base: {self.base_dir.absolute()}")
        print(f"📂 Modelos: {self.modelos_dir.absolute()}")
        
        # Verificar directorios
        if not self.modelos_dir.exists():
            raise FileNotFoundError(f"❌ No se encuentra: {self.modelos_dir}")
        if not self.datos_dir.exists():
            raise FileNotFoundError(f"❌ No se encuentra: {self.datos_dir}")
        
        # Cargar metadata y datos
        self._cargar_metadata_modelos()
        self._cargar_datos()
        self._cargar_metadata_coordenadas()
        
        self._ultima_prediccion = None
    
    def _cargar_metadata_modelos(self):
        """Carga metadata de los modelos entrenados"""
        try:
            metadata = joblib.load(self.modelos_dir / 'metadata_estaciones.pkl')
            self.estaciones_nombres = metadata['estaciones']
            self.columnas_prec = metadata['columnas_prec']
            self.columnas_tmax = metadata['columnas_tmax']
            
            print(f"✅ Metadata cargada: {len(self.estaciones_nombres)} estaciones")
        except Exception as e:
            raise Exception(f"❌ Error cargando metadata: {e}")
    
    def _cargar_datos(self):
        """Carga datos históricos"""
        try:
            csv_path = self.datos_dir / 'cundinamarca_imputado_v1.csv'
            
            if not csv_path.exists():
                raise FileNotFoundError(f"❌ No se encuentra: {csv_path}")
            
            self.df = pd.read_csv(csv_path)
            self.df['Fecha'] = pd.to_datetime(self.df['Fecha'])
            
            print(f"✅ Datos cargados: {len(self.df)} registros")
        except Exception as e:
            raise Exception(f"❌ Error cargando datos: {e}")
    
    def _cargar_metadata_coordenadas(self):
        """Carga metadata de coordenadas de estaciones"""
        try:
            if not self.metadata_path.exists():
                print(f"⚠️ No se encontró metadata de coordenadas")
                self.coordenadas = {}
                return
            
            metadata_coords = pd.read_csv(self.metadata_path)
            
            self.coordenadas = {}
            for _, row in metadata_coords.iterrows():
                codigo = str(row['CodigoEstacion'])
                self.coordenadas[codigo] = {
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'alt': float(row['alt']),
                    'nombre': str(row['nombre'])
                }
            
            print(f"✅ Coordenadas cargadas: {len(self.coordenadas)} estaciones")
        except Exception as e:
            print(f"⚠️ Error cargando coordenadas: {e}")
            self.coordenadas = {}
    
    def _extraer_codigo_estacion(self, nombre_columna):
        """Extrae código de estación desde nombre de columna"""
        partes = nombre_columna.split('_')
        if len(partes) >= 2:
            return partes[1]
        return None
    
    def _simular_datos_faltantes(self, fecha_hasta):
        """Simula datos faltantes hasta fecha_hasta"""
        df_extendido = self.df.copy()
        ultima_fecha = df_extendido['Fecha'].max()
        
        if fecha_hasta <= ultima_fecha:
            return df_extendido
        
        print(f"🔧 Simulando datos desde {ultima_fecha.date()} hasta {fecha_hasta.date()}...")
        
        df_extendido['Mes'] = df_extendido['Fecha'].dt.month
        df_extendido['Dia'] = df_extendido['Fecha'].dt.day
        
        promedios = {}
        for col in self.estaciones_nombres + self.columnas_prec + self.columnas_tmax:
            promedios[col] = df_extendido.groupby(['Mes', 'Dia'])[col].mean()
        
        fechas_faltantes = pd.date_range(
            start=ultima_fecha + pd.Timedelta(days=1),
            end=fecha_hasta,
            freq='D'
        )
        
        nuevas_filas = []
        for fecha in fechas_faltantes:
            mes = fecha.month
            dia = fecha.day
            
            nueva_fila = {'Fecha': fecha}
            
            for col in self.estaciones_nombres + self.columnas_prec + self.columnas_tmax:
                if (mes, dia) in promedios[col].index:
                    nueva_fila[col] = promedios[col].loc[(mes, dia)]
                else:
                    nueva_fila[col] = df_extendido[df_extendido['Mes'] == mes][col].mean()
            
            nuevas_filas.append(nueva_fila)
        
        df_nuevas_filas = pd.DataFrame(nuevas_filas)
        df_extendido = pd.concat([df_extendido, df_nuevas_filas], ignore_index=True)
        df_extendido = df_extendido.sort_values('Fecha').reset_index(drop=True)
        df_extendido = df_extendido.drop(columns=['Mes', 'Dia'], errors='ignore')
        
        print(f"✅ {len(nuevas_filas)} días simulados")
        
        return df_extendido
    
    def _crear_features_completos(self, df_input, target_col, incluir_prec_tmax=False, 
                                 cols_prec=None, cols_tmax=None):
        """Crea features usando la arquitectura validada"""
        df_out = df_input.copy()
        
        # Temporales
        df_out['Mes'] = df_out['Fecha'].dt.month
        df_out['DíaAño'] = df_out['Fecha'].dt.dayofyear
        df_out['Trimestre'] = df_out['Fecha'].dt.quarter
        df_out['DiaSemana'] = df_out['Fecha'].dt.dayofweek
        df_out['Semana'] = df_out['Fecha'].dt.isocalendar().week
        
        # Cíclicos
        df_out['Mes_sin'] = np.sin(2 * np.pi * df_out['Mes'] / 12)
        df_out['Mes_cos'] = np.cos(2 * np.pi * df_out['Mes'] / 12)
        df_out['DíaAño_sin'] = np.sin(2 * np.pi * df_out['DíaAño'] / 365)
        df_out['DíaAño_cos'] = np.cos(2 * np.pi * df_out['DíaAño'] / 365)
        df_out['Semana_sin'] = np.sin(2 * np.pi * df_out['Semana'] / 52)
        df_out['Semana_cos'] = np.cos(2 * np.pi * df_out['Semana'] / 52)
        df_out['DiaSemana_sin'] = np.sin(2 * np.pi * df_out['DiaSemana'] / 7)
        df_out['DiaSemana_cos'] = np.cos(2 * np.pi * df_out['DiaSemana'] / 7)
        
        # Rezagos
        for lag in [1, 2, 3, 7, 14, 21, 30]:
            df_out[f'TMIN_lag_{lag}'] = df_out[target_col].shift(lag)
        
        # Medias móviles
        for window in [3, 7, 14, 30]:
            df_out[f'TMIN_ma_{window}'] = df_out[target_col].shift(1).rolling(window=window).mean()
            df_out[f'TMIN_std_{window}'] = df_out[target_col].shift(1).rolling(window=window).std()
            df_out[f'TMIN_min_{window}'] = df_out[target_col].shift(1).rolling(window=window).min()
            df_out[f'TMIN_max_{window}'] = df_out[target_col].shift(1).rolling(window=window).max()
        
        # Diferencias
        df_out['TMIN_diff_1'] = df_out[target_col].diff(1)
        df_out['TMIN_diff_7'] = df_out[target_col].diff(7)
        df_out['TMIN_diff_30'] = df_out[target_col].diff(30)
        
        # Tendencias
        def calcular_tendencia(serie):
            if len(serie) < 5 or serie.isna().all():
                return 0
            try:
                x = np.arange(len(serie))
                coef = np.polyfit(x, serie.values, 1)[0]
                return coef
            except:
                return 0
        
        for window in [7, 14, 30]:
            df_out[f'TMIN_tendencia_{window}'] = df_out[target_col].shift(1).rolling(window=window).apply(
                calcular_tendencia, raw=False
            )
        
        # Rangos
        for window in [7, 14, 30]:
            df_out[f'TMIN_rango_{window}'] = df_out[f'TMIN_max_{window}'] - df_out[f'TMIN_min_{window}']
        
        # Percentiles
        for window in [7, 14, 30]:
            df_out[f'TMIN_q25_{window}'] = df_out[target_col].shift(1).rolling(window=window).quantile(0.25)
            df_out[f'TMIN_q75_{window}'] = df_out[target_col].shift(1).rolling(window=window).quantile(0.75)
        
        # Aceleración
        df_out['TMIN_aceleracion'] = df_out['TMIN_diff_1'].diff(1)
        
        # PREC y TMax
        if incluir_prec_tmax and cols_prec is not None and cols_tmax is not None:
            if len(cols_prec) > 0:
                for col in cols_prec:
                    df_out[f'{col}_lag1'] = df_out[col].shift(1)
                
                cols_prec_lag = [f'{col}_lag1' for col in cols_prec]
                df_out['PREC_promedio'] = df_out[cols_prec_lag].mean(axis=1)
                df_out['PREC_max'] = df_out[cols_prec_lag].max(axis=1)
                df_out['PREC_std'] = df_out[cols_prec_lag].std(axis=1)
                
                for lag in [2, 3, 7]:
                    df_out[f'PREC_promedio_lag{lag}'] = df_out['PREC_promedio'].shift(lag)
                
                for window in [3, 7, 14]:
                    df_out[f'PREC_suma_{window}'] = df_out['PREC_promedio'].shift(1).rolling(window=window).sum()
            
            if len(cols_tmax) > 0:
                for col in cols_tmax:
                    df_out[f'{col}_lag1'] = df_out[col].shift(1)
                
                cols_tmax_lag = [f'{col}_lag1' for col in cols_tmax]
                df_out['TMAX_promedio'] = df_out[cols_tmax_lag].mean(axis=1)
                df_out['TMAX_std'] = df_out[cols_tmax_lag].std(axis=1)
                df_out['Rango_termico_lag1'] = df_out['TMAX_promedio'] - df_out['TMIN_lag_1']
                
                for window in [3, 7, 14]:
                    df_out[f'TMAX_ma_{window}'] = df_out['TMAX_promedio'].shift(1).rolling(window=window).mean()
                
                df_out['TMAX_diff_1'] = df_out['TMAX_promedio'].diff(1)
            
            if 'TMAX_promedio' in df_out.columns and 'TMIN_lag_1' in df_out.columns:
                df_out['TMax_TMin_ratio'] = df_out['TMAX_promedio'] / (df_out['TMIN_lag_1'].abs() + 1)
            
            if 'PREC_promedio' in df_out.columns:
                df_out['PREC_binaria'] = (df_out['PREC_promedio'] > 0).astype(int)
            
            for col in cols_prec + cols_tmax:
                if col in df_out.columns:
                    df_out.drop(col, axis=1, inplace=True)
        
        df_out = df_out.dropna().reset_index(drop=True)
        return df_out
    
    def predecir(self, fecha_consulta=None, forzar_recalculo=False):
        """
        Predice temperatura y heladas para TODAS las estaciones
        
        Returns:
            dict con predicciones por estación + interpolación
        """
        if self._ultima_prediccion and not forzar_recalculo:
            print("📌 Usando predicción cacheada")
            return self._ultima_prediccion
        
        try:
            if fecha_consulta is None:
                fecha_consulta = pd.Timestamp.now().normalize()
            else:
                fecha_consulta = pd.to_datetime(fecha_consulta).normalize()
            
            df_completo = self._simular_datos_faltantes(fecha_consulta)
            df_hasta_hoy = df_completo[df_completo['Fecha'] <= fecha_consulta].copy()
            
            if len(df_hasta_hoy) < 50:
                return {"error": "Datos insuficientes"}
            
            print(f"🔮 Predicción multi-estación ({len(self.estaciones_nombres)} modelos)")
            print(f"📅 Predicción para: {(fecha_consulta + pd.Timedelta(days=1)).date()}")
            
            predicciones_estaciones = []
            
            # PREDECIR PARA CADA ESTACIÓN
            for estacion in self.estaciones_nombres:
                codigo = self._extraer_codigo_estacion(estacion)
                
                try:
                    # CARGAR MODELOS
                    modelo_temp = joblib.load(self.modelos_dir / f'modelo_temp_{codigo}.pkl')
                    scaler_temp = joblib.load(self.modelos_dir / f'scaler_temp_{codigo}.pkl')
                    features_temp = joblib.load(self.modelos_dir / f'features_temp_{codigo}.pkl')
                    
                    modelo_helada = joblib.load(self.modelos_dir / f'modelo_helada_{codigo}.pkl')
                    scaler_helada = joblib.load(self.modelos_dir / f'scaler_helada_{codigo}.pkl')
                    features_helada = joblib.load(self.modelos_dir / f'features_helada_{codigo}.pkl')
                    
                    # PREDECIR TEMPERATURA
                    df_temp = df_hasta_hoy[['Fecha', estacion]].copy().dropna(subset=[estacion])
                    df_temp = self._crear_features_completos(df_temp, estacion, incluir_prec_tmax=False)
                    
                    if len(df_temp) == 0:
                        continue
                    
                    ultima_fila_temp = df_temp.iloc[[-1]]
                    X_temp = ultima_fila_temp[features_temp]
                    X_temp_s = scaler_temp.transform(X_temp)
                    temp_pred = float(modelo_temp.predict(X_temp_s)[0])
                    
                    # PREDECIR HELADA
                    df_helada = df_hasta_hoy[['Fecha', estacion] + self.columnas_prec + self.columnas_tmax].copy()
                    df_helada = df_helada.dropna(subset=[estacion])
                    
                    for col in self.columnas_prec + self.columnas_tmax:
                        if df_helada[col].isna().any():
                            df_helada[col].fillna(df_helada[col].mean(), inplace=True)
                    
                    df_helada = self._crear_features_completos(
                        df_helada, estacion, incluir_prec_tmax=True,
                        cols_prec=self.columnas_prec, cols_tmax=self.columnas_tmax
                    )
                    
                    if len(df_helada) == 0:
                        continue
                    
                    ultima_fila_helada = df_helada.iloc[[-1]]
                    X_helada = ultima_fila_helada[features_helada]
                    X_helada_s = scaler_helada.transform(X_helada)
                    
                    score_helada = modelo_helada.decision_function(X_helada_s)[0]
                    probabilidad_helada = 1 / (1 + np.exp(-score_helada)) * 100
                    
                    # DETERMINAR RIESGO
                    if temp_pred <= -2:
                        riesgo, emoji, color = "MUY ALTO", "🔴", "red"
                    elif temp_pred <= 0:
                        riesgo, emoji, color = "ALTO", "🟠", "orange"
                    elif temp_pred <= 2:
                        riesgo, emoji, color = "MEDIO", "🟡", "yellow"
                    elif temp_pred <= 4:
                        riesgo, emoji, color = "BAJO", "🟢", "green"
                    else:
                        riesgo, emoji, color = "MUY BAJO", "🟢", "green"
                    
                    coords = self.coordenadas.get(codigo, {})
                    
                    predicciones_estaciones.append({
                        "codigo": codigo,
                        "nombre": coords.get('nombre', estacion),
                        "temperatura_predicha": temp_pred,
                        "probabilidad_helada": float(probabilidad_helada),
                        "riesgo": riesgo,
                        "emoji_riesgo": emoji,
                        "color_mapa": color,
                        "lat": coords.get('lat', None),
                        "lon": coords.get('lon', None),
                        "alt": coords.get('alt', None),
                        "helada_predicha": int(temp_pred <= 0)
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error prediciendo {estacion}: {e}")
                    continue
            
            resultado = {
                "fecha_consulta": fecha_consulta.date(),
                "fecha_prediccion": (fecha_consulta + pd.Timedelta(days=1)).date(),
                "predicciones_estaciones": predicciones_estaciones,
                "timestamp": datetime.now(),
                "registros_usados": len(df_hasta_hoy)
            }
            
            self._ultima_prediccion = resultado
            
            print(f"✅ Predicción completada para {len(predicciones_estaciones)} estaciones")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error en predicción: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def interpolar_idw(self, lat_click, lon_click, predicciones, potencia=2):
        """
        Interpolación IDW (Inverse Distance Weighting) para temperatura
        
        Args:
            lat_click: Latitud del punto de interés
            lon_click: Longitud del punto de interés
            predicciones: Lista de predicciones por estación
            potencia: Exponente para el peso (default=2)
        
        Returns:
            float: Temperatura interpolada
        """
        try:
            pesos_totales = 0
            temp_interpolada = 0
            epsilon = 1e-10  # Evitar división por cero
            
            estaciones_validas = 0
            for pred in predicciones:
                if pred['lat'] is None or pred['lon'] is None:
                    continue
                
                # Calcular distancia euclidiana en km (aproximación)
                delta_lat = (pred['lat'] - lat_click) * 111.0  # 1° lat ≈ 111 km
                delta_lon = (pred['lon'] - lon_click) * 111.0 * np.cos(np.radians(lat_click))
                dist_km = np.sqrt(delta_lat**2 + delta_lon**2)
                
                # Si el punto está muy cerca de una estación, usar directamente su valor
                if dist_km < 0.1:  # Menos de 100 metros
                    return pred['temperatura_predicha']
                
                # Calcular peso IDW
                peso = 1.0 / (dist_km ** potencia + epsilon)
                pesos_totales += peso
                temp_interpolada += peso * pred['temperatura_predicha']
                estaciones_validas += 1
            
            if pesos_totales == 0 or estaciones_validas == 0:
                return None
            
            return temp_interpolada / pesos_totales
            
        except Exception as e:
            print(f"❌ Error en interpolación IDW: {e}")
            return None
    
    def interpolar_probabilidad_helada(self, lat_click, lon_click, predicciones, potencia=2):
        """
        Interpolación IDW para probabilidad de helada
        """
        try:
            pesos_totales = 0
            prob_interpolada = 0
            epsilon = 1e-10
            
            estaciones_validas = 0
            for pred in predicciones:
                if pred['lat'] is None or pred['lon'] is None:
                    continue
                
                # Calcular distancia
                delta_lat = (pred['lat'] - lat_click) * 111.0
                delta_lon = (pred['lon'] - lon_click) * 111.0 * np.cos(np.radians(lat_click))
                dist_km = np.sqrt(delta_lat**2 + delta_lon**2)
                
                if dist_km < 0.1:
                    return pred['probabilidad_helada']
                
                # Calcular peso
                peso = 1.0 / (dist_km ** potencia + epsilon)
                pesos_totales += peso
                prob_interpolada += peso * pred['probabilidad_helada']
                estaciones_validas += 1
            
            if pesos_totales == 0 or estaciones_validas == 0:
                return None
            
            return prob_interpolada / pesos_totales
            
        except Exception as e:
            print(f"❌ Error interpolando probabilidad: {e}")
            return None