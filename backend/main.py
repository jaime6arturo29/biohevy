from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
import traceback
import os
from datetime import timezone
import models, schemas, biomech_engine
from database import engine, get_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[SYSTEM] Conexión a base de datos diferida o en modo test: {e}")

app = FastAPI(title="BioHevy API")

# Constantes de error para cumplimiento de mantenibilidad y Sonar
USER_NOT_FOUND = "Usuario no encontrado"

# Configurar rutas absolutas para portabilidad
base_dir = os.path.dirname(os.path.abspath(__file__))
dist_path = os.path.join(base_dir, "..", "biohevy-web", "dist")
assets_path = os.path.join(dist_path, "assets")

# Montar los assets estáticos compilados de React de manera opcional
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    print("[SYSTEM] Frontend compilado de React detectado y montado.")
else:
    print("[SYSTEM] Ejecutando en modo de desarrollo separado (Next.js en puerto 3000 / FastAPI en puerto 8000).")

# Configurar CORS seguro para el frontend en React (cumplimiento Sonar / CWE-942)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/muscle-groups")
def get_muscle_groups(db: Session = Depends(get_db)):
    # Derivar grupos musculares del campo string en Exercise (no hay tabla separada)
    groups = db.query(models.Exercise.muscle_group).distinct().all()
    return [{"name": g[0]} for g in groups if g[0]]

@app.get("/exercises")
def get_exercises(group_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Exercise)
    if group_id:
        query = query.filter(models.Exercise.muscle_group == group_id)
    return query.all()

# --- RUTINAS ---
@app.post("/routines")
def create_routine(routine: schemas.RoutineCreate, db: Session = Depends(get_db)):
    # Límite de 6 rutinas
    count = db.query(models.Routine).filter(models.Routine.user_id == routine.user_id).count()
    if count >= 6:
        raise HTTPException(status_code=400, detail="Límite máximo de 6 rutinas alcanzado.")

    db_routine = models.Routine(name=routine.name, user_id=routine.user_id)
    db.add(db_routine)
    db.commit()
    db.refresh(db_routine)
    
    for ex in routine.exercises:
        db_ex = models.RoutineExercise(
            routine_id=db_routine.id,
            exercise_id=ex.exercise_id,
            order_index=ex.order_index,
            template_data=ex.template_data
        )
        db.add(db_ex)
    db.commit()
    return db_routine

@app.put("/routines/{routine_id}")
def update_routine(routine_id: int, routine: schemas.RoutineUpdate, db: Session = Depends(get_db)):
    db_routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
    if not db_routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    if routine.name:
        db_routine.name = routine.name
    
    if routine.exercises is not None:
        # Eliminar ejercicios viejos y poner los nuevos
        db.query(models.RoutineExercise).filter(models.RoutineExercise.routine_id == routine_id).delete()
        for ex in routine.exercises:
            db_ex = models.RoutineExercise(
                routine_id=routine_id,
                exercise_id=ex.exercise_id,
                order_index=ex.order_index,
                template_data=ex.template_data
            )
            db.add(db_ex)
    
    db.commit()
    return {"status": "success"}

@app.delete("/routines/{routine_id}")
def delete_routine(routine_id: int, db: Session = Depends(get_db)):
    db_routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
    if not db_routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    
    # Set routine_id to None in completed sessions referencing this routine
    db.query(models.Session).filter(models.Session.routine_id == routine_id).update({models.Session.routine_id: None})
    
    db.query(models.RoutineExercise).filter(models.RoutineExercise.routine_id == routine_id).delete()
    db.delete(db_routine)
    db.commit()
    return {"status": "success"}

