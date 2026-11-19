"""
BioHevy Diagnostico Rapido
Verifica cada eslabon de la cadena: Backend - WebSocket - Datos
"""
import asyncio
import json
import sys
import time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_HOST = "127.0.0.1"
API_PORT = 8000

async def test_backend():
    import websockets
    
    print("=" * 60)
    print("  BIOHEVY - DIAGNOSTICO DE CONEXION EMG")
    print("=" * 60)
    
    # Test 1: Backend
    print("\n[1/3] Verificando backend...")
    try:
        import urllib.request
        req = urllib.request.urlopen(f"http://{API_HOST}:{API_PORT}/docs", timeout=3)
        print("  [OK] Backend activo")
    except Exception as e:
        print(f"  [FALLO] Backend no responde: {e}")
        print("  -> Ejecuta iniciar_proyecto.bat primero")
        return
    
    # Test 2: WebSocket
    print(f"\n[2/3] Conectando WebSocket...")
    try:
        ws = await websockets.connect(f"ws://{API_HOST}:{API_PORT}/ws/emg/frontend")
        print("  [OK] WebSocket frontend conectado")
        
        await ws.send(json.dumps({"action": "START_MONITORING"}))
        print("  [OK] Comando START_MONITORING enviado")
        
        # Test 3: Datos del ESP32
        print(f"\n[3/3] Esperando datos del ESP32 (15 seg)...")
        print("  Si el ESP32 esta encendido, deberian llegar datos.\n")
        
        start = time.time()
        msg_count = 0
        while time.time() - start < 15:
            try:
                data = await asyncio.wait_for(ws.recv(), timeout=1.0)
                parsed = json.loads(data)
                msg_count += 1
                
                if parsed.get("type") == "REALTIME_EMG":
                    ch1 = parsed.get("ch1", {})
                    raw = ch1.get("raw", [])
                    metrics = ch1.get("metrics")
                    alerts = ch1.get("alerts", [])
                    
                    line = f"  Paquete #{msg_count}: {len(raw)} muestras"
                    if raw:
                        line += f" | Rango:[{min(raw)},{max(raw)}]"
                    if metrics:
                        line += f" | RMS={metrics.get('rms',0):.1f} MNF={metrics.get('mnf',0):.1f}Hz FI={metrics.get('fatigue_index',0):.1f}% St={metrics.get('state','?')}"
                    else:
                        line += f" | Sin metricas (predictor en estado idle?)"
                    if alerts:
                        line += f" | ALERTA: {[a.get('msg','') for a in alerts]}"
                    print(line)
                    
                elif parsed.get("type") == "STATE_CHANGE":
                    print(f"  Cambio de estado: {parsed.get('state')}")
                else:
                    print(f"  Mensaje: {json.dumps(parsed)[:200]}")
                    
            except asyncio.TimeoutError:
                elapsed = int(time.time() - start)
                sys.stdout.write(f"\r  {elapsed}s - Sin datos...     ")
                sys.stdout.flush()
        
        print()
        if msg_count == 0:
            print("\n  [FALLO] NO llegaron datos del ESP32.")
            print("  Causas posibles:")
            print("  1. ESP32 apagado o sin bateria")
            print("  2. ESP32 no conectado al WiFi 'GalGom'")
            print("  3. IP incorrecta en firmware (192.168.0.231)")
            print("     -> Verifica tu IP con: ipconfig")
            print("  4. Firewall de Windows bloquea puerto 8000")
        else:
            print(f"\n  [OK] {msg_count} paquetes recibidos del ESP32.")
            print("  El pipeline ESP32 -> Backend -> Frontend FUNCIONA.")
            
        await ws.close()
        
    except Exception as e:
        print(f"  [FALLO] WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend())
    input("\nPresiona Enter para cerrar...")
