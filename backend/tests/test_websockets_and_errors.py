"""
Pruebas del módulo biomecánico en tiempo real (WebSockets) y de las rutas de error
del backend (rollback, IntegrityError, errores 500) — ISO/IEC 25010: Fiabilidad y
Tolerancia a fallos.
"""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi import HTTPException, WebSocketDisconnect
from sqlalchemy.exc import IntegrityError

import database
import main
import schemas


class FakeWebSocket:
    """Doble de prueba de starlette.WebSocket: entrega mensajes en cola y luego se desconecta."""

    def __init__(self, incoming=None, fail_on_send=False, final_exc=None):
        self.incoming = list(incoming or [])
        self.sent = []
        self.accepted = False
        self.fail_on_send = fail_on_send
        self.final_exc = final_exc or WebSocketDisconnect()

    async def accept(self):
        self.accepted = True

    async def _next(self):
        if self.incoming:
            return self.incoming.pop(0)
        raise self.final_exc

    async def receive_json(self):
        return await self._next()

    async def receive_text(self):
        return await self._next()

    async def send_json(self, message):
        if self.fail_on_send:
            raise RuntimeError("socket cerrado")
        self.sent.append(message)


def run_sync(coro):
    """Ejecuta una corrutina que nunca se suspende (los dobles de WebSocket responden
    de inmediato) sin crear un event loop: determinista y portable entre plataformas."""
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    coro.close()
    raise RuntimeError("La corrutina se suspendió inesperadamente")


def _emg_signal(n=600, amp=300.0, freq=90.0, fs=430):
    t = np.arange(n) / fs
    return (2048 + amp * np.sin(2 * np.pi * freq * t)).tolist()


@pytest.fixture(autouse=True)
def reset_realtime_state():
    main.manager.frontend_connections.clear()
    main.predictor_ch1.reset()
    main.predictor_ch2.reset()
    yield
    main.manager.frontend_connections.clear()
    main.predictor_ch1.reset()
    main.predictor_ch2.reset()


class TestEmgFrameProcessing:
    def test_frame_without_both_channels_is_ignored(self):
        assert main.process_emg_frame({"ch1": [1, 2, 3]}) is None
        assert main.process_emg_frame({}) is None

    def test_frame_with_both_channels_builds_payload(self):
        main.predictor_ch1.start_monitoring()
        main.predictor_ch2.start_monitoring()
        signal = _emg_signal()
        payload = main.process_emg_frame({"ch1": signal, "ch2": signal})
        assert payload["type"] == "REALTIME_EMG"
        assert payload["ch1"]["raw"] == signal
        assert payload["ch1"]["metrics"] is not None
        assert isinstance(payload["ch2"]["alerts"], list)

    def test_channel_payload_without_metrics(self):
        assert main._build_channel_payload([1], [], []) == {"raw": [1], "metrics": None, "alerts": []}

    def test_debug_log_handles_empty_metrics(self, capsys):
        main._log_emg_debug([], [])
        assert capsys.readouterr().out == ""
        main._log_emg_debug([{"rms": 10, "mnf": 100, "is_active": True}], [])
        assert "[EMG] ACT" in capsys.readouterr().out


class TestFrontendCommands:
    @pytest.mark.parametrize("action,state", [
        ("START_MONITORING", "LISTENING"),
        ("NEW_SET", "LISTENING"),
        ("RESET", "IDLE"),
    ])
    def test_valid_actions(self, action, state):
        assert main.handle_frontend_command(json.dumps({"action": action})) == {
            "type": "STATE_CHANGE", "state": state
        }

    @pytest.mark.parametrize("raw", ["{no-json", json.dumps({"action": "HACK"}), json.dumps([1, 2]), "{}"])
    def test_invalid_or_unknown_commands_are_ignored(self, raw):
        assert main.handle_frontend_command(raw) is None


class TestWebSocketEndpoints:
    def test_esp32_socket_broadcasts_to_frontends(self):
        frontend = FakeWebSocket()
        run_sync(main.manager.connect_frontend(frontend))
        signal = _emg_signal()
        esp32 = FakeWebSocket(incoming=[{"ch1": signal, "ch2": signal}, {"ping": True}])

        run_sync(main.websocket_emg(esp32))

        assert esp32.accepted
        assert len(frontend.sent) == 1
        assert frontend.sent[0]["type"] == "REALTIME_EMG"

    def test_esp32_socket_survives_unexpected_error(self, capsys):
        esp32 = FakeWebSocket(final_exc=ValueError("trama corrupta"))
        run_sync(main.websocket_emg(esp32))
        assert "Error en WebSocket ESP32" in capsys.readouterr().out

    def test_frontend_socket_command_flow_and_disconnect(self):
        ws = FakeWebSocket(incoming=[
            json.dumps({"action": "START_MONITORING"}),
            "basura",
            json.dumps({"action": "RESET"}),
        ])
        run_sync(main.websocket_emg_frontend(ws))
        assert [m["state"] for m in ws.sent] == ["LISTENING", "IDLE"]
        assert ws not in main.manager.frontend_connections

    def test_broadcast_removes_dead_connections(self):
        alive, dead = FakeWebSocket(), FakeWebSocket(fail_on_send=True)
        main.manager.frontend_connections.extend([alive, dead])
        run_sync(main.manager.broadcast_to_frontends({"type": "PING"}))
        assert alive.sent == [{"type": "PING"}]
        assert dead not in main.manager.frontend_connections


class TestErrorPathsAndResilience:
    def test_start_session_commit_failure_rolls_back(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = object()
        db.commit.side_effect = RuntimeError("db caída")
        payload = schemas.SessionCreate(user_id=1, routine_id=None, start_time=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            main.start_session(payload, db=db)
        assert exc.value.status_code == 400
        db.rollback.assert_called_once()

    def test_end_session_integrity_error_returns_400(self):
        db = MagicMock()
        db.query.side_effect = IntegrityError("INSERT", {}, Exception("fk"))
        data = schemas.SessionEnd(end_time=datetime.now(timezone.utc), sets=[])
        with pytest.raises(HTTPException) as exc:
            main.end_session(1, data, db=db)
        assert exc.value.status_code == 400
        db.rollback.assert_called_once()

    def test_end_session_unexpected_error_returns_500(self):
        db = MagicMock()
        db.query.side_effect = RuntimeError("timeout")
        data = schemas.SessionEnd(end_time=datetime.now(timezone.utc), sets=[])
        with pytest.raises(HTTPException) as exc:
            main.end_session(1, data, db=db)
        assert exc.value.status_code == 500

    def test_clerk_login_concurrent_creation_recovers_existing_user(self):
        recovered = MagicMock(id=7, clerk_id="clerk_x", username="Ana")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [None, None, recovered]
        db.commit.side_effect = RuntimeError("unique violation")
        res = main.clerk_login(main.ClerkLoginRequest(clerk_id="clerk_x", username="Ana"), db=db)
        assert res == {"id": 7, "clerk_id": "clerk_x", "username": "Ana"}
        db.rollback.assert_called_once()

    def test_clerk_login_unrecoverable_creation_returns_409(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit.side_effect = RuntimeError("db caída")
        with pytest.raises(HTTPException) as exc:
            main.clerk_login(main.ClerkLoginRequest(clerk_id="c", username="u"), db=db)
        assert exc.value.status_code == 409

    def test_get_db_yields_and_closes_session(self):
        gen = database.get_db()
        session = next(gen)
        assert session is not None
        with pytest.raises(StopIteration):
            next(gen)
