import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_session_flow():
    # 1. Iniciar sesión
    start_payload = {
        "user_id": 1,
        "start_time": datetime.utcnow().isoformat()
    }
    res_start = requests.post(f"{BASE_URL}/sessions/start", json=start_payload)
    session = res_start.json()
    session_id = session['id']
    print(f"Sesión iniciada: ID {session_id}")

    # 2. Finalizar con 2 series de Press de Banca (ID 1)
    # 10 reps x 80kg = 800
    # 10 reps x 80kg = 800
    # Total esperado = 1600kg
    end_payload = {
        "end_time": datetime.utcnow().isoformat(),
        "sets": [
            {"exercise_id": 1, "reps": 10, "weight": 80.0, "is_failure": False},
            {"exercise_id": 1, "reps": 10, "weight": 80.0, "is_failure": False}
        ]
    }
    res_end = requests.post(f"{BASE_URL}/sessions/{session_id}/end", json=end_payload)
    result = res_end.json()
    print(f"Resultado Final: Volumen={result['volume']}kg, Calorías={result['calories']}kcal")

if __name__ == "__main__":
    try:
        test_session_flow()
    except Exception as e:
        print(f"Error: {e}")
