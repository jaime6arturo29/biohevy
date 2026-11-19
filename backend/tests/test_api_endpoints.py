import pytest
from datetime import datetime, timezone
import asyncio
from fastapi import HTTPException
import main
import schemas
import models

class TestExercisesAndCatalogDirect:
    """Pruebas funcionales de endpoints de catálogo y ejercicios."""

    def test_get_all_exercises(self, db_session):
        data = main.get_exercises(group_id=None, db=db_session)
        assert isinstance(data, list)
        assert len(data) >= 3
        names = [e.name for e in data]
        assert "Press de Banca" in names
        assert "Sentadilla" in names
        assert "Dominadas" in names

    def test_filter_exercises_by_muscle_group(self, db_session):
        data = main.get_exercises(group_id="Pecho", db=db_session)
        assert len(data) >= 1
        for ex in data:
            assert ex.muscle_group == "Pecho"

    def test_get_muscle_groups(self, db_session):
        data = main.get_muscle_groups(db=db_session)
        assert isinstance(data, list)
        group_names = [g["name"] for g in data]
        assert "Pecho" in group_names
        assert "Piernas" in group_names
        assert "Espalda" in group_names

    def test_get_news(self):
        data = main.get_news()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "title" in data[0]
        assert "content" in data[0]


class TestRoutinesCRUDDirect:
    """Pruebas CRUD para la gestión de rutinas de entrenamiento."""

    def test_create_and_get_routine(self, db_session):
        payload = schemas.RoutineCreate(
            name="Rutina Torso Fuerza",
            user_id=1,
            exercises=[
                schemas.RoutineExerciseCreate(
                    exercise_id=1,
                    order_index=1,
                    template_data='[{"reps": 8, "weight": 85}]'
                )
            ]
        )
        from fastapi.encoders import jsonable_encoder
        created = main.create_routine(routine=payload, db=db_session)
        encoded = jsonable_encoder(created)
        assert encoded.get("id") is not None
        assert encoded.get("name") == "Rutina Torso Fuerza"
        assert created.id is not None
        assert created.name == "Rutina Torso Fuerza"

        # Consultar las rutinas del usuario
        routines = main.get_routines(user_id=1, db=db_session)
        assert any(r["id"] == created.id and r["name"] == "Rutina Torso Fuerza" for r in routines)

    def test_update_routine(self, db_session):
        # Crear rutina
        create_payload = schemas.RoutineCreate(name="Rutina Original", user_id=1, exercises=[])
        created = main.create_routine(routine=create_payload, db=db_session)

        # Actualizar
        update_payload = schemas.RoutineUpdate(name="Rutina Renombrada")
        res = main.update_routine(routine_id=created.id, routine=update_payload, db=db_session)
        assert res == {"status": "success"}

        # Verificar cambio
        routines = main.get_routines(user_id=1, db=db_session)
        matched = [r for r in routines if r["id"] == created.id]
        assert len(matched) == 1
        assert matched[0]["name"] == "Rutina Renombrada"

    def test_update_routine_with_exercises_replacement(self, db_session):
        # Crear rutina con 1 ejercicio
        r_payload = schemas.RoutineCreate(
            name="Rutina Base",
            user_id=1,
            exercises=[schemas.RoutineExerciseCreate(exercise_id=1, order_index=1, template_data="[]")]
        )
        r = main.create_routine(routine=r_payload, db=db_session)

        # Actualizar sustituyendo ejercicios
        update_payload = schemas.RoutineUpdate(
            name="Rutina Con Nuevos Ejercicios",
            exercises=[
                schemas.RoutineExerciseCreate(exercise_id=2, order_index=1, template_data="[{\"reps\": 10}]"),
                schemas.RoutineExerciseCreate(exercise_id=3, order_index=2, template_data="[{\"reps\": 12}]")
            ]
        )
        res = main.update_routine(routine_id=r.id, routine=update_payload, db=db_session)
        assert res == {"status": "success"}

        # Verificar en base de datos
        routines = main.get_routines(user_id=1, db=db_session)
        target = [item for item in routines if item["id"] == r.id][0]
        assert len(target["exercises"]) == 2
        assert target["exercises"][0]["id"] == 2
        assert target["exercises"][1]["id"] == 3

    def test_delete_routine(self, db_session):
        create_payload = schemas.RoutineCreate(name="Rutina a Borrar", user_id=1, exercises=[])
        created = main.create_routine(routine=create_payload, db=db_session)

        del_res = main.delete_routine(routine_id=created.id, db=db_session)
        assert del_res == {"status": "success"}

        # Verificar que ya no existe en el listado
        routines = main.get_routines(user_id=1, db=db_session)
        assert not any(r["id"] == created.id for r in routines)


