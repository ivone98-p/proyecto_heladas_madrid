# predictor_multiestacion.py
# VERSIÓN HÍBRIDA CON COORDENADAS DESDE CSV Y CACHÉ

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime, timedelta

class PredictorHeladasMulti:
    def __init__(self):
        base_dir = Path(__file__).parent.parent / "Datos"
        
        self.modelo_madrid_dir = base_dir / "modelos_entrenados"
        self.modelo_unificado_dir = base_dir / "modelo_unificado_SIN_MADRID"
        self.datos_dir = base_dir / "datos_imputados"
        self.metadata_path = base_dir / "datos_prediccion" / "metadata_estaciones.csv"
        
        # ✅ Cache de predicciones
        self._ultima_prediccion = None
        self._fecha_cache = None
        
        print("="*60)
        print("PREDICTOR HÍBRIDO OFICIAL")
        print("   → Madrid: modelo dedicado")
        print("   → Resto: modelo unificado")
        print("="*60)
        
        self._cargar_modelos()
        self._cargar_datos()
        self._cargar_coordenadas()

    def _cargar_coordenadas(self):
        """Carga coordenadas desde CSV de metadata"""
        try:
            if not self.metadata_path.exists():
                print(f"⚠️ No se encontró: {self.metadata_path}")
                print("⚠️ Usando coordenadas por defecto")
                self._usar_coordenadas_defecto()
                return
            
            metadata = pd.read_csv(self.metadata_path)
            print(f"✅ Metadata CSV cargada: {len(metadata)} estaciones")
            
            self.coordenadas = {}
            for _, row in metadata.iterrows():
                codigo = str(row['CodigoEstacion'])
                self.coordenadas[codigo] = {
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'alt': float(row['alt']),
                    'nombre': str(row['nombre'])
                }
            
            print(f"✅ Coordenadas cargadas para {len(self.coordenadas)} estaciones:")
            for cod, info in self.coordenadas.items():
                print(f"   {cod}: {info['nombre']} ({info['lat']:.4f}, {info['lon']:.4f})")
                
        except Exception as e:
            print(f"⚠️ Error cargando coordenadas: {e}")
            self._usar_coordenadas_defecto()
    
    def _usar_coordenadas_defecto(self):
        """Coordenadas de respaldo si no existe el CSV"""
        self.coordenadas = {
            "21205880": {"lat": 4.789722222, "lon": -74.26477778, "alt": 2600, "nombre": "Flores Chibcha"},
            "21206060": {"lat": 4.75, "lon": -74.3, "alt": 2550, "nombre": "Estación 2"},
            "21205420": {"lat": 4.78, "lon": -74.28, "alt": 2580, "nombre": "Estación 3"},
            "21205960": {"lat": 4.80, "lon": -74.25, "alt": 2620, "nombre": "Estación 4"},
            "21205980": {"lat": 4.77, "lon": -74.27, "alt": 2590, "nombre": "Estación 5"},
            "21205870": {"lat": 4.82, "lon": -74.26, "alt": 2610, "nombre": "Estación 6"},
            "21205940": {"lat": 4.76, "lon": -74.29, "alt": 2570, "nombre": "Estación 7"},
        }
        print("⚠️ Usando coordenadas por defecto")

    def _cargar_modelos(self):
        print("Cargando modelos...")
        
        # MADRID
        self.m_temp = joblib.load(self.modelo_madrid_dir / "modelo_temperatura_ridge.pkl")
        self.s_temp = joblib.load(self.modelo_madrid_dir / "scaler_temperatura.pkl")
        self.f_temp = joblib.load(self.modelo_madrid_dir / "features_temperatura.pkl")
        self.m_helada = joblib.load(self.modelo_madrid_dir / "modelo_helada_ridge.pkl")
        self.s_helada = joblib.load(self.modelo_madrid_dir / "scaler_helada.pkl")
        self.f_helada = joblib.load(self.modelo_madrid_dir / "features_helada.pkl")
        
        # RESTO
        self.mu_temp = joblib.load(self.modelo_unificado_dir / "modelo_temperatura_SIN_MADRID.pkl")
        self.su_temp = joblib.load(self.modelo_unificado_dir / "scaler_temperatura_SIN_MADRID.pkl")
        self.fu_temp = joblib.load(self.modelo_unificado_dir / "features_temperatura_SIN_MADRID.pkl")
        self.mu_helada = joblib.load(self.modelo_unificado_dir / "modelo_helada_SIN_MADRID.pkl")
        self.su_helada = joblib.load(self.modelo_unificado_dir / "scaler_helada_SIN_MADRID.pkl")
        self.fu_helada = joblib.load(self.modelo_unificado_dir / "features_helada_SIN_MADRID.pkl")

        print("✅ Modelos cargados")

    def _cargar_datos(self):
        path = self.datos_dir / "cundinamarca_imputado_v1.csv"
        self.df = pd.read_csv(path)
        self.df["Fecha"] = pd.to_datetime(self.df["Fecha"])
        print(f"✅ Datos cargados: {len(self.df)} registros")

    def _crear_features_madrid(self, df_input, target_col, incluir_prec_tmax=False):
        """Features COMPLETOS para Madrid (con Trimestre y quantiles)"""
        df_out = df_input.copy()
        
        # Temporales COMPLETOS
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
        
        # Rolling
        for window in [3, 7, 14, 30]:
            df_out[f'TMIN_ma_{window}'] = df_out[target_col].shift(1).rolling(window).mean()
            df_out[f'TMIN_std_{window}'] = df_out[target_col].shift(1).rolling(window).std()
            df_out[f'TMIN_min_{window}'] = df_out[target_col].shift(1).rolling(window).min()
            df_out[f'TMIN_max_{window}'] = df_out[target_col].shift(1).rolling(window).max()
        
        # Diferencias
        df_out['TMIN_diff_1'] = df_out[target_col].diff(1)
        df_out['TMIN_diff_7'] = df_out[target_col].diff(7)
        df_out['TMIN_diff_30'] = df_out[target_col].diff(30)
        
        # Tendencias
        def calcular_tendencia(serie):
            if len(serie) < 5 or serie.isna().all():
                return 0
            try:
                return np.polyfit(np.arange(len(serie)), serie.values, 1)[0]
            except:
                return 0
        
        for window in [7, 14, 30]:
            df_out[f'TMIN_tendencia_{window}'] = df_out[target_col].shift(1).rolling(window).apply(
                calcular_tendencia, raw=False
            )
        
        # Rangos
        for window in [7, 14, 30]:
            df_out[f'TMIN_rango_{window}'] = df_out[f'TMIN_max_{window}'] - df_out[f'TMIN_min_{window}']
        
        # QUANTILES
        for window in [7, 14, 30]:
            df_out[f'TMIN_q25_{window}'] = df_out[target_col].shift(1).rolling(window).quantile(0.25)
            df_out[f'TMIN_q75_{window}'] = df_out[target_col].shift(1).rolling(window).quantile(0.75)
        
        # Aceleración
        df_out['TMIN_aceleracion'] = df_out['TMIN_diff_1'].diff(1)
        
        # PREC y TMax
        if incluir_prec_tmax:
            columnas_prec = [col for col in df_out.columns if 'PREC' in col and col != target_col]
            columnas_tmax = [col for col in df_out.columns if 'TMax' in col and col != target_col]
            
            if len(columnas_prec) > 0:
                for col in columnas_prec:
                    df_out[f'{col}_lag1'] = df_out[col].shift(1)
                
                cols_prec_lag = [f'{col}_lag1' for col in columnas_prec]
                df_out['PREC_promedio'] = df_out[cols_prec_lag].mean(axis=1)
                df_out['PREC_max'] = df_out[cols_prec_lag].max(axis=1)
                df_out['PREC_std'] = df_out[cols_prec_lag].std(axis=1)
                
                for lag in [2, 3, 7]:
                    df_out[f'PREC_promedio_lag{lag}'] = df_out['PREC_promedio'].shift(lag)
                
                for window in [3, 7, 14]:
                    df_out[f'PREC_suma_{window}'] = df_out['PREC_promedio'].shift(1).rolling(window).sum()
            
            if len(columnas_tmax) > 0:
                for col in columnas_tmax:
                    df_out[f'{col}_lag1'] = df_out[col].shift(1)
                
                cols_tmax_lag = [f'{col}_lag1' for col in columnas_tmax]
                df_out['TMAX_promedio'] = df_out[cols_tmax_lag].mean(axis=1)
                df_out['TMAX_std'] = df_out[cols_tmax_lag].std(axis=1)
                df_out['Rango_termico_lag1'] = df_out['TMAX_promedio'] - df_out['TMIN_lag_1']
                
                for window in [3, 7, 14]:
                    df_out[f'TMAX_ma_{window}'] = df_out['TMAX_promedio'].shift(1).rolling(window).mean()
                
                df_out['TMAX_diff_1'] = df_out['TMAX_promedio'].diff(1)
            
            if 'TMAX_promedio' in df_out.columns and 'TMIN_lag_1' in df_out.columns:
                df_out['TMax_TMin_ratio'] = df_out['TMAX_promedio'] / (df_out['TMIN_lag_1'].abs() + 1)
            
            if 'PREC_promedio' in df_out.columns:
                df_out['PREC_binaria'] = (df_out['PREC_promedio'] > 0).astype(int)
            
            for col in columnas_prec + columnas_tmax:
                if col in df_out.columns:
                    df_out.drop(col, axis=1, inplace=True)
        
        return df_out.dropna().reset_index(drop=True)

    def _crear_features_unificado(self, df_input, target_col, incluir_prec_tmax=False):
        """Features para modelo unificado (SIN Trimestre, SIN quantiles)"""
        df_out = df_input.copy()
        
        df_out['Mes'] = df_out['Fecha'].dt.month
        df_out['DíaAño'] = df_out['Fecha'].dt.dayofyear
        df_out['Semana'] = df_out['Fecha'].dt.isocalendar().week
        df_out['DiaSemana'] = df_out['Fecha'].dt.dayofweek
        
        df_out['Mes_sin'] = np.sin(2 * np.pi * df_out['Mes']/12)
        df_out['Mes_cos'] = np.cos(2 * np.pi * df_out['Mes']/12)
        df_out['DíaAño_sin'] = np.sin(2 * np.pi * df_out['DíaAño']/365)
        df_out['DíaAño_cos'] = np.cos(2 * np.pi * df_out['DíaAño']/365)
        df_out['Semana_sin'] = np.sin(2 * np.pi * df_out['Semana']/52)
        df_out['Semana_cos'] = np.cos(2 * np.pi * df_out['Semana']/52)
        df_out['DiaSemana_sin'] = np.sin(2 * np.pi * df_out['DiaSemana']/7)
        df_out['DiaSemana_cos'] = np.cos(2 * np.pi * df_out['DiaSemana']/7)

        for lag in [1,2,3,7,14,21,30]:
            df_out[f'TMIN_lag_{lag}'] = df_out[target_col].shift(lag)

        for w in [3,7,14,30]:
            df_out[f'TMIN_ma_{w}'] = df_out[target_col].shift(1).rolling(w).mean()
            df_out[f'TMIN_std_{w}'] = df_out[target_col].shift(1).rolling(w).std()
            df_out[f'TMIN_min_{w}'] = df_out[target_col].shift(1).rolling(w).min()
            df_out[f'TMIN_max_{w}'] = df_out[target_col].shift(1).rolling(w).max()

        df_out['TMIN_diff_1'] = df_out[target_col].diff(1)
        df_out['TMIN_diff_7'] = df_out[target_col].diff(7)
        df_out['TMIN_diff_30'] = df_out[target_col].diff(30)

        def tendencia(s):
            if len(s) < 5 or s.isna().all(): return 0
            try: return np.polyfit(np.arange(len(s)), s, 1)[0]
            except: return 0

        for w in [7,14,30]:
            df_out[f'TMIN_tendencia_{w}'] = df_out[target_col].shift(1).rolling(w).apply(tendencia, raw=False)
            df_out[f'TMIN_rango_{w}'] = df_out[f'TMIN_max_{w}'] - df_out[f'TMIN_min_{w}']

        df_out['TMIN_aceleracion'] = df_out['TMIN_diff_1'].diff(1)
        
        # PREC y TMax
        if incluir_prec_tmax:
            columnas_prec = [col for col in df_out.columns if 'PREC' in col and col != target_col]
            columnas_tmax = [col for col in df_out.columns if 'TMax' in col and col != target_col]
            
            if len(columnas_prec) > 0:
                for col in columnas_prec:
                    df_out[f'{col}_lag1'] = df_out[col].shift(1)
                
                cols_prec_lag = [f'{col}_lag1' for col in columnas_prec]
                df_out['PREC_promedio'] = df_out[cols_prec_lag].mean(axis=1)
                df_out['PREC_binaria'] = (df_out['PREC_promedio'] > 0).astype(int)
            
            if len(columnas_tmax) > 0:
                for col in columnas_tmax:
                    df_out[f'{col}_lag1'] = df_out[col].shift(1)
                
                cols_tmax_lag = [f'{col}_lag1' for col in columnas_tmax]
                df_out['TMAX_promedio'] = df_out[cols_tmax_lag].mean(axis=1)
                
                if 'TMIN_lag_1' in df_out.columns:
                    df_out['Rango_termico_lag1'] = df_out['TMAX_promedio'] - df_out['TMIN_lag_1']
            
            for col in columnas_prec + columnas_tmax:
                if col in df_out.columns:
                    df_out.drop(col, axis=1, inplace=True)
        
        return df_out.dropna().reset_index(drop=True)

    def predecir(self, fecha_consulta=None, forzar_recalculo=False):
        """
        Genera predicciones híbridas con sistema de caché
        
        Args:
            fecha_consulta: Fecha para la cual predecir (default: hoy)
            forzar_recalculo: Si True, ignora el caché y recalcula (default: False)
        """
        if fecha_consulta is None:
            fecha_consulta = pd.Timestamp.now().normalize()
        else:
            fecha_consulta = pd.to_datetime(fecha_consulta).normalize()

        # ✅ Verificar caché
        if not forzar_recalculo and self._ultima_prediccion is not None:
            if self._fecha_cache == fecha_consulta:
                print("📦 Usando predicción cacheada")
                return self._ultima_prediccion

        print("🔄 Calculando nueva predicción...")

        fecha_limite = fecha_consulta - timedelta(days=1)
        df_hoy = self.df[self.df['Fecha'] <= fecha_limite].copy()
        if len(df_hoy) < 100:
            return {"error": "Datos insuficientes"}

        predicciones = []
        
        # Detectar estaciones
        cols_tmin = [c for c in df_hoy.columns if c.startswith('TMin_')]
        estaciones_disponibles = {}
        
        for col in cols_tmin:
            partes = col.split('_')
            if len(partes) >= 3:
                codigo = partes[1]
                nombre_col = '_'.join(partes[2:])
                estaciones_disponibles[codigo] = nombre_col

        print(f"📊 Estaciones: {len(estaciones_disponibles)}")

        # Columnas PREC y TMax
        columnas_prec = [col for col in df_hoy.columns if 'PREC' in col]
        columnas_tmax = [col for col in df_hoy.columns if 'TMax' in col]

        for codigo, nombre_col in estaciones_disponibles.items():
            col_tmin = next((c for c in df_hoy.columns if c.startswith(f"TMin_{codigo}_")), None)
            
            if not col_tmin:
                continue

            try:
                # OBTENER NOMBRE Y COORDENADAS DESDE CSV
                coords_info = self.coordenadas.get(codigo, {})
                nombre_estacion = coords_info.get('nombre', nombre_col)
                
                if codigo == "21205880":
                    # MADRID
                    print(f"   → Madrid: usando modelo dedicado")
                    
                    df_temp = df_hoy[['Fecha', col_tmin]].dropna()
                    if len(df_temp) < 50:
                        continue
                    
                    df_feat_temp = self._crear_features_madrid(df_temp, col_tmin, incluir_prec_tmax=False)
                    if len(df_feat_temp) == 0:
                        continue
                    
                    X = df_feat_temp[self.f_temp].iloc[[-1]]
                    temp_pred = float(self.m_temp.predict(self.s_temp.transform(X))[0])
                    
                    df_helada = df_hoy[['Fecha', col_tmin] + columnas_prec + columnas_tmax].copy()
                    df_helada = df_helada.dropna(subset=[col_tmin])
                    
                    for col in columnas_prec + columnas_tmax:
                        if df_helada[col].isna().any():
                            df_helada[col].fillna(df_helada[col].mean(), inplace=True)
                    
                    df_feat_helada = self._crear_features_madrid(df_helada, col_tmin, incluir_prec_tmax=True)
                    if len(df_feat_helada) == 0:
                        continue
                    
                    Xh = df_feat_helada[self.f_helada].iloc[[-1]]
                    score = self.m_helada.decision_function(self.s_helada.transform(Xh))[0]
                    
                else:
                    # OTRAS ESTACIONES
                    df_temp = df_hoy[['Fecha', col_tmin]].dropna()
                    if len(df_temp) < 50:
                        continue
                    
                    df_feat_temp = self._crear_features_unificado(df_temp, col_tmin, incluir_prec_tmax=False)
                    if len(df_feat_temp) == 0:
                        continue
                    
                    X = df_feat_temp[self.fu_temp].iloc[[-1]]
                    temp_pred = float(self.mu_temp.predict(self.su_temp.transform(X))[0])
                    
                    df_helada = df_hoy[['Fecha', col_tmin] + columnas_prec + columnas_tmax].copy()
                    df_helada = df_helada.dropna(subset=[col_tmin])
                    
                    for col in columnas_prec + columnas_tmax:
                        if df_helada[col].isna().any():
                            df_helada[col].fillna(df_helada[col].mean(), inplace=True)
                    
                    df_feat_helada = self._crear_features_unificado(df_helada, col_tmin, incluir_prec_tmax=True)
                    if len(df_feat_helada) == 0:
                        continue
                    
                    Xh = df_feat_helada[self.fu_helada].iloc[[-1]]
                    score = self.mu_helada.decision_function(self.su_helada.transform(Xh))[0]

                # Probabilidad y riesgo
                prob = 1 / (1 + np.exp(-score)) * 100

                if temp_pred <= -2:
                    riesgo, emoji, color = "MUY ALTO", "🔴", "red"
                elif temp_pred <= 0:
                    riesgo, emoji, color = "ALTO", "🟠", "orange"
                elif temp_pred <= 2:
                    riesgo, emoji, color = "MEDIO", "🟡", "yellow"
                elif temp_pred <= 4:
                    riesgo, emoji, color = "BAJO", "🟢", "lightblue"
                else:
                    riesgo, emoji, color = "MUY BAJO", "🟢", "green"

                predicciones.append({
                    "codigo": codigo,
                    "nombre": nombre_estacion,
                    "temperatura_predicha": round(temp_pred, 2),
                    "probabilidad_helada": round(prob, 1),
                    "riesgo": riesgo,
                    "emoji_riesgo": emoji,
                    "color_mapa": color,
                    "lat": coords_info.get('lat'),
                    "lon": coords_info.get('lon'),
                    "alt": coords_info.get('alt', 0)
                })
                
                print(f"   ✅ {nombre_estacion}: {temp_pred:.1f}°C ({riesgo})")

            except Exception as e:
                print(f"   ❌ Error en {codigo}: {e}")
                import traceback
                traceback.print_exc()
                continue

        if len(predicciones) == 0:
            return {"error": "No se generaron predicciones"}

        print(f"✅ Total: {len(predicciones)} estaciones")
        
        resultado = {
            "fecha_consulta": fecha_limite.date(),
            "fecha_prediccion": fecha_consulta.date(),
            "predicciones_estaciones": predicciones
        }
        
        # ✅ Guardar en caché
        self._ultima_prediccion = resultado
        self._fecha_cache = fecha_consulta
        
        return resultado

    def interpolar_idw(self, lat, lon, predicciones, potencia=2):
        pesos_total = temp_ponderada = 0
        
        for p in predicciones:
            if p['lat'] is None or p['lon'] is None:
                continue
            
            dlat = (p['lat'] - lat) * 111
            dlon = (p['lon'] - lon) * 111 * np.cos(np.radians(lat))
            distancia = np.sqrt(dlat**2 + dlon**2)
            
            if distancia < 0.01:
                return p['temperatura_predicha']
            
            peso = 1 / (distancia ** potencia)
            pesos_total += peso
            temp_ponderada += peso * p['temperatura_predicha']
        
        return temp_ponderada / pesos_total if pesos_total > 0 else None

    def interpolar_probabilidad_helada(self, lat, lon, predicciones, potencia=2):
        pesos_total = prob_ponderada = 0
        
        for p in predicciones:
            if p['lat'] is None or p['lon'] is None:
                continue
            
            dlat = (p['lat'] - lat) * 111
            dlon = (p['lon'] - lon) * 111 * np.cos(np.radians(lat))
            distancia = np.sqrt(dlat**2 + dlon**2)
            
            if distancia < 0.01:
                return p['probabilidad_helada']
            
            peso = 1 / (distancia ** potencia)
            pesos_total += peso
            prob_ponderada += peso * p['probabilidad_helada']
        
        return prob_ponderada / pesos_total if pesos_total > 0 else None