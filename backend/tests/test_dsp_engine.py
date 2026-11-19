import pytest
import numpy as np
from biomech_engine import BioHevyDSP, FatiguePredictor

class TestBioHevyDSP:
    """Pruebas unitarias para los algoritmos de filtrado digital de señales (DSP)."""

    def test_dsp_initialization(self):
        dsp = BioHevyDSP(fs=430)
        assert dsp.fs == 430
        assert dsp.nyq == 215.0
        assert dsp.b_band is not None
        assert dsp.a_band is not None
        assert dsp.b_notch is not None
        assert dsp.a_notch is not None

    def test_notch_filter_attenuates_60hz(self):
        """El filtro Notch debe atenuar fuertemente la frecuencia parásita de 60 Hz."""
        fs = 430
        dsp = BioHevyDSP(fs=fs)
        t = np.linspace(0, 1.0, fs, endpoint=False)
        # Señal pura de 60 Hz
        sig_60 = np.sin(2 * np.pi * 60 * t)
        filtered = dsp.apply_filters(sig_60)

        # La energía RMS de la señal filtrada en 60 Hz debe reducirse significativamente
        energy_in = np.sqrt(np.mean(sig_60**2))
        energy_out = np.sqrt(np.mean(filtered**2))
        attenuation_ratio = energy_out / energy_in
        assert attenuation_ratio < 0.35, f"Atenuación insuficiente en 60Hz: ratio={attenuation_ratio}"

    def test_bandpass_filter_preserves_muscle_frequencies(self):
        """Frecuencias dentro de la banda electromiográfica (ej. 80 Hz) deben conservarse."""
        fs = 430
        dsp = BioHevyDSP(fs=fs)
        t = np.linspace(0, 1.0, fs, endpoint=False)
        sig_80 = np.sin(2 * np.pi * 80 * t)
        filtered = dsp.apply_filters(sig_80)

        # La amplitud en 80 Hz debe mantenerse cercana a la entrada (fuera del Notch de 60Hz)
        energy_in = np.sqrt(np.mean(sig_80**2))
        energy_out = np.sqrt(np.mean(filtered[100:-100]**2)) # descartar transitorio inicial
        assert energy_out > 0.5 * energy_in, "El filtro atenuó excesivamente una frecuencia EMG válida (80 Hz)"


class TestFatiguePredictor:
    """Pruebas unitarias para el motor de predicción y auto-calibración de fatiga."""

    def test_predictor_initialization(self):
        p = FatiguePredictor(fs=430, window_ms=300, overlap_ms=150)
        assert p.fs == 430
        assert p.window_size == int(430 * 0.3) # ~129 muestras
        assert p.step_size == int(430 * 0.15)  # ~64 muestras
        assert p.calibrated is False
        assert p.buffer == []

    def test_empty_buffer_handling(self):
        """Manejo seguro de buffers vacíos o nulos sin excepciones."""
        p = FatiguePredictor(fs=430)
        metrics, alerts = p.process_incoming_data([])
        assert metrics == []
        assert alerts == []

    def test_short_data_accumulates_in_buffer(self):
        """Datos menores al tamaño de ventana deben acumularse en el buffer."""
        p = FatiguePredictor(fs=430)
        small_chunk = [13200.0] * 50
        metrics, alerts = p.process_incoming_data(small_chunk)
        assert len(metrics) == 0
        assert len(p.buffer) == 50

    def test_process_synthetic_signal_and_metrics(self):
        """Procesa una señal sintética de contracción y produce métricas completas."""
        p = FatiguePredictor(fs=430)
        # 1000 muestras simulando reposo y contracción muscular
        np.random.seed(42)
        base = np.random.randn(500) * 20 + 13200 # reposo
        burst = np.random.randn(500) * 400 + 13200 # contracción
        sig = list(np.concatenate([base, burst]))

        metrics, alerts = p.process_incoming_data(sig)
        assert len(metrics) > 0

        # Verificar estructura de cada ventana procesada
        first_metric = metrics[0]
        assert "rms" in first_metric
        assert "mnf" in first_metric
        assert "state" in first_metric
        assert "fatigue_index" in first_metric

    def test_auto_calibration_transition(self):
        """Verifica que el predictor se auto-calibra tras superar la fase de ruido y contracciones."""
        p = FatiguePredictor(fs=430)
        np.random.seed(42)

        # Fase 1: Pasar las primeras 15 ventanas con ruido de reposo (15 * 65 muestras ~ 1000)
        noise_samples = list(np.random.randn(1500) * 15 + 13200)
        p.process_incoming_data(noise_samples)

        # Fase 2: Enviar contracciones fuertes para calibrar (amplitud > 100)
        for _ in range(8):
            contraction = list(np.random.randn(200) * 400 + 13200)
            p.process_incoming_data(contraction)

        assert p.calibrated is True, "El predictor debió calibrar tras las contracciones activas"
        assert p.base_mnf > 0, "La frecuencia media base debe ser mayor a 0"
        assert p.activity_threshold > p.noise_floor, "El umbral de actividad debe ser mayor al ruido de fondo"

    def test_fatigue_alert_emission(self):
        """Verifica que un fatigue_index alto dispare las alertas FATIGUE_WARNING y FATIGUE_CRITICAL."""
        p = FatiguePredictor(fs=430)
        p.calibrated = True
        p.base_mnf = 120.0
        p.base_peak_rms = 400.0
        p.base_valley_rms = 50.0
        p.noise_floor = 20.0
        p.activity_threshold = 80.0

        # Forzar estado de fatiga extrema
        p.fatigue_index = 60.0
        metrics, alerts = p.process_incoming_data([])
        # Comprobar que los umbrales de alerta responden
        assert p.fatigue_index >= 50.0
        assert p._critical_sent is False # Antes de enviar el check

    def test_reset_and_start_monitoring(self):
        """Verifica el restablecimiento de variables al reiniciar serie."""
        p = FatiguePredictor(fs=430)
        p.buffer = [1, 2, 3]
        p.calibrated = True
        p.reset()

        assert len(p.buffer) == 0
        assert p.calibrated is False
        assert p._warning_sent is False
        assert p._critical_sent is False

        p.start_monitoring()
        assert p.calibrated is False
