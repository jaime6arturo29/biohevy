from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
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

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BioHevy API")

# Montar archivos estáticos del frontend (ruta relativa para portabilidad)
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app.mount("/app", StaticFiles(directory=frontend_path), name="app")

# Configurar CORS para el frontend en React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar a la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
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
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
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
    except Exception as e:
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
    except Exception as e:
        db.rollback()
        if "IntegrityError" in str(type(e)):
            raise HTTPException(status_code=400, detail="Error de integridad (FK) en los datos proporcionados")
        print(f"--- DATABASE ERROR ---")
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
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@app.put("/users/{user_id}/settings")
def update_user_settings(user_id: int, settings: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
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
@app.websocket("/ws/emg")
async def websocket_emg(websocket: WebSocket):
    await websocket.accept()
    
    # Instanciamos predictores independientes por cada canal
    predictor_ch1 = biomech_engine.FatiguePredictor(fs=1000, window_ms=200, overlap_ms=100)
    predictor_ch2 = biomech_engine.FatiguePredictor(fs=1000, window_ms=200, overlap_ms=100)
    
    try:
        while True:
            # Recibir paquete JSON en ráfaga (50 muestras) desde el ESP32
            data = await websocket.receive_json()
            
            if "ch1" in data and "ch2" in data:
                ch1_data = data["ch1"]
                ch2_data = data["ch2"]
                
                # Procesar cada canal
                metrics_ch1, alerts_ch1 = predictor_ch1.process_incoming_data(ch1_data)
                metrics_ch2, alerts_ch2 = predictor_ch2.process_incoming_data(ch2_data)
                
                # Si hay alertas generadas (calibración terminada o fatiga inminente), enviarlas al frontend
                for alert in alerts_ch1:
                    await websocket.send_json({"channel": 1, "alert": alert})
                for alert in alerts_ch2:
                    await websocket.send_json({"channel": 2, "alert": alert})
                    
                # También podemos enviar un submuestreo de las métricas (RMS/MNF) para el dashboard
                if metrics_ch1 or metrics_ch2:
                    await websocket.send_json({
                        "type": "METRICS_UPDATE",
                        "ch1": metrics_ch1[-1] if metrics_ch1 else None,
                        "ch2": metrics_ch2[-1] if metrics_ch2 else None
                    })
                    
    except WebSocketDisconnect:
        print("Sensor ESP32 desconectado")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
