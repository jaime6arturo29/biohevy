import sys
sys.path.insert(0, '.')
from biomech_engine import FatiguePredictor
import numpy as np

p = FatiguePredictor(fs=430, window_ms=300, overlap_ms=150)
print(f"OK: window={p.window_size} step={p.step_size} fs={p.fs}")

# Simular datos: señal con ruido + contracción muscular
data = list(np.random.randn(500) * 50 + 13200)  # ruido base
# Agregar una "contracción" (amplitud alta)
contraction = list(np.random.randn(300) * 500 + 13200)
data.extend(contraction)

m, a = p.process_incoming_data(data)
print(f"Ventanas procesadas: {len(m)}")
for i, x in enumerate(m):
    rms = x.get('rms', 0)
    mnf = x.get('mnf', 0)
    fi = x.get('fatigue_index', 0)
    st = x.get('state', '?')
    print(f"  #{i}: RMS={rms:.0f} MNF={mnf:.0f}Hz FI={fi:.1f}% Estado={st}")

if a:
    print(f"Alertas: {a}")
else:
    print("Sin alertas (normal para datos tan cortos)")
