import pytest
import os
import sys

# Forzar base de datos SQLite en memoria para tests antes de cualquier import
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Ensure backend directory is in python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

import models
from database import Base, get_db
from main import app

# Configurar motor SQLite en memoria con StaticPool para compartir el estado entre hilos
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Crea un esquema nuevo y limpio para cada función de prueba."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Poblar datos semilla esenciales para pruebas
    user = models.User(
        id=1,
        username="IronWarrior",
        weight_kg=80.0,
        height_cm=180.0,
        clerk_id="user_clerk_test_1",
        unit_preference="kg",
        measure_unit="cm",
        theme="dark"
    )
    ex1 = models.Exercise(
        id=1,
        name="Press de Banca",
        muscle_group="Pecho",
        equipment="Barra",
        difficulty="Intermedio",
        description="Empuje horizontal para pectoral"
    )
    ex2 = models.Exercise(
        id=2,
        name="Sentadilla",
        muscle_group="Piernas",
        equipment="Barra",
        difficulty="Avanzado",
        description="Flexión de rodilla y cadera para cuádriceps"
    )
    ex3 = models.Exercise(
        id=3,
        name="Dominadas",
        muscle_group="Espalda",
        equipment="Barra fija",
        difficulty="Intermedio",
        description="Tracción vertical para dorsal ancho"
    )
    session.add_all([user, ex1, ex2, ex3])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Cliente HTTP de pruebas configurado con la base de datos en memoria."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
