import pytest
from datetime import datetime, timezone
from fastapi import HTTPException
import main
import schemas

class TestEdgeCasesAndNegativeTestingDirect:
    """Pruebas de casos de borde, robustez y manejo de excepciones (ISO 25010 Confiabilidad)."""

    def test_routine_maximum_limit_enforced(self, db_session):
        """No debe permitir registrar más de 6 rutinas por usuario."""
        # Crear 6 rutinas
        for i in range(1, 7):
            payload = schemas.RoutineCreate(name=f"Rutina {i}", user_id=1, exercises=[])
            main.create_routine(routine=payload, db=db_session)

        # La 7ma rutina debe ser rechazada con HTTP 400
        overflow_payload = schemas.RoutineCreate(name="Rutina 7 Excedida", user_id=1, exercises=[])
        with pytest.raises(HTTPException) as exc_info:
            main.create_routine(routine=overflow_payload, db=db_session)

        assert exc_info.value.status_code == 400
        assert "Límite máximo de 6 rutinas" in exc_info.value.detail

    def test_reject_invalid_foreign_key_in_sets(self, db_session):
        """CRÍTICO: Debe rechazar series asociadas a un exercise_id inexistente (Integridad Referencial)."""
        # Iniciar sesión válida
        start_payload = schemas.SessionCreate(user_id=1, start_time=datetime.now(timezone.utc))
        session_obj = main.start_session(session=start_payload, db=db_session)

        # Intentar finalizar con exercise_id 99999 (inexistente)
        bad_payload = schemas.SessionEnd(
            end_time=datetime.now(timezone.utc),
            sets=[
                schemas.SetCreate(exercise_id=99999, reps=10, weight=50.0, is_failure=False)
            ]
        )
        with pytest.raises(HTTPException) as exc_info:
            main.end_session(session_id=session_obj.id, data=bad_payload, db=db_session)

        assert exc_info.value.status_code == 400
        assert "no existe" in exc_info.value.detail

    def test_user_not_found_returns_404(self, db_session):
        """Consultar usuario inexistente debe lanzar HTTPException(404)."""
        with pytest.raises(HTTPException) as exc_info:
            main.get_user(user_id=99999, db=db_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Usuario no encontrado"

    def test_update_settings_user_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            main.update_user_settings(user_id=99999, settings={"theme": "dark"}, db=db_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Usuario no encontrado"

    def test_start_session_user_not_found(self, db_session):
        start_payload = schemas.SessionCreate(user_id=99999, start_time=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc_info:
            main.start_session(session=start_payload, db=db_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Usuario no encontrado"

    def test_end_session_not_found(self, db_session):
        end_payload = schemas.SessionEnd(end_time=datetime.now(timezone.utc), sets=[])
        with pytest.raises(HTTPException) as exc_info:
            main.end_session(session_id=99999, data=end_payload, db=db_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Sesión no encontrada"

    def test_update_nonexistent_routine(self, db_session):
        update_payload = schemas.RoutineUpdate(name="Fantasma")
        with pytest.raises(HTTPException) as exc_info:
            main.update_routine(routine_id=99999, routine=update_payload, db=db_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Rutina no encontrada"

    def test_delete_nonexistent_routine(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            main.delete_routine(routine_id=99999, db=db_session)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Rutina no encontrada"


class TestSecurityAndDataSanitizationDirect:
    """Pruebas de seguridad, inyección y validación de esquemas (ISO 25010 Seguridad)."""

    def test_sql_injection_resilience_in_exercise_filters(self, db_session):
        """Comprueba que entradas SQL maliciosas se traten como string seguro."""
        payload_sqli = "' OR '1'='1"
        res = main.get_exercises(group_id=payload_sqli, db=db_session)
        assert res == []

    def test_empty_routine_exercises_accepted_safely(self, db_session):
        """Crear una rutina con 0 ejercicios no debe provocar fallos."""
        payload = schemas.RoutineCreate(name="Rutina Vacia Segura", user_id=1, exercises=[])
        created = main.create_routine(routine=payload, db=db_session)
        assert created.name == "Rutina Vacia Segura"

    def test_session_calories_burned_fallback_when_user_none(self, db_session):
        """Si la sesión tiene duración cero o mínima, se calcula de forma segura."""
        import models
        sess = models.Session(id=777, user_id=1, start_time=datetime.now(timezone.utc))
        db_session.add(sess)
        db_session.commit()

        end_payload = schemas.SessionEnd(end_time=datetime.now(timezone.utc), sets=[])
        res = main.end_session(session_id=777, data=end_payload, db=db_session)
        assert res["status"] == "success"
        assert res["calories"] >= 0
