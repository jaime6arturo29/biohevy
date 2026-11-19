"""
BioHevy Motor de Predicción de Fatiga v4 — Ingeniería Corregida

Correcciones respecto a versiones anteriores:
1. fs corregido a 430 Hz (frecuencia real del ADS1115 leyendo 2 canales por I2C)
2. Filtro pasa-banda ajustado a 20-200 Hz (dentro del límite de Nyquist a 215 Hz)
3. MNF calculada SOLO durante contracciones activas (no durante reposo entre reps)
4. Sistema multi-indicador: MNF contracción + RMS valleys + RMS picos
5. Ventana ampliada a 300ms para mejor resolución espectral
"""
import numpy as np
from scipy.signal import butter, lfilter, iirnotch
from scipy.fft import fft, fftfreq
from collections import deque


class BioHevyDSP:
    """DSP corregido para la frecuencia REAL del hardware"""
    def __init__(self, fs=430):
        self.fs = fs
        self.nyq = 0.5 * fs  # 215 Hz
        
        # Filtro Pasa-Banda 20-200 Hz (DENTRO del Nyquist de 215 Hz)
        low = 20.0 / self.nyq
        high = 200.0 / self.nyq
        self.b_band, self.a_band = butter(4, [low, high], btype='band')
        
        # Filtro Notch 60 Hz
        w0 = 60.0 / self.nyq
        self.b_notch, self.a_notch = iirnotch(w0, 30.0)

    def apply_filters(self, data):
        centered = np.array(data, dtype=np.float64) - np.mean(data)
        y_band = lfilter(self.b_band, self.a_band, centered)
        y_clean = lfilter(self.b_notch, self.a_notch, y_band)
        return y_clean