@app.get("/routines")
def get_routines(user_id: int, db: Session = Depends(get_db)):
    routines = db.query(models.Routine).filter(models.Routine.user_id == user_id).all()
    result = []
    for r in routines:
        exs = []
        # Ordenar por order_index
        sorted_exercises = sorted(r.exercises, key=lambda x: x.order_index)
        for re in sorted_exercises:
            exs.append({
                "id": re.exercise.id,
                "name": re.exercise.name,
                "template_data": re.template_data,
                "order_index": re.order_index
            })
        result.append({
            "id": r.id,
            "name": r.name,
            "exercises": exs
        })
    return result

# --- SESIONES (Entrenamientos) ---
@app.post("/sessions/start")
def start_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
        
    db_session = models.Session(
        user_id=session.user_id,
        routine_id=session.routine_id,
        start_time=session.start_time
    )
    db.add(db_session)
    try:
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad (FK) en inicio de sesión")

@app.post("/sessions/{session_id}/end")
def end_session(session_id: int, data: schemas.SessionEnd, db: Session = Depends(get_db)):
    try:
        db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        end_time = data.end_time
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
            
        db_session.end_time = end_time
        
        start_time = db_session.start_time
        if start_time is None:
            start_time = end_time
        elif start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        total_volume = 0
        for s in data.sets:
            # Validar que el ejercicio exista antes de insertar para garantizar integridad referencial (ISO 25010)
            ex_check = db.query(models.Exercise).filter(models.Exercise.id == s.exercise_id).first()
            if not ex_check:
                raise HTTPException(status_code=400, detail=f"Ejercicio con id {s.exercise_id} no existe")

            total_volume += (s.reps or 0) * (s.weight or 0)
            db_set = models.Set(
                session_id=session_id,
                exercise_id=s.exercise_id,
                reps=s.reps,
                weight=s.weight,
                is_failure=s.is_failure
            )
            db.add(db_set)
        
        db_session.total_volume = total_volume
        
        user = db.query(models.User).filter(models.User.id == db_session.user_id).first()
        if user:
            duration = (end_time - start_time).total_seconds()
            duration_hours = max(0.02, duration / 3600)
            db_session.calories_burned = 6.0 * user.weight_kg * duration_hours
        else:
            db_session.calories_burned = 0

        db.commit()
        return {
            "status": "success", 
            "volume": total_volume, 
            "calories": db_session.calories_burned
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        if "IntegrityError" in str(type(e)):
            raise HTTPException(status_code=400, detail="Error de integridad (FK) en los datos proporcionados")
        print("--- DATABASE ERROR ---")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# --- USUARIOS ---
@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserBase, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

from pydantic import BaseModel
class ClerkLoginRequest(BaseModel):
    clerk_id: str
    username: str

@app.post("/auth/clerk-login")
def clerk_login(data: ClerkLoginRequest, db: Session = Depends(get_db)):
    # Check if user with clerk_id exists
    user = db.query(models.User).filter(models.User.clerk_id == data.clerk_id).first()
    if not user:
        # Check if username exists (fallback)
        user = db.query(models.User).filter(models.User.username == data.username).first()
        if user:
            user.clerk_id = data.clerk_id
            db.commit()
        else:
            # Create new user without forcing ID
            user = models.User(
                clerk_id=data.clerk_id, 
                username=data.username, 
                weight_kg=70, 
                height_cm=175,
                unit_preference="kg",
                measure_unit="cm",
                theme="dark"
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except Exception:
                db.rollback()
                # Final fallback if something went wrong during concurrent creation
                user = db.query(models.User).filter(models.User.clerk_id == data.clerk_id).first()
    
    return {"id": user.id, "clerk_id": user.clerk_id, "username": user.username}


@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
    return user

@app.put("/users/{user_id}/settings")
def update_user_settings(user_id: int, settings: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
    
    if "unit_preference" in settings:
        user.unit_preference = settings["unit_preference"]
    if "measure_unit" in settings:
        user.measure_unit = settings["measure_unit"]
    if "theme" in settings:
        user.theme = settings["theme"]
    
    db.commit()
    return {"status": "success"}

# --- NOTICIAS ---
@app.get("/news")
def get_news():
    return [
        {
            "id": 1,
            "title": "Nuevas Máquinas en BioHevy",
            "content": "Hemos actualizado nuestra base de datos con las últimas máquinas de resistencia variable para optimizar tu entrenamiento.",
            "date": "2024-04-23"
        },
        {
            "id": 2,
            "title": "Importancia del Descanso",
            "content": "Estudios recientes demuestran que descansos de 90-120 segundos entre series de máquinas mejoran la hipertrofia muscular.",
            "date": "2024-04-22"
        },
        {
            "id": 3,
            "title": "Técnica vs Peso",
            "content": "En máquinas, priorizar el rango de movimiento completo sobre la carga máxima reduce el riesgo de lesiones articulares.",
            "date": "2024-04-21"
        }
    ]

# --- MÓDULO BIOMECÁNICO (Real-time) ---
# ConnectionManager para reenviar datos del ESP32 a todos los frontends conectados
class ConnectionManager:
    def __init__(self):
        self.frontend_connections: List[WebSocket] = []

    async def connect_frontend(self, websocket: WebSocket):
        await websocket.accept()
        self.frontend_connections.append(websocket)
        print(f"[WS] 🖥️ Frontend conectado. Total frontends: {len(self.frontend_connections)}")

    def disconnect_frontend(self, websocket: WebSocket):
        if websocket in self.frontend_connections:
            self.frontend_connections.remove(websocket)
        print(f"[WS] 🖥️ Frontend desconectado. Total frontends: {len(self.frontend_connections)}")

    async def broadcast_to_frontends(self, message: dict):
        dead = []
        for conn in self.frontend_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.disconnect_frontend(d)

manager = ConnectionManager()

# Predictores globales — fs=430 Hz (frecuencia REAL del ADS1115 leyendo 2 canales por I2C)
predictor_ch1 = biomech_engine.FatiguePredictor(fs=430, window_ms=300, overlap_ms=150)
predictor_ch2 = biomech_engine.FatiguePredictor(fs=430, window_ms=300, overlap_ms=150)

@app.websocket("/ws/emg")
async def websocket_emg(websocket: WebSocket):
    """Endpoint para el ESP32. Recibe datos crudos y los reenvía procesados a los frontends."""
    await websocket.accept()
    print("[WS] ESP32 conectado al servidor.")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if "ch1" in data and "ch2" in data:
                ch1_data = data["ch1"]
                ch2_data = data["ch2"]
                
                # Procesar cada canal con el motor biomecánico
                metrics_ch1, alerts_ch1 = predictor_ch1.process_incoming_data(ch1_data)
                metrics_ch2, alerts_ch2 = predictor_ch2.process_incoming_data(ch2_data)
                
                # Debug: mostrar métricas en consola
                if metrics_ch1:
                    m = metrics_ch1[-1]
                    active = "ACT" if m.get('is_active', False) else "rest"
                    st = m.get('state', '?')
                    fi = m.get('fatigue_index', 0)
                    ms = m.get('mnf_score', 0)
                    vs = m.get('valley_score', 0)
                    ps = m.get('peak_score', 0)
                    nf = predictor_ch1.noise_floor
                    th = predictor_ch1.activity_threshold
                    print(f"[EMG] {active} RMS={m.get('rms',0):.0f} NF={nf:.0f} TH={th:.0f} MNF={m.get('mnf',0):.0f}Hz | FI={fi:.1f}% (mnf:{ms:.0f} valley:{vs:.0f} peak:{ps:.0f}) | {st} | Alerts:{len(alerts_ch1)}")
                
                # Construir payload para el frontend con datos reales
                payload = {
                    "type": "REALTIME_EMG",
                    "ch1": {
                        "raw": ch1_data,
                        "metrics": metrics_ch1[-1] if metrics_ch1 else None,
                        "alerts": alerts_ch1
                    },
                    "ch2": {
                        "raw": ch2_data,
                        "metrics": metrics_ch2[-1] if metrics_ch2 else None,
                        "alerts": alerts_ch2
                    }
                }
                
                # Reenviar a todos los frontends conectados
                await manager.broadcast_to_frontends(payload)
                    
    except WebSocketDisconnect:
        print("[WS] 🔌 ESP32 desconectado.")
    except Exception as e:
        print(f"[WS] 💥 Error en WebSocket ESP32: {e}")
        traceback.print_exc()

@app.websocket("/ws/emg/frontend")
async def websocket_emg_frontend(websocket: WebSocket):
    """Endpoint para el frontend React. Recibe comandos y envía datos procesados."""
    await manager.connect_frontend(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                cmd = json.loads(raw)
                action = cmd.get("action", "")
                
                if action == "START_MONITORING":
                    predictor_ch1.start_monitoring()
                    predictor_ch2.start_monitoring()
                    print("[WS] 📡 Monitoreo EMG iniciado — Auto-calibración activa.")
                    await websocket.send_json({"type": "STATE_CHANGE", "state": "LISTENING"})
                    
                elif action == "NEW_SET":
                    predictor_ch1.start_monitoring()
                    predictor_ch2.start_monitoring()
                    print("[WS] 🔄 Nueva serie — Recalibrando automáticamente.")
                    await websocket.send_json({"type": "STATE_CHANGE", "state": "LISTENING"})
                    
                elif action == "RESET":
                    predictor_ch1.reset()
                    predictor_ch2.reset()
                    print("[WS] ⏹ Monitoreo detenido.")
                    await websocket.send_json({"type": "STATE_CHANGE", "state": "IDLE"})
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect_frontend(websocket)
    except Exception:
        manager.disconnect_frontend(websocket)

@app.get("/sessions")
def get_sessions(user_id: int, db: Session = Depends(get_db)):
    sessions = db.query(models.Session).filter(models.Session.user_id == user_id).order_by(models.Session.start_time.desc()).all()
    result = []
    for s in sessions:
        sets = db.query(models.Set).filter(models.Set.session_id == s.id).all()
        
        # Agrupar sets por ejercicio para el resumen
        ex_map = {}
        for st in sets:
            if st.exercise_id not in ex_map:
                ex_map[st.exercise_id] = {
                    "id": st.exercise.id,
                    "name": st.exercise.name,
                    "sets": []
                }
            ex_map[st.exercise_id]["sets"].append({
                "weight": st.weight,
                "reps": st.reps,
                "is_failure": st.is_failure
            })
        
        duration_mins = 0
        if s.start_time and s.end_time:
            duration_mins = int((s.end_time - s.start_time).total_seconds() / 60)
        
        result.append({
            "id": s.id,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration_minutes": duration_mins,
            "total_volume": s.total_volume,
            "calories_burned": s.calories_burned,
            "set_count": len(sets),
            "exercises": list(ex_map.values())
        })
    return result

@app.get("/stats/{user_id}")
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    sessions = db.query(models.Session).filter(models.Session.user_id == user_id).all()
    total_volume = sum([s.total_volume or 0 for s in sessions])
    total_calories = sum([s.calories_burned or 0 for s in sessions])
    return {
        "total_sessions": len(sessions),
        "total_volume": total_volume,
        "total_calories": total_calories
    }

# ================= SERVIR FRONTEND ESTÁTICO (PORTABILIDAD) =================
@app.get("/")
def serve_index():
    index_html = os.path.join(dist_path, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
    return {"message": "BioHevy API is running, but React build was not found. Please compile frontend using 'npm run build'."}

@app.get("/{catchall:path}")
def serve_spa_fallback(catchall: str):
    # Evitar capturar rutas de la API reales
    if catchall.startswith(("api", "ws", "docs")):
        raise HTTPException(status_code=404, detail="Not Found")
    
    index_html = os.path.join(dist_path, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
    raise HTTPException(status_code=404, detail="SPA Index not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
