import os
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, event

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Por defecto usa SQLite local, pero en la nube usará la URL de PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./biohevy.db")

# SQLAlchemy 1.4+ requiere que la URL de postgres empiece con postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    
    # Activar Foreign Keys para SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # Configuración para PostgreSQL en la nube (Render, Railway, Supabase, etc.)
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