class TestSessionsAndMetricsDirect:
    """Pruebas del ciclo de vida de sesiones, cómputo de volumen y calorías."""

    def test_full_session_flow_with_metrics(self, db_session):
        # 1. Iniciar sesión
        start_payload = schemas.SessionCreate(
            user_id=1,
            start_time=datetime.now(timezone.utc)
        )
        session_obj = main.start_session(session=start_payload, db=db_session)
        assert session_obj.id is not None
        session_id = session_obj.id

        # 2. Finalizar sesión con 2 sets válidos:
        # 10 reps x 80 kg = 800
        # 12 reps x 80 kg = 960
        # Total volumen esperado = 1760 kg
        end_payload = schemas.SessionEnd(
            end_time=datetime.now(timezone.utc),
            sets=[
                schemas.SetCreate(exercise_id=1, reps=10, weight=80.0, is_failure=False),
                schemas.SetCreate(exercise_id=1, reps=12, weight=80.0, is_failure=True)
            ]
        )
        result = main.end_session(session_id=session_id, data=end_payload, db=db_session)
        assert result["status"] == "success"
        assert result["volume"] == 1760.0
        assert result["calories"] > 0

        # 3. Verificar listado de sesiones históricas
        sessions = main.get_sessions(user_id=1, db=db_session)
        current_sess = [s for s in sessions if s["id"] == session_id][0]
        assert current_sess["total_volume"] == 1760.0
        assert current_sess["set_count"] == 2
        assert len(current_sess["exercises"]) == 1

        # 4. Verificar reporte agregado de estadísticas
        stats = main.get_user_stats(user_id=1, db=db_session)
        assert stats["total_sessions"] >= 1
        assert stats["total_volume"] >= 1760.0
        assert stats["total_calories"] > 0


class TestUsersAndSettingsDirect:
    """Pruebas de gestión de usuario y preferencias."""

    def test_get_user_profile(self, db_session):
        user = main.get_user(user_id=1, db=db_session)
        assert user.id == 1
        assert user.username == "IronWarrior"
        assert user.weight_kg == 80.0

    def test_create_user_endpoint(self, db_session):
        user_in = schemas.UserBase(
            username="ChampionUser",
            weight_kg=75.5,
            height_cm=178.0,
            unit_preference="kg",
            measure_unit="cm",
            theme="dark"
        )
        created = main.create_user(user=user_in, db=db_session)
        assert created.id is not None
        assert created.username == "ChampionUser"

    def test_update_user_settings(self, db_session):
        settings_payload = {
            "unit_preference": "lbs",
            "measure_unit": "inch",
            "theme": "light"
        }
        res = main.update_user_settings(user_id=1, settings=settings_payload, db=db_session)
        assert res == {"status": "success"}

        # Verificar actualización
        user = main.get_user(user_id=1, db=db_session)
        assert user.unit_preference == "lbs"
        assert user.measure_unit == "inch"
        assert user.theme == "light"

    def test_clerk_login_existing_and_new_user(self, db_session):
        # Login de usuario existente por clerk_id
        req_existing = main.ClerkLoginRequest(
            clerk_id="user_clerk_test_1",
            username="IronWarrior"
        )
        res_existing = main.clerk_login(data=req_existing, db=db_session)
        assert res_existing["id"] == 1

        # Login de nuevo usuario (auto-creación)
        req_new = main.ClerkLoginRequest(
            clerk_id="user_clerk_new_99",
            username="NewAthlete"
        )
        res_new = main.clerk_login(data=req_new, db=db_session)
        assert res_new["username"] == "NewAthlete"
        assert res_new["clerk_id"] == "user_clerk_new_99"

    def test_connection_manager_logic(self):
        mgr = main.ConnectionManager()
        assert mgr.frontend_connections == []

        dummy_ws = object()
        mgr.frontend_connections.append(dummy_ws)
        assert len(mgr.frontend_connections) == 1

        mgr.disconnect_frontend(dummy_ws)
        assert len(mgr.frontend_connections) == 0