class FatiguePredictor:
    """
    Predictor de fatiga multi-indicador para ejercicios dinámicos.
    
    En lugar de usar solo MNF (que falla con ejercicio dinámico),
    combina 3 indicadores:
    
    1. MNF durante contracción: solo se calcula cuando hay esfuerzo real
    2. RMS de valles (entre reps): sube cuando el músculo no puede relajarse
    3. RMS de picos (durante contracción): baja cuando el músculo ya no puede generar fuerza
    
    SIEMPRE procesa datos (sin estados bloqueantes).
    Se auto-calibra con las primeras contracciones detectadas.
    """
    # Frecuencia REAL: ADS1115 leyendo 2 canales por I2C ≈ 430 Hz por canal
    EFFECTIVE_FS = 430
    
    # Ventana de 300ms para mejor resolución espectral (~129 muestras a 430 Hz)
    WINDOW_MS = 300
    OVERLAP_MS = 150
    
    # Calibración: solo 4 ventanas activas (~primera rep completa)
    BASELINE_CONTRACTIONS = 4
    
    # Pesos del score multi-indicador
    # Valley tiene más peso porque es el indicador más fiable con este hardware
    W_MNF = 0.25      # Peso de la caída de MNF
    W_VALLEY = 0.45    # Peso de la elevación de valles (relajación incompleta)
    W_PEAK = 0.30      # Peso de la caída de picos (pérdida de fuerza)
    
    def __init__(self, fs=430, window_ms=300, overlap_ms=150):
        self.fs = fs
        self.window_size = int(fs * (window_ms / 1000.0))  # ~129 muestras
        self.step_size = int(fs * ((window_ms - overlap_ms) / 1000.0))  # ~65 muestras
        
        self.dsp = BioHevyDSP(fs=fs)
        self.buffer = []
        
        # === Estado de calibración ===
        self.calibrated = False
        self.noise_floor = 0.0
        self.noise_count = 0
        self.activity_threshold = 0.0
        
        # Valores de línea base (primeras reps)
        self.baseline_active_mnf_values = []  # MNF durante contracciones (calibración)
        self.baseline_active_rms_values = []  # RMS de picos (calibración)
        self.baseline_rest_rms_values = []    # RMS de valles (calibración)
        
        self.base_mnf = 0.0         # MNF promedio de contracción en estado fresco
        self.base_peak_rms = 0.0    # RMS pico promedio en estado fresco
        self.base_valley_rms = 0.0  # RMS de reposo en estado fresco
        
        # === Tracking en tiempo real ===
        # Historial de RMS recientes para estimar el ruido mínimo dinámico (últimos 4.5 segundos)
        self.recent_rms_history = deque(maxlen=30)
        # Historial de MNF solo durante contracciones activas
        self.active_mnf_history = deque(maxlen=40)
        # Historial de RMS durante reposo (valles entre reps)
        self.rest_rms_history = deque(maxlen=30)
        # Historial de RMS pico durante contracciones
        self.peak_rms_history = deque(maxlen=30)
        
        # EMA para suavizado
        self.mnf_ema = 0.0
        self.rest_rms_ema = 0.0
        self.peak_rms_ema = 0.0
        self.ema_init_mnf = False
        self.ema_init_rest = False
        self.ema_init_peak = False
        
        # Score de fatiga compuesto (0-100%)
        self.fatigue_index = 0.0
        
        # Alertas
        self._warning_sent = False
        self._critical_sent = False
        self._window_count = 0

    def reset(self):
        self.buffer.clear()
        self.calibrated = False
        self.noise_floor = 0.0
        self.noise_count = 0
        self.activity_threshold = 0.0
        self.baseline_active_mnf_values.clear()
        self.baseline_active_rms_values.clear()
        self.baseline_rest_rms_values.clear()
        self.base_mnf = 0.0
        self.base_peak_rms = 0.0
        self.base_valley_rms = 0.0
        self.recent_rms_history.clear()
        self.active_mnf_history.clear()
        self.rest_rms_history.clear()
        self.peak_rms_history.clear()
        self.mnf_ema = 0.0
        self.rest_rms_ema = 0.0
        self.peak_rms_ema = 0.0
        self.ema_init_mnf = False
        self.ema_init_rest = False
        self.ema_init_peak = False
        self.fatigue_index = 0.0
        self._warning_sent = False
        self._critical_sent = False
        self._window_count = 0
    
    def start_monitoring(self):
        self.reset()
    def start_calibration(self):
        self.reset()
        
    def _rms(self, segment):
        return float(np.sqrt(np.mean(np.square(segment))))
    
    def _mnf(self, segment):
        """MNF solo en rango 20-200 Hz (dentro del Nyquist real)"""
        n = len(segment)
        if n < 8:
            return 0.0
        yf = fft(segment)
        xf = fftfreq(n, 1.0 / self.fs)
        
        mask = (xf > 20) & (xf < 200)
        freqs = xf[mask]
        power = np.abs(yf[mask]) ** 2
        
        total = np.sum(power)
        if total == 0:
            return 0.0
        return float(np.sum(freqs * power) / total)
    
    def _ema(self, prev, new_val, alpha=0.2):
        return alpha * new_val + (1.0 - alpha) * prev

    def process_incoming_data(self, new_data):
        """SIEMPRE procesa. Sin bloqueo. Auto-calibra."""
        self.buffer.extend(new_data)
        metrics = []
        alerts = []

        while len(self.buffer) >= self.window_size:
            window = np.array(self.buffer[:self.window_size], dtype=np.float64)
            self.buffer = self.buffer[self.step_size:]
            self._window_count += 1
            
            # Filtrar
            clean = self.dsp.apply_filters(window)
            rms = self._rms(clean)
            
            # Guardar en el historial de RMS recientes
            self.recent_rms_history.append(rms)
            
            # --- Fase 1: Estimar piso de ruido dinámico ---
            # Primeras 15 ventanas (~2.3 seg): solo acumular datos, NO clasificar
            if self._window_count < 15:
                metrics.append({"rms": rms, "mnf": 0.0, "fatigue_index": 0.0,
                                "state": "CALIBRATING", "calibration_progress": 0.0})
                continue
            
            # Piso de ruido = percentil 10 de las últimas 30 ventanas
            # (más robusto que el mínimo absoluto, ignora picos anómalos bajos)
            sorted_recent = sorted(self.recent_rms_history)
            p10_idx = max(0, int(len(sorted_recent) * 0.1))
            self.noise_floor = float(sorted_recent[p10_idx])
            
            # Umbral de actividad CONSERVADOR: 3x ruido + mínimo absoluto de 100
            # Esto garantiza que el ruido eléctrico NUNCA se clasifique como contracción
            self.activity_threshold = max(self.noise_floor * 3.0, 100.0)
            
            # --- Clasificar ventana: ACTIVA (contracción) o REPOSO ---
            is_active = rms > self.activity_threshold
            
            # Computar MNF solo si hay contracción activa genuina
            mnf = self._mnf(clean) if is_active else 0.0
            
            # --- Fase 2: Auto-calibración con primeras reps ---
            if not self.calibrated:
                if is_active and mnf > 0:
                    self.baseline_active_mnf_values.append(mnf)
                    self.baseline_active_rms_values.append(rms)
                elif not is_active:
                    self.baseline_rest_rms_values.append(rms)
                
                progress = (len(self.baseline_active_mnf_values) / self.BASELINE_CONTRACTIONS) * 100.0
                
                # Estado visual: LISTENING si aún no hay contracciones, CALIBRATING si ya hay alguna
                cal_state = "CALIBRATING" if len(self.baseline_active_mnf_values) > 0 else "LISTENING"
                metrics.append({
                    "rms": rms, "mnf": mnf, "fatigue_index": 0.0,
                    "state": cal_state,
                    "calibration_progress": min(100.0, progress)
                })
                
                if len(self.baseline_active_mnf_values) >= self.BASELINE_CONTRACTIONS:
                    self.base_mnf = float(np.mean(self.baseline_active_mnf_values))
                    self.base_peak_rms = float(np.mean(self.baseline_active_rms_values))
                    self.base_valley_rms = float(np.mean(self.baseline_rest_rms_values)) if self.baseline_rest_rms_values else self.noise_floor
                    
                    # Inicializar EMAs
                    self.mnf_ema = self.base_mnf
                    self.rest_rms_ema = self.base_valley_rms
                    self.peak_rms_ema = self.base_peak_rms
                    self.ema_init_mnf = True
                    self.ema_init_rest = True
                    self.ema_init_peak = True
                    
                    self.calibrated = True
                    self._warning_sent = False
                    self._critical_sent = False
                    
                    alerts.append({
                        "type": "CALIBRATION_DONE",
                        "msg": f"Base: MNF={self.base_mnf:.0f}Hz RMS_peak={self.base_peak_rms:.0f} RMS_valley={self.base_valley_rms:.0f}"
                    })
                continue
            
            # --- Fase 3: Predicción de fatiga multi-indicador ---
            
            # Indicador 1: MNF durante contracciones
            mnf_score = 0.0
            if is_active and mnf > 0:
                self.mnf_ema = self._ema(self.mnf_ema, mnf, 0.25)
                self.active_mnf_history.append(self.mnf_ema)
                if self.base_mnf > 0:
                    mnf_drop = max(0, (self.base_mnf - self.mnf_ema) / self.base_mnf)
                    mnf_score = min(1.0, mnf_drop * 5.0)  # 20% de caída = score máximo
            
            # Indicador 2: RMS de valles (relajación incompleta)
            valley_score = 0.0
            if not is_active:
                self.rest_rms_ema = self._ema(self.rest_rms_ema, rms, 0.25)
                self.rest_rms_history.append(self.rest_rms_ema)
                if self.base_valley_rms > 0:
                    valley_rise = max(0, (self.rest_rms_ema - self.base_valley_rms) / self.base_valley_rms)
                    valley_score = min(1.0, valley_rise * 3.0)  # 33% de subida = score máximo
            
            # Indicador 3: Caída de RMS pico (pérdida de fuerza)
            peak_score = 0.0
            if is_active:
                self.peak_rms_ema = self._ema(self.peak_rms_ema, rms, 0.2)
                self.peak_rms_history.append(self.peak_rms_ema)
                if self.base_peak_rms > 0:
                    # El RMS primero SUBE (reclutamiento) y luego BAJA (fallo)
                    if len(self.peak_rms_history) > 3:
                        max_peak = max(list(self.peak_rms_history))
                        if max_peak > self.base_peak_rms * 0.9:
                            peak_drop = max(0, (max_peak - self.peak_rms_ema) / max_peak)
                            peak_score = min(1.0, peak_drop * 5.0)  # 20% de caída = score máximo
            
            # Score compuesto ponderado
            # Usar el último score conocido de cada indicador
            latest_mnf = mnf_score if is_active else getattr(self, '_last_mnf_score', 0.0)
            latest_valley = valley_score if not is_active else getattr(self, '_last_valley_score', 0.0)
            latest_peak = peak_score if is_active else getattr(self, '_last_peak_score', 0.0)
            
            # Guardar últimos scores conocidos
            if is_active and mnf > 0:
                self._last_mnf_score = mnf_score
                self._last_peak_score = peak_score
            if not is_active:
                self._last_valley_score = valley_score
            
            # Fatigue Index compuesto (0-100%)
            raw_fi = (latest_mnf * self.W_MNF + latest_valley * self.W_VALLEY + latest_peak * self.W_PEAK) * 100.0
            # Suavizar pero responder rápido (alpha 0.3 = sigue la señal real)
            self.fatigue_index = self._ema(self.fatigue_index, raw_fi, 0.3)
            
            metrics.append({
                "rms": rms, "mnf": self.mnf_ema if is_active else 0.0,
                "fatigue_index": self.fatigue_index,
                "state": "ACTIVE",
                "calibration_progress": 100.0,
                "is_active": is_active,
                # Debug: scores individuales
                "mnf_score": latest_mnf * 100,
                "valley_score": latest_valley * 100,
                "peak_score": latest_peak * 100
            })
            
            # --- Alertas ---
            if self.fatigue_index >= 25.0 and not self._warning_sent:
                self._warning_sent = True
                alerts.append({
                    "type": "FATIGUE_WARNING",
                    "msg": f"Fatiga detectada: {self.fatigue_index:.0f}%",
                    "fatigue_index": self.fatigue_index
                })
            
            if self.fatigue_index >= 50.0 and not self._critical_sent:
                self._critical_sent = True
                alerts.append({
                    "type": "FATIGUE_CRITICAL",
                    "msg": f"FALLO INMINENTE: {self.fatigue_index:.0f}%",
                    "fatigue_index": self.fatigue_index
                })

        return metrics, alerts
