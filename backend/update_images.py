import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get("DATABASE_URL")
engine = create_engine(database_url)

mapping = {
    "Press de Banca con Barra": "/exercises/bench.png",
    "Sentadilla con Barra": "/exercises/squat.png",
    "Peso Muerto": "/exercises/deadlift.png",
    "Dominadas (Pull-ups)": "/exercises/pullups.png"
}

try:
    with engine.connect() as conn:
        for name, url in mapping.items():
            conn.execute(text("UPDATE exercises SET image_url = :url WHERE name = :name"), {"url": url, "name": name})
        conn.commit()
        print("Exercise images updated in database.")
except Exception as e:
    print(f"Error: {e}")
