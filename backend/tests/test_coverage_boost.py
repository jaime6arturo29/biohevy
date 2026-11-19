import pytest
from datetime import datetime, timezone
import models
import schemas
import main

class TestCoverageBoost:
    """Pruebas adicionales para maximizar la cobertura del backend al 85%+ y superar el umbral de New Code."""

    def test_get_user_sessions_with_sets_grouping(self, db_session):
        # 1. Crear usuario y ejercicio
        user = models.User(username="session_viewer", clerk_id="clerk_view_1", weight_kg=75.0, height_cm=178)
        db_session.add(user)
        db_session.commit()

        ex = models.Exercise(name="Dominadas Test", muscle_group="Espalda", description="Test")
        db_session.add(ex)
        db_session.commit()

        # 2. Crear sesión terminada con sets (routine_id=None es válido)
        start = datetime.now(timezone.utc)
        end = datetime.now(timezone.utc)
        sess = models.Session(user_id=user.id, routine_id=None, start_time=start, end_time=end, total_volume=500.0, calories_burned=120.0)
        db_session.add(sess)
        db_session.commit()

        s1 = models.Set(session_id=sess.id, exercise_id=ex.id, reps=10, weight=50.0, is_failure=False)
        s2 = models.Set(session_id=sess.id, exercise_id=ex.id, reps=8, weight=50.0, is_failure=True)
        db_session.add_all([s1, s2])
        db_session.commit()

        # 3. Invocar endpoint
        result = main.get_sessions(user_id=user.id, db=db_session)
        assert len(result) == 1
        assert result[0]["total_volume"] == 500.0
        assert result[0]["calories_burned"] == 120.0
        assert result[0]["set_count"] == 2
        assert len(result[0]["exercises"]) == 1
        assert result[0]["exercises"][0]["name"] == "Dominadas Test"

    def test_get_user_stats_calculation(self, db_session):
        user = models.User(username="stats_calc", clerk_id="clerk_stats_1", weight_kg=80.0, height_cm=180)
        db_session.add(user)
        db_session.commit()

        sess1 = models.Session(user_id=user.id, routine_id=None, total_volume=1000.0, calories_burned=250.0)
        sess2 = models.Session(user_id=user.id, routine_id=None, total_volume=1500.0, calories_burned=350.0)
        db_session.add_all([sess1, sess2])
        db_session.commit()

        stats = main.get_user_stats(user_id=user.id, db=db_session)
        assert stats["total_sessions"] == 2
        assert stats["total_volume"] == 2500.0
        assert stats["total_calories"] == 600.0

    def test_serve_index_and_spa_fallback(self):
        # Cuando el build de react no existe, retorna mensaje informativo
        idx = main.serve_index()
        assert "message" in idx

        # SPA fallback para rutas no API ni WS
        with pytest.raises(Exception) as exc:
            main.serve_spa_fallback("unknown/route")
        assert exc.value.status_code == 404

        # SPA fallback para rutas reservadas api/ws
        with pytest.raises(Exception) as exc2:
            main.serve_spa_fallback("api/protected")
        assert exc2.value.status_code == 404

    def test_clerk_login_username_fallback_link(self, db_session):
        # Usuario preexistente por username sin clerk_id
        user = models.User(username="legacy_athlete", clerk_id=None, weight_kg=72.0, height_cm=170)
        db_session.add(user)
        db_session.commit()

        req = main.ClerkLoginRequest(clerk_id="new_clerk_link_123", username="legacy_athlete")
        res = main.clerk_login(req, db=db_session)
        assert res["clerk_id"] == "new_clerk_link_123"

        # Verificar que se actualizó en base de datos
        db_session.refresh(user)
        assert user.clerk_id == "new_clerk_link_123"

    def test_end_session_with_naive_datetime(self, db_session):
        user = models.User(username="naive_time_user", weight_kg=70.0, height_cm=175)
        db_session.add(user)
        db_session.commit()

        sess = models.Session(user_id=user.id, routine_id=None, start_time=None)
        db_session.add(sess)
        db_session.commit()

        ex = models.Exercise(name="Bicep Curl", muscle_group="Brazos", description="Test")
        db_session.add(ex)
        db_session.commit()

        # Enviar datetime ingenuo (sin tzinfo) para cubrir ramas de normalización UTC
        naive_end = datetime(2026, 5, 20, 10, 30, 0)
        end_data = schemas.SessionEnd(
            end_time=naive_end,
            sets=[schemas.SetCreate(exercise_id=ex.id, reps=10, weight=20.0, is_failure=False)]
        )

        res = main.end_session(session_id=sess.id, data=end_data, db=db_session)
        assert res["status"] == "success"
        assert res["volume"] == 200.0


