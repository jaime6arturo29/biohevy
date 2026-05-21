import requests
import json
from datetime import datetime

BASE = "http://127.0.0.1:8000"
results = []

def test(name, fn):
    try:
        ok, msg = fn()
        results.append({"name": name, "ok": ok, "msg": msg})
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
    except Exception as e:
        results.append({"name": name, "ok": False, "msg": str(e)})
        print(f"[ERROR] {name}: {e}")

# T1: Backend activo
def t1():
    r = requests.get(f"{BASE}/exercises", timeout=5)
    data = r.json()
    return r.status_code == 200, f"Status {r.status_code}, {len(data)} ejercicios"
test("Backend activo", t1)

# T2: Filtro group_id
def t2():
    r = requests.get(f"{BASE}/exercises?group_id=1", timeout=5)
    return r.status_code == 200, f"Devuelve {len(r.json())} ejercicios para group_id=1"
test("Filtro group_id", t2)

# T3: Muscle groups endpoint
def t3():
    r = requests.get(f"{BASE}/muscle-groups", timeout=5)
    return r.status_code == 200, f"{len(r.json())} grupos musculares"
test("Muscle Groups endpoint", t3)

# T4: Rutina vacía (edge case)
def t4():
    payload = {"name": "Rutina Vacia", "user_id": 1, "exercises": []}
    r = requests.post(f"{BASE}/routines", json=payload, timeout=5)
    return r.status_code == 200, f"Status {r.status_code}"
test("Rutina sin ejercicios", t4)

# T5: Sesión completa con volumen correcto
def t5():
    r = requests.post(f"{BASE}/sessions/start", json={"user_id": 1, "start_time": datetime.utcnow().isoformat()}, timeout=5)
    sid = r.json()["id"]
    end_payload = {
        "end_time": datetime.utcnow().isoformat(),
        "sets": [{"exercise_id": 1, "reps": 10, "weight": 80.0, "is_failure": False}]
    }
    r2 = requests.post(f"{BASE}/sessions/{sid}/end", json=end_payload, timeout=5)
    d = r2.json()
    vol = d.get("volume")
    cal = round(d.get("calories", 0), 2)
    return vol == 800.0, f"volume={vol} (esperado 800.0), calories={cal}"
test("Sesion: volumen correcto (10x80=800)", t5)

# T6: User inexistente en inicio de sesion -> 404
def t6():
    r = requests.post(f"{BASE}/sessions/start", json={"user_id": 9999, "start_time": datetime.utcnow().isoformat()}, timeout=5)
    return r.status_code == 404, f"Status {r.status_code} (esperado 404 para user inexistente)"
test("User inexistente -> 404", t6)

# T7: Session ID que no existe -> 404
def t7():
    end_payload = {"end_time": datetime.utcnow().isoformat(), "sets": []}
    r = requests.post(f"{BASE}/sessions/99999/end", json=end_payload, timeout=5)
    return r.status_code == 404, f"Status {r.status_code} (esperado 404)"
test("Session ID inexistente -> 404", t7)

# T8: exercise_id invalido en set (FK no validada)
def t8():
    r = requests.post(f"{BASE}/sessions/start", json={"user_id": 1, "start_time": datetime.utcnow().isoformat()}, timeout=5)
    sid = r.json()["id"]
    end_payload = {
        "end_time": datetime.utcnow().isoformat(),
        "sets": [{"exercise_id": 99999, "reps": 5, "weight": 50.0, "is_failure": False}]
    }
    r2 = requests.post(f"{BASE}/sessions/{sid}/end", json=end_payload, timeout=5)
    # Deberia rechazarlo, pero SQLite no enforcea FK por default -> BUG
    is_bug = r2.status_code == 200
    return not is_bug, f"Status {r2.status_code} {'(BUG: acepto FK invalido)' if is_bug else '(rechazado correctamente)'}"
test("exercise_id invalido -> debe rechazar", t8)

# T9: Routines para user inexistente = lista vacía
def t9():
    r = requests.get(f"{BASE}/routines?user_id=9999", timeout=5)
    data = r.json()
    return r.status_code == 200 and data == [], f"Devuelve: {data}"
test("Routines user inexistente = lista vacia", t9)

# T10: Stats endpoint estructura correcta
def t10():
    r = requests.get(f"{BASE}/stats/1", timeout=5)
    d = r.json()
    keys_ok = all(k in d for k in ["total_sessions", "total_volume", "total_calories"])
    return keys_ok, str(d)
test("Stats endpoint - estructura correcta", t10)

# T11: GET /users/{id} existente
def t11():
    r = requests.get(f"{BASE}/users/1", timeout=5)
    return r.status_code == 200, f"Status {r.status_code}, data={r.json()}"
test("GET user existente", t11)

# T12: GET /users/{id} inexistente debe ser 404 (BUG: devuelve null)
def t12():
    r = requests.get(f"{BASE}/users/99999", timeout=5)
    is_bug = r.status_code == 200 and r.json() is None
    return not is_bug, f"Status {r.status_code}, body={r.text[:50]} {'(BUG: null 200)' if is_bug else ''}"
test("GET user inexistente -> 404", t12)

# Guardar JSON para el dashboard
with open("test_results.json", "w") as f:
    json.dump(results, f, indent=2)

passed = sum(1 for r in results if r["ok"])
print(f"\n{'='*40}")
print(f"TOTAL: {passed}/{len(results)} pruebas pasadas")
print(f"{'='*40}")
