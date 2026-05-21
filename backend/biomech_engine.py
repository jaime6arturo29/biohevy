import numpy as np
from scipy.signal import butter, lfilter, iirnotch
from scipy.fft import fft, fftfreq
from scipy.stats import linregress
from collections import deque

class BioHevyDSP:
    """Procesamiento Digital de Señales (DSP) para EMG"""
    def __init__(self, fs=1000):
        self.fs = fs
        self.nyq = 0.5 * fs
        
        # Filtro Pasa-Banda Butterworth (20 Hz a 450 Hz) de 4to orden
        # Elimina artefactos de movimiento (<20Hz) y ruido de alta frecuencia (>450Hz)
        low = 20.0 / self.nyq
        high = 450.0 / self.nyq
        self.b_band, self.a_band = butter(4, [low, high], btype='band')
        
        # Filtro Notch (60 Hz) para eliminar ruido de la red eléctrica
        w0 = 60.0 / self.nyq
        Q = 30.0
        self.b_notch, self.a_notch = iirnotch(w0, Q)
        
        # Offset de 1.65V en bits. 
        # ADS1115 GAIN_ONE (+/-4.096V a 16 bits -> 1 bit = 0.125mV)
        # 1.65V / 0.000125V = 13200 bits.
        self.dc_offset_bits = 13200

    def apply_filters(self, data):
        """Aplica la secuencia completa de filtros (Pipeline DSP)"""
        # 1. Remoción de DC Offset (centrar la señal en 0V)
        # Se puede usar el valor teórico (13200) o la media móvil. 
        # Usaremos la media de la ventana actual para mayor robustez ante variaciones físicas.
        data_centered = np.array(data) - np.mean(data)
        
        # 2. Filtro Pasa-Banda
        y_band = lfilter(self.b_band, self.a_band, data_centered)
        
        # 3. Filtro Notch
        y_clean = lfilter(self.b_notch, self.a_notch, y_band)
        
        return y_clean


class FatiguePredictor:
    """Modelo Clínico de Predicción de Fatiga (Algoritmo BioHevy)"""
    def __init__(self, fs=1000, window_ms=200, overlap_ms=100):
        self.fs = fs
        self.window_size = int(fs * (window_ms / 1000.0))  # 200 muestras
        self.step_size = int(fs * ((window_ms - overlap_ms) / 1000.0)) # 100 muestras
        
        self.dsp = BioHevyDSP(fs=fs)
        
        # Buffers de entrada por canal
        self.buffer = []
        
        # Historial de características (últimos 3 segundos aprox -> 30 ventanas)
        self.rms_history = deque(maxlen=30) 
        self.mnf_history = deque(maxlen=30)
        
        # Variables de Calibración MVC (Contracción Voluntaria Máxima)
        self.is_calibrated = False
        self.calibration_samples = 0
        self.calibration_target = fs * 3 # 3 segundos de calibración
        self.base_mnf = 0.0
        self.max_rms = 0.0
        
    def calculate_rms(self, segment):
        """Indicador de Amplitud (Reclutamiento de fibras musculares)"""
        return np.sqrt(np.mean(np.square(segment)))

    def calculate_mnf(self, segment):
        """Indicador de Fatiga (Frecuencia Media - Espectro de Potencia)"""
        n = len(segment)
        yf = fft(segment)
        xf = fftfreq(n, 1/self.fs)
        
        # Tomar solo frecuencias positivas
        pos_mask = (xf > 0)
        freqs = xf[pos_mask]
        power_spec = np.abs(yf[pos_mask])**2
        
        total_power = np.sum(power_spec)
        if total_power == 0: 
            return 0.0
            
        mnf = np.sum(freqs * power_spec) / total_power
        return mnf

    def process_incoming_data(self, new_data):
        """
        Ingresa ráfagas de datos (ej. 50 muestras), extrae ventanas con overlap,
        filtra, calcula características y ejecuta el algoritmo de fatiga.
        """
        self.buffer.extend(new_data)
        metrics = []
        alerts = []

        # Mientras haya datos para armar al menos una ventana completa (200 muestras)
        while len(self.buffer) >= self.window_size:
            # 1. Extraer ventana de 200ms
            window = np.array(self.buffer[:self.window_size])
            
            # 2. Deslizar buffer (Overlap del 50% -> avanzamos 100ms)
            self.buffer = self.buffer[self.step_size:]
            
            # 3. Pipeline DSP
            clean_window = self.dsp.apply_filters(window)
            
            # 4. Extracción de Características
            rms = self.calculate_rms(clean_window)
            mnf = self.calculate_mnf(clean_window)
            
            self.rms_history.append(rms)
            self.mnf_history.append(mnf)
            
            metrics.append({"rms": float(rms), "mnf": float(mnf)})

            # 5. Algoritmo BioHevy
            if not self.is_calibrated:
                # Rutina de Calibración (Primeros 3 segundos)
                self.calibration_samples += self.step_size
                if self.calibration_samples >= self.calibration_target:
                    self.base_mnf = np.mean(list(self.mnf_history))
                    self.max_rms = np.max(list(self.rms_history))
                    self.is_calibrated = True
                    alerts.append({"type": "CALIBRATION_DONE", "msg": "Calibración MVC Exitosa"})
            else:
                # Lógica de Predicción: Analizar tendencia de los últimos 2-3 segundos
                if len(self.mnf_history) >= 20: # Al menos 2 segundos de historial
                    rms_arr = list(self.rms_history)
                    mnf_arr = list(self.mnf_history)
                    
                    # Calcular la pendiente (tendencia) mediante regresión lineal
                    slope_mnf, _, r_val_mnf, _, _ = linregress(range(len(mnf_arr)), mnf_arr)
                    slope_rms, _, _, _, _ = linregress(range(len(rms_arr)), rms_arr)
                    
                    # CRITERIO DE FATIGA: 
                    # MNF baja continuamente (velocidad de conducción cae por acidez metabólica)
                    # RMS se mantiene o sube (el sistema nervioso intenta reclutar más fibras para compensar)
                    if slope_mnf < -0.3 and (r_val_mnf**2) > 0.5 and slope_rms >= -0.1:
                        # Asegurar que realmente hay esfuerzo activo (al menos 40% del MVC original)
                        if np.mean(rms_arr[-5:]) > (self.max_rms * 0.4):
                            alerts.append({"type": "FATIGUE_WARNING", "msg": "Fatiga Inminente Detectada"})
                            # Limpiamos parte del historial para no saturar con la misma alerta repetida
                            self.mnf_history.clear()
                            self.rms_history.clear()

        return metrics, alerts
